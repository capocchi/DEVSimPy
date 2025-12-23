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

from DEVSKernel.Strategies import DirectCouplingPyDEVSSimStrategy
from DEVSKernel.KafkaDEVS.MS4Me.MS4MeKafkaWorker import MS4MeKafkaWorker
from DEVSKernel.KafkaDEVS.MS4Me.ms4me_kafka_wire_adapters import StandardWireAdapter
from DEVSKernel.KafkaDEVS.MS4Me.ms4me_kafka_messages import (
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
from DEVSKernel.KafkaDEVS.Proxies import KafkaReceiverProxy, KafkaStreamProxy
from DEVSKernel.KafkaDEVS.MS4Me.auto_kafka import ensure_kafka_broker
from DEVSKernel.KafkaDEVS.logconfig import configure_logging, LOGGING_LEVEL
from DEVSKernel.KafkaDEVS.MS4Me.kafkaconfig import KAFKA_BOOTSTRAP, AUTO_START_KAFKA_BROKER

configure_logging()
logger = logging.getLogger("DEVSKernel.KafkaDEVS.SimStrategyKafkaMS4Me")
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


class SimStrategyKafkaMS4Me(DirectCouplingPyDEVSSimStrategy):
    """
    Kafka strategy with in-memory workers (threads instead of processes),
    using typed DEVS messages and a wire adapter (Standard/Local).
    Refactored architecture with Proxy pattern (Stream/Receiver).
    """

    def __init__(self, simulator=None,
                 kafka_bootstrap=KAFKA_BOOTSTRAP,
                 request_timeout=30.0,
                 stream_proxy_class=None,
                 receiver_proxy_class=None):
        super().__init__(simulator)

        # Ensure confluent-kafka is available
        try:
            import confluent_kafka
        except ImportError:
            raise RuntimeError("confluent-kafka not available. Please install it: pip install confluent-kafka")

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
            wire_adapter=self.wire
        )
        
        self._receiver_proxy = ReceiverProxyClass(
            self.bootstrap,
            group_id,
            wire_adapter=self.wire
        )
        
        # Subscribe to output topic
        self._receiver_proxy.subscribe([MS4MeKafkaWorker.OUT_TOPIC])

        # Check if atomic models have been loaded properly
        assert self.flat_priority_list != []

        # DEVS Atomic models list
        self._atomic_models = list(self.flat_priority_list)
        self._num_atomics = len(self._atomic_models)
        self._index2model = {i: m for i, m in enumerate(self._atomic_models)}

        # Worker threads
        self._workers = MultiKeyDict()
        
        logger.info("KafkaDEVS SimStrategy initialized (Proxy Pattern)")
        logger.info(f"  Bootstrap servers: {self.bootstrap}")
        logger.info(f"  Consumer group: {group_id}")
        logger.info(f"  Number of atomic models: {self._num_atomics}")
        logger.info(f"  Index Mapping:")
        for i, m in enumerate(self._atomic_models):
            logger.info(f"    Index {i} -> {m.myID} ({m.getBlockModel().label})")

    # ------------------------------------------------------------------
    #  Simulation
    # ------------------------------------------------------------------

    def simulate(self, T=1e8, **kwargs):
        """Main simulation loop with Kafka coordination and message routing"""
        if self._simulator is None:
            raise ValueError("Simulator instance must be provided.")

        logger.info("=" * 60)
        logger.info("  KafkaDEVS Simulation Starting (Proxy Pattern)")
        logger.info("=" * 60)
        
        self._create_workers()
        self._create_topics()

        logger.info("Waiting for workers to initialize (2s)...")
        time.sleep(2)

        # Purge old messages via proxy
        flushed = self._receiver_proxy.purge_old_messages(max_seconds=2.0)
        logger.info(f"System ready (flushed {flushed} old messages)")

        # Chose the specific message type used
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
                self.bootstrap
            )

            logger.info(f"  Model {model.myID} ({worker.get_model_label()}):")
            logger.info(f"    Real class: {model.__class__.__module__}.{model.__class__.__name__}")
            logger.info(f"    OPorts: {[p.name for p in model.OPorts]}")
            logger.info(f"    IPorts: {[p.name for p in model.IPorts]}")
            logger.info(
                f"    in_topic={worker.get_topic_to_write()}, "
                f"out_topic={worker.get_topic_to_read()}"
            )

            worker.start()

            # Dict with multiple keys
            self._workers.add([i, model.myID], worker)

        logger.info("  All %s threads started", self._num_atomics)

    def _create_topics(self):
        """Create Kafka topics for local or standard mode."""
        
        admin = AdminClient({"bootstrap.servers": self.bootstrap})

        # Existing topics
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

        # Build the set of topic names to create
        desired = set()

        # Worker input topics
        for w in self._workers.values():
            desired.add(w.get_topic_to_write())

        # Coordinator output topic
        desired.add(MS4MeKafkaWorker.OUT_TOPIC)

        # Filter topics that don't exist yet
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
        
        Args:
            pending: List of models to wait for responses from
            
        Returns:
            Dictionary {model: message} of responses
        """
        if not pending:
            pending = list(self._atomic_models)
        
        return self._receiver_proxy.receive_messages(pending, self.request_timeout)

    def _simulate_for_ms4me(self, T=1e8):
        """Simulate using standard KafkaDEVS message routing."""
        try:

            # STEP 0: distributed init
            logger.info("Initializing atomic models...")

            st = SimTime(t=self.ts.Get())

            for worker in self._workers.values():
                self._send_msg_to_kafka(
                    msg=InitSim(st), 
                    topic=worker.get_topic_to_write()
                )

            init_workers_results = self._await_msgs_from_kafka()
            
            # Check time consistency
            for model in self._atomic_models:
                label = model.getBlockModel().label
                devs_msg = init_workers_results[model]
                assert isinstance(devs_msg, NextTime)
                logger.info(f"  Model {label}: next={model.timeNext}")

            # MAIN SIMULATION LOOP
            logger.info(f"Simulation loop starting (T={T})...")
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
                
                # Get imminent workers and models
                imminents_worker, imminents_model = zip(*[
                    (w, w.get_model())
                    for w in self._workers.values()
                    if w.get_model_time_next() == tmin
                ]) if tmin is not None else ((), ())

                imminents_model = list(imminents_model)

                logger.info("=" * 60)
                logger.info(f"Iteration {iteration}: t={tmin}")
                logger.info(f"  Imminent models: {list(map(str, imminents_model))}")
                logger.info("=" * 60)

                # STEP 1: execute output functions
                logger.info("[1/4] Executing output functions...")
                st = SimTime(t=tmin)
                for w in imminents_worker:
                    self._send_msg_to_kafka(
                        msg=SendOutput(st), 
                        topic=w.get_topic_to_write()
                    )

                output_msgs = self._await_msgs_from_kafka(imminents_model)
                assert all(isinstance(msg, ModelOutputMessage) for msg in output_msgs.values())
                
                # STEP 2: routing outputs to destinations
                logger.info("[2/4] Routing outputs to destinations...")
                externals_to_send = {}
                parent_model = (
                    self._atomic_models[0].parent if self._atomic_models else None
                )

                if parent_model is not None:
                    for model, devs_msg in output_msgs.items():
                        if devs_msg is None or not isinstance(devs_msg, ModelOutputMessage):
                            continue

                        outputs = devs_msg.modelOutput
                        if not outputs:
                            continue

                        logger.info("  Model %s produced %s outputs", model.myID, len(outputs))

                        for pv in outputs:
                            src_port = None
                            for p in model.OPorts:
                                if p.name == pv.portIdentifier:
                                    src_port = p
                                    break
                            if src_port is None:
                                continue

                            for coupling in parent_model.IC:
                                try:
                                    (src_m, src_p), (dest_m, dest_p) = coupling
                                except Exception:
                                    continue

                                if src_m is model and src_p is src_port:
                                    dest_idx = None
                                    for idx, m in self._index2model.items():
                                        if m is dest_m:
                                            dest_idx = idx
                                            break
                                    if dest_idx is None:
                                        continue

                                    logger.info(
                                        "    -> Routing %s.%s -> %s.%s",
                                        model.myID, pv.portIdentifier,
                                        dest_m.myID, dest_p.name
                                    )

                                    if dest_idx not in externals_to_send:
                                        externals_to_send[dest_idx] = {}
                                    externals_to_send[dest_idx][dest_p.name] = pv.value

                # STEP 2b: external transitions
                td_ext = {}

                if externals_to_send:
                    for dest_idx, inputs in externals_to_send.items():
                        pv_list = [
                            PortValue(v, port, type(v).__name__)
                            for port, v in inputs.items()
                        ]

                        current_worker = self._workers.get(dest_idx)
                        logger.info(f"  Sending external transitions to {current_worker.get_model_label()}...")
                        
                        self._send_msg_to_kafka(
                            msg=ExecuteTransition(st, pv_list), 
                            topic=current_worker.get_topic_to_write()
                        )

                    td_ext = self._await_msgs_from_kafka([
                        self._workers.get(i).get_model() 
                        for i in externals_to_send.keys()
                    ])
                    assert all(isinstance(msg, TransitionDone) for msg in td_ext.values())
                else:
                    logger.info("  No outputs to route!")

                # STEP 3: internal transitions
                logger.info(f"[3/4] Executing internal transitions...")
                for w in imminents_worker:
                    self._send_msg_to_kafka(
                        msg=ExecuteTransition(st), 
                        topic=w.get_topic_to_write()
                    )

                td_int = self._await_msgs_from_kafka(imminents_model)
                assert all(isinstance(msg, TransitionDone) for msg in td_int.values())

                # Update tmin
                all_next_times = [t.nextTime.t for _, t in td_int.items()] + [t.nextTime.t for _, t in td_ext.items()]
                tmin = min(all_next_times) if all_next_times else float("inf")
                
                # Update progress
                self.master.timeLast = tmin
                self._simulator.cpu_time = old_cpu_time + (time.time() - t_start)

            logger.info("=" * 60)
            logger.info(f"Simulation completed at t={self.ts.Get()}")
            logger.info(f"  Iterations: {iteration}")
            logger.info(f"  CPU time: {self._simulator.cpu_time:.3f}s")
            logger.info("=" * 60)

            self._simulator.terminate()

        except KeyboardInterrupt:
            logger.warning("Simulation interrupted by user")
        except Exception as e:
            logger.exception("Simulation error: %s", e)
        finally:
            # Broadcast SimulationDone to all workers
            logger.info("Broadcasting SimulationDone...")
            st = SimTime(t=self.ts.Get())
            for w in self._workers.values():
                self._send_msg_to_kafka(
                    msg=SimulationDone(time=st), 
                    topic=w.get_topic_to_write()
                )

            self._terminate_workers()
            logger.info("MS4Me KafkaDEVS Simulation Ended")

    def __del__(self):
        """Cleanup: close proxies properly"""
        if hasattr(self, '_stream_proxy'):
            self._stream_proxy.close()
        if hasattr(self, '_receiver_proxy'):
            self._receiver_proxy.close()