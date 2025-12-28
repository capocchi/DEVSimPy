# -*- coding: utf-8 -*-
"""
SimStrategyKafkaMS4Me - Kafka-based distributed DEVS simulation strategy
with in-memory workers (threads) using typed DEVS messages.
"""

import logging
import time
from typing import Dict, List, Optional

from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException, KafkaError

from DEVSKernel.PyDEVS.SimStrategies import DirectCouplingPyDEVSSimStrategy
from DomainInterface import DomainStructure, DomainBehavior
from DEVSKernel.BrokerDEVS.MS4Me.MS4MeKafkaWorker import MS4MeKafkaWorker
from DEVSKernel.BrokerDEVS.MS4Me.ms4me_kafka_wire_adapters import StandardWireAdapter
from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import (
    BaseMessage,
    SimTime,
    InitSim,
    NextTime,
    ExecuteTransition,
    SendOutput,
    ModelOutputMessage,
    PortValue,
    TransitionDone,
    SimulationDone,
)
from DEVSKernel.BrokerDEVS.Proxies.kafka import KafkaReceiverProxy
from DEVSKernel.BrokerDEVS.Proxies.kafka import KafkaStreamProxy
from DEVSKernel.BrokerDEVS.MS4Me.auto_kafka import ensure_kafka_broker
from DEVSKernel.BrokerDEVS.logconfig import configure_logging, LOGGING_LEVEL
from DEVSKernel.BrokerDEVS.MS4Me.kafkaconfig import KAFKA_BOOTSTRAP, AUTO_START_KAFKA_BROKER


configure_logging()
logger = logging.getLogger("DEVSKernel.BrokerDEVS.SimStrategyKafkaMS4Me")
logger.setLevel(LOGGING_LEVEL)


class MultiKeyDict:
    """Dictionary that supports multiple keys pointing to the same value"""

    def __init__(self):
        self._data = {}
        self._keys = {}  # valeur → liste de clés

    def add(self, keys, value):
        """Associate multiple keys to a value"""
        for key in keys:
            self._data[key] = value
        self._keys[value] = keys

    def get(self, key):
        return self._data.get(key)

    def values(self):
        """Return unique values"""
        return set(self._data.values())

    def keys(self):
        """Return all keys"""
        return self._data.keys()

    def items(self):
        """Return all (key, value) pairs"""
        return self._data.items()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __len__(self):
        """Return number of unique values"""
        return len(set(self._data.values()))

    def __contains__(self, key):
        return key in self._data

def build_routing_table(atomic_models):
    """
    Table de routage HYBRIDE : ports aplatis + résolution complète EIC/IC
    """
    routing_table = {}
    logger.info("=== Building HYBRID routing table ===")
	
    # PHASE 1: Connexions directes via outLine (rapides)
    logger.info("PHASE 1: Direct atomic connections (outLine)")
    for src in atomic_models:
        for op in getattr(src, "OPorts", []):
            key = (src, op.name)
            destinations = []
			
            for ip in getattr(op, "outLine", []):
                if hasattr(ip, 'host') and hasattr(ip.host, 'myID'):
                    dest_model = ip.host
                    dest_port = ip.name
                    if isinstance(dest_model, DomainBehavior):  # atomic only
                        destinations.append((dest_model, dest_port))
                        logger.info("  DIRECT: %s.%s -> %s.%s", 
                                  src.myID, op.name, dest_model.myID, dest_port)
			
            if destinations:
                routing_table[key] = destinations
	
    # PHASE 2: Résolution complète via IC/EIC de TOUS les couplés
    logger.info("PHASE 2: Hierarchical resolution via IC/EIC")
    def resolve_hierarchical(model, target_port, visited=None):
        """Résout récursivement une destination via la hiérarchie IC/EIC"""
        if visited is None:
            visited = set()
        if model in visited:
            return []
        visited.add(model)
		
        destinations = []
		
        # Si atomique → fin de résolution
        if isinstance(model, DomainBehavior):
            return [(model, target_port.name)]
		
        # Si couplé → parcourir EIC puis IC récursivement
        if isinstance(model, DomainStructure):
            if hasattr(model, 'EIC'):
                for eic in model.EIC:
                    try:
                        # Formats EIC possibles: (ext_port, int_model, int_port) ou tuples
                        if len(eic) == 3:
                            ext_port, int_model, int_port = eic
                        elif len(eic) == 2 and isinstance(eic[0], tuple):
                            _, ext_port = eic[0]
                            int_model, int_port = eic[1]
                        else:
                            continue
						
                        # Matching port externe
                        if (hasattr(ext_port, 'name') and ext_port.name == target_port.name) or \
                           (hasattr(target_port, 'name') and ext_port == target_port.name):
                            destinations.extend(resolve_hierarchical(int_model, int_port, visited))
                    except Exception:
                        continue
			
            # Parcourir IC pour propagation interne
            if hasattr(model, 'IC'):
                for ic in model.IC:
                    try:
                        if len(ic) == 2 and isinstance(ic[0], tuple):
                            src_m, src_p = ic[0]
                            dest_m, dest_p = ic[1]
                        elif len(ic) == 4:
                            src_m, src_p, dest_m, dest_p = ic
                        else:
                            continue
						
                        destinations.extend(resolve_hierarchical(dest_m, dest_p, visited))
                    except Exception:
                        continue
		
        return destinations
	
    # Appliquer résolution hiérarchique sur TOUS les outLine
    for src in atomic_models:
        for op in getattr(src, "OPorts", []):
            key = (src, op.name)
            if key not in routing_table:
                routing_table[key] = []
			
            for ip in getattr(op, "outLine", []):
                if hasattr(ip, 'host') and hasattr(ip.host, 'EIC'):  # Couplé détecté
                    hierarchical_dests = resolve_hierarchical(ip.host, ip, set())
                    for dest_model, dest_port in hierarchical_dests:
                        if dest_model in atomic_models:
                            routing_table[key].append((dest_model, dest_port))
                            logger.info("  HIERARCHICAL: %s.%s -> %s.%s (via %s)", 
                                      src.myID, op.name, dest_model.myID, dest_port, ip.host.myID)
	
    # Éliminer doublons
    for key in routing_table:
        routing_table[key] = list(set(routing_table[key]))
	
    logger.info("=== HYBRID table: %d routes ===", len(routing_table))
    for key, dests in routing_table.items():
        logger.info("  %s.%s -> [%s]", key[0].myID, key[1], 
                   ', '.join(f"{d[0].myID}.{d[1]}" for d in dests))
	
    return routing_table


class SimStrategyKafkaMS4Me(DirectCouplingPyDEVSSimStrategy):
    """
    Kafka strategy with in-memory workers (threads instead of processes),
    using typed DEVS messages and a wire adapter (Standard/Local).
    Refactored architecture with Proxy pattern (Stream/Receiver).
    """

    def __init__(
        self,
        simulator=None,
        kafka_bootstrap=KAFKA_BOOTSTRAP,
        request_timeout=30.0,
        stream_proxy_class=None,
        receiver_proxy_class=None,
    ):
        super().__init__(simulator)

        # Ensure confluent-kafka is available
        try:
            import confluent_kafka  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "confluent-kafka not available. Please install it: pip install confluent-kafka"
            )

        # Ensure Kafka broker is alive
        if AUTO_START_KAFKA_BROKER:
            try:
                self.bootstrap = ensure_kafka_broker(bootstrap=kafka_bootstrap)
            except RuntimeError as e:
                logger.error("%s", e)
                raise
        else:
            self.bootstrap = kafka_bootstrap

        # Wire adapter choice
        self.wire = StandardWireAdapter

        # Unique group ID for this run
        group_id = f"coordinator-{int(time.time() * 1000)}"
        self.request_timeout = request_timeout

        # Dependency injection: use provided proxy classes or defaults
        StreamProxyClass = stream_proxy_class or KafkaStreamProxy
        ReceiverProxyClass = receiver_proxy_class or KafkaReceiverProxy

        # Instantiate proxies (replaces direct Producer/Consumer)
        self._stream_proxy = StreamProxyClass(
            self.bootstrap,
        )

        self._receiver_proxy = ReceiverProxyClass(
            self.bootstrap,
            group_id,
        )

        # Subscribe to output topic
        self._receiver_proxy.subscribe([MS4MeKafkaWorker.OUT_TOPIC])

        # DEVS Atomic models list
        self._atomic_models = list(self.flat_priority_list)
        self._num_atomics = len(self._atomic_models)
        self._index2model = {i: m for i, m in enumerate(self._atomic_models)}

        # Build routing table from flattened ports
        logger.info(
            "Building routing table for %d models (using flattened port connections)",
            len(self.flat_priority_list),
        )
        self._routing_table = build_routing_table(self.flat_priority_list)

        # Debug routes
        for key, dests in self._routing_table.items():
            logger.info(
                "  %s.%s -> %s",
                key[0].myID,
                key[1],
                [(d[0].myID, d[1]) for d in dests],
            )

        # Worker threads
        self._workers = MultiKeyDict()

        logger.info("BrokerDEVS SimStrategy initialized (Proxy Pattern)")
        logger.info("  Bootstrap servers: %s", self.bootstrap)
        logger.info("  Consumer group: %s", group_id)
        logger.info("  Number of atomic models: %d", self._num_atomics)
        logger.info("  Index Mapping:")
        for i, m in enumerate(self._atomic_models):
            logger.info("    Index %d -> %s (%s)", i, m.myID, m.getBlockModel().label)

    # ------------------------------------------------------------------
    #  Simulation
    # ------------------------------------------------------------------

    def simulate(self, T=1e8, **kwargs):
        """Main simulation loop with Kafka coordination and message routing"""
        if self._simulator is None:
            raise ValueError("Simulator instance must be provided.")

        logger.info("=" * 60)
        logger.info("  BrokerDEVS Simulation Starting (Proxy Pattern)")
        logger.info("=" * 60)

        self._create_workers()
        self._create_topics()

        logger.info("Waiting for workers to initialize (2s)...")
        time.sleep(2)

        # Purge old messages via proxy
        flushed = self._receiver_proxy.purge_old_messages(max_seconds=2.0)
        logger.info("System ready (flushed %d old messages)", flushed)

        return self._simulate_for_ms4me(T)

    # ------------------------------------------------------------------
    #  Topics & workers
    # ------------------------------------------------------------------

    def _create_workers(self):
        """Spawn in-memory worker threads"""

        logger.info("Spawning %s worker threads...", self._num_atomics)

        for i, model in enumerate(self._atomic_models):
            worker = MS4MeKafkaWorker(
                model.getBlockModel().label,
                model,
                self.bootstrap,
            )

            logger.info("  Model %s (%s):", model.myID, worker.get_model_label())
            logger.info(
                "    Real class: %s.%s",
                model.__class__.__module__,
                model.__class__.__name__,
            )
            logger.info("    OPorts: %s", [p.name for p in model.OPorts])
            logger.info("    IPorts: %s", [p.name for p in model.IPorts])
            logger.info(
                "    in_topic=%s, out_topic=%s",
                worker.get_topic_to_write(),
                worker.get_topic_to_read(),
            )

            worker.start()
            self._workers.add([i, model.myID], worker)

        logger.info("  All %s threads started", self._num_atomics)

    def _create_topics(self):
        """Create Kafka topics for local or standard mode."""
        admin = AdminClient({"bootstrap.servers": self.bootstrap})

        try:
            metadata = admin.list_topics(timeout=10)
        except KafkaException as e:
            err = e.args[0]
            if err.code() == KafkaError._TRANSPORT:
                logger.error(
                    "Unable to connect to Kafka broker at %s.\n"
                    "Please verify that the broker is running.",
                    self.bootstrap,
                )
            else:
                logger.error("Kafka error while listing topics: %s", err)
            raise

        existing = set(metadata.topics.keys())
        desired = set()

        for w in self._workers.values():
            desired.add(w.get_topic_to_write())

        desired.add(MS4MeKafkaWorker.OUT_TOPIC)

        topics_to_create = [t for t in desired if t not in existing]

        if not topics_to_create:
            logger.info(
                "All required Kafka topics already exist: %s",
                sorted(existing),
            )
            return

        logger.info("  Topics to create: %s", topics_to_create)

        new_topics = [
            NewTopic(
                t,
                num_partitions=(3 if t == MS4MeKafkaWorker.OUT_TOPIC else 1),
                replication_factor=1,
            )
            for t in topics_to_create
        ]

        fs = admin.create_topics(new_topics)

        for topic, f in fs.items():
            try:
                logger.info("Waiting for topic %s creation...", topic)
                f.result()
                logger.info("  Topic %s created", topic)
            except KafkaException as e:
                err = e.args[0]
                if err.code() == KafkaError.TOPIC_ALREADY_EXISTS:
                    logger.info("  Topic %s already exists", topic)
                else:
                    logger.error("Error creating topic %s: %s", topic, err.str())
                    raise

    def _terminate_workers(self):
        """Stop all worker threads"""
        logger.info("Stopping worker threads...")

        for worker in self._workers.values():
            worker.stop()

        for worker in self._workers.values():
            worker.join(timeout=2.0)

        logger.info("  All workers stopped")

    # ------------------------------------------------------------------
    #  Message sending/receiving via proxies
    # ------------------------------------------------------------------

    def _send_msg_to_kafka(self, topic: str, msg: BaseMessage):
        """Send a message via the StreamProxy."""
        self._stream_proxy.send_message(topic, msg)

    def _await_msgs_from_kafka(self, pending: Optional[List] = None) -> Dict:
        """
        Wait for worker responses via the ReceiverProxy.

        Returns:
            Dictionary {model: message} of responses
        """
        if not pending:
            pending = list(self._atomic_models)

        return self._receiver_proxy.receive_messages(pending, self.request_timeout)

    # ------------------------------------------------------------------
    #  Main simulation loop
    # ------------------------------------------------------------------

    def _simulate_for_ms4me(self, T=1e8):
        """Simulate using standard MS4ME message routing."""
        try:
            # STEP 0: distributed init
            logger.info("Initializing atomic models...")

            st = SimTime(t=self.ts.Get())

            for worker in self._workers.values():
                self._send_msg_to_kafka(
                    msg=InitSim(st),
                    topic=worker.get_topic_to_write(),
                )

            init_workers_results = self._await_msgs_from_kafka()

            logger.info("Received %d initialization responses:", len(init_workers_results))
            for model, msg in init_workers_results.items():
                label = model.getBlockModel().label if hasattr(model, 'getBlockModel') else model.label
                logger.info("  Model %s: %s", label, type(msg).__name__)

            for model in self._atomic_models:
                label = model.getBlockModel().label
                devs_msg = init_workers_results[model]
                if not isinstance(devs_msg, NextTime):
                    logger.error(
                        "Expected NextTime message for model %s, got %s: %s",
                        label,
                        type(devs_msg).__name__,
                        devs_msg,
                    )
                    assert isinstance(devs_msg, NextTime), \
                        f"Expected NextTime for {label}, got {type(devs_msg).__name__}: {devs_msg}"
                logger.info("  Model %s: next=%s", label, model.timeNext)

            logger.info("Simulation loop starting (T=%s)...", T)
            iteration = 0
            t_start = time.time()
            old_cpu_time = 0.0

            tmin = min(a.time.t for a in init_workers_results.values())

            while self.ts.Get() < T and not self._simulator.end_flag:
                iteration += 1

                if tmin == float("inf"):
                    logger.info("No more events - simulation complete")
                    break
                if tmin > T:
                    logger.info("Next event at t=%s exceeds T=%s", tmin, T)
                    break

                self.ts.Set(tmin)

                imminents_worker, imminents_model = zip(
                    *[
                        (w, w.get_model())
                        for w in self._workers.values()
                        if w.get_model_time_next() == tmin
                    ]
                ) if tmin is not None else ((), ())

                imminents_model = list(imminents_model)

                logger.info("=" * 60)
                logger.info("Iteration %d: t=%s", iteration, tmin)
                logger.info("  Imminent models: %s", list(map(str, imminents_model)))
                logger.info("=" * 60)

                # STEP 1: execute output functions
                logger.info("[1/4] Executing output functions...")
                st = SimTime(t=tmin)
                for w in imminents_worker:
                    self._send_msg_to_kafka(
                        msg=SendOutput(st),
                        topic=w.get_topic_to_write(),
                    )

                output_msgs = self._await_msgs_from_kafka(imminents_model)
                assert all(
                    isinstance(msg, ModelOutputMessage)
                    for msg in output_msgs.values()
                )

                # STEP 2: routing outputs to destinations
                logger.info("[2/4] Routing outputs to destinations...")
                externals_to_send = {}

                logger.info(
                    "Routing table exists with %d entries", len(self._routing_table)
                )
                for key, dests in self._routing_table.items():
                    logger.info(
                        "  Route: %s.%s -> %d destinations",
                        key[0].myID,
                        key[1],
                        len(dests),
                    )

                for model, devsmsg in output_msgs.items():
                    if devsmsg is None or not isinstance(
                        devsmsg, ModelOutputMessage
                    ):
                        continue

                    outputs = devsmsg.modelOutput
                    if not outputs:
                        continue

                    logger.info(
                        "Model %s produced %d outputs", model.myID, len(outputs)
                    )

                    for pv in outputs:
                        key = (model, pv.portIdentifier)
                        logger.info(
                            "  Looking for route key: (%s, %s)",
                            model.myID,
                            pv.portIdentifier,
                        )

                        if key in self._routing_table:
                            destinations = self._routing_table[key]
                            logger.info(
                                "  Port %s has %d destinations",
                                pv.portIdentifier,
                                len(destinations),
                            )

                            for dest_model, dest_port_name in destinations:
                                destidx = None
                                for idx, m in self._index2model.items():
                                    if m is dest_model:
                                        destidx = idx
                                        break

                                if destidx is not None:
                                    logger.info(
                                        "  - Routing %s.%s -> %s.%s",
                                        model.myID,
                                        pv.portIdentifier,
                                        dest_model.myID,
                                        dest_port_name,
                                    )
                                    if destidx not in externals_to_send:
                                        externals_to_send[destidx] = {}
                                    externals_to_send[destidx][
                                        dest_port_name
                                    ] = pv.value
                        else:
                            logger.warning("  No route found for key %s", key)

                # STEP 2b: external transitions
                td_ext = {}

                if externals_to_send:
                    for dest_idx, inputs in externals_to_send.items():
                        pv_list = [
                            PortValue(v, port, type(v).__name__)
                            for port, v in inputs.items()
                        ]

                        current_worker = self._workers.get(dest_idx)
                        logger.info(
                            "  Sending external transitions to %s...",
                            current_worker.get_model_label(),
                        )

                        self._send_msg_to_kafka(
                            msg=ExecuteTransition(st, pv_list),
                            topic=current_worker.get_topic_to_write(),
                        )

                    td_ext = self._await_msgs_from_kafka(
                        [self._workers.get(i).get_model() for i in externals_to_send]
                    )
                    assert all(
                        isinstance(msg, TransitionDone) for msg in td_ext.values()
                    )
                else:
                    logger.info("  No outputs to route!")

                # STEP 3: internal transitions
                logger.info("[3/4] Executing internal transitions...")
                for w in imminents_worker:
                    self._send_msg_to_kafka(
                        msg=ExecuteTransition(st),
                        topic=w.get_topic_to_write(),
                    )

                td_int = self._await_msgs_from_kafka(imminents_model)
                assert all(
                    isinstance(msg, TransitionDone) for msg in td_int.values()
                )

                # Update tmin
                all_next_times = [t.nextTime.t for t in td_int.values()] + [
                    t.nextTime.t for t in td_ext.values()
                ]
                tmin = min(all_next_times) if all_next_times else float("inf")

                # Update progress
                self.master.timeLast = tmin
                self._simulator.cpu_time = old_cpu_time + (time.time() - t_start)

            logger.info("=" * 60)
            logger.info("Simulation completed at t=%s", self.ts.Get())
            logger.info("  Iterations: %d", iteration)
            logger.info("  CPU time: %.3fs", self._simulator.cpu_time)
            logger.info("=" * 60)

            self._simulator.terminate()

        except KeyboardInterrupt:
            logger.warning("Simulation interrupted by user")
        except Exception as e:
            logger.exception("Simulation error: %s", e)
        finally:
            logger.info("Broadcasting SimulationDone...")
            st = SimTime(t=self.ts.Get())
            for w in self._workers.values():
                self._send_msg_to_kafka(
                    msg=SimulationDone(time=st),
                    topic=w.get_topic_to_write(),
                )

            self._terminate_workers()
            logger.info("MS4Me BrokerDEVS Simulation Ended")

    def __del__(self):
        """Cleanup: close proxies properly"""
        if hasattr(self, "_stream_proxy"):
            self._stream_proxy.close()
        if hasattr(self, "_receiver_proxy"):
            self._receiver_proxy.close()