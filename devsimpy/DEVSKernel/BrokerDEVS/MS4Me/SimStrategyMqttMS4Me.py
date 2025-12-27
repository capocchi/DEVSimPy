# -*- coding: utf-8 -*-
"""
SimStrategyMqttMS4Me - MQTT-based distributed DEVS simulation strategy
with in-memory workers (threads) using typed DEVS messages (MS4Me format).

Mirrors SimStrategyKafkaMS4Me but uses MQTT as the message broker instead of Kafka.
Maintains compatibility with MS4Me message standardization and worker coordination.
"""

import logging
import time
from typing import Dict, List, Optional

from DEVSKernel.PyDEVS.SimStrategies import DirectCouplingPyDEVSSimStrategy
from DomainInterface import DomainStructure, DomainBehavior
from DEVSKernel.BrokerDEVS.MS4Me.MS4MeMqttWorker import MS4MeMqttWorker
from DEVSKernel.BrokerDEVS.MS4Me.ms4me_mqtt_wire_adapters import StandardWireAdapter
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
from DEVSKernel.BrokerDEVS.Proxies.MqttReceiverProxy import MqttReceiverProxy
from DEVSKernel.BrokerDEVS.Proxies.MqttStreamProxy import MqttStreamProxy
from DEVSKernel.BrokerDEVS.MS4Me.auto_mqtt import ensure_mqtt_broker
from DEVSKernel.BrokerDEVS.logconfig import configure_logging, LOGGING_LEVEL
from DEVSKernel.BrokerDEVS.MS4Me.mqttconfig import MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, AUTO_START_MQTT_BROKER


configure_logging()
logger = logging.getLogger("DEVSKernel.BrokerDEVS.SimStrategyMqttMS4Me")
logger.setLevel(LOGGING_LEVEL)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MULTI-KEY DICTIONARY FOR WORKER MAPPING
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


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


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# ROUTING TABLE CONSTRUCTION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def build_routing_table(atomic_models):
    """
    Build hybrid routing table: flattened ports + complete EIC/IC resolution
    """
    routing_table = {}
    logger.info("=== Building HYBRID routing table ===")

    # PHASE 1: Direct atomic connections via outLine (fast path)
    logger.info("PHASE 1: Direct atomic connections (outLine)")
    for src in atomic_models:
        for op in getattr(src, "OPorts", []):
            key = (src, op.name)
            destinations = []

            for ip in getattr(op, "outLine", []):
                if hasattr(ip, 'host') and hasattr(ip.host, 'myID'):
                    dest_model = ip.host
                    dest_port = ip.name
                    destinations.append((dest_model, dest_port))
                    logger.info(
                        "  %s.%s → %s.%s (outLine)",
                        src.myID, op.name,
                        dest_model.myID, dest_port,
                    )

            if destinations:
                routing_table[key] = destinations

    # PHASE 2: EIC (External Input Coupling) - from coupled to atomic
    logger.info("PHASE 2: External Input Coupling (EIC)")
    for src in atomic_models:
        src_struct = src.getBlockModel()
        for ic in getattr(src_struct, 'EIC', []):
            src_port, dest_atomic, dest_port = ic
            key = (src, src_port)
            destinations = [(dest_atomic, dest_port)]
            if key not in routing_table:
                routing_table[key] = destinations
                logger.info(
                    "  EIC: %s.%s → %s.%s",
                    src.myID, src_port,
                    dest_atomic.myID, dest_port,
                )

    # PHASE 3: IC (Internal Coupling) - between atomics within coupled model
    logger.info("PHASE 3: Internal Coupling (IC)")
    for src in atomic_models:
        src_struct = src.getBlockModel()
        for ic in getattr(src_struct, 'IC', []):
            src_atomic, src_port, dest_atomic, dest_port = ic
            if src_atomic in atomic_models:
                key = (src_atomic, src_port)
                if key not in routing_table:
                    routing_table[key] = []
                routing_table[key].append((dest_atomic, dest_port))
                logger.info(
                    "  IC: %s.%s → %s.%s",
                    src_atomic.myID, src_port,
                    dest_atomic.myID, dest_port,
                )

    logger.info("Routing table built: %d routes", len(routing_table))
    return routing_table


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MQTT SIMULATION STRATEGY WITH MS4Me MESSAGES
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class SimStrategyMqttMS4Me(DirectCouplingPyDEVSSimStrategy):
    """
    MQTT-based distributed DEVS simulation strategy with MS4Me message format.
    
    Orchestrates distributed DEVS simulation where:
    - Each atomic model runs in a worker thread
    - Workers communicate via MQTT topics
    - Coordinator manages simulation timing and routing
    - Messages follow MS4Me standardization
    
    Features:
    - Thread-based in-memory workers
    - MQTT-based inter-process communication
    - Automatic topic creation and management
    - Hybrid routing table (ports + EIC/IC)
    - Message serialization/deserialization
    - Timeout and deadline management
    - Graceful shutdown
    """

    def __init__(
        self,
        simulator=None,
        mqtt_broker_address: str = MQTT_BROKER_ADDRESS,
        mqtt_broker_port: int = MQTT_BROKER_PORT,
        request_timeout: float = 30.0,
        stream_proxy_class=None,
        receiver_proxy_class=None,
    ):
        """
        Initialize MQTT MS4Me simulation strategy.
        
        Args:
            simulator: PyDEVS simulator instance
            mqtt_broker_address: MQTT broker address (default: localhost)
            mqtt_broker_port: MQTT broker port (default: 1883)
            request_timeout: Timeout for message responses (seconds)
            stream_proxy_class: Custom MqttStreamProxy class
            receiver_proxy_class: Custom MqttReceiverProxy class
        """
        super().__init__(simulator)

        # Ensure paho-mqtt is available
        try:
            import paho.mqtt.client  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "paho-mqtt not available. Please install it: pip install paho-mqtt"
            )

        # Ensure MQTT broker is alive
        if AUTO_START_MQTT_BROKER:
            try:
                self.broker_address, self.broker_port = ensure_mqtt_broker(
                    address=mqtt_broker_address,
                    port=mqtt_broker_port
                )
            except RuntimeError as e:
                logger.error("%s", e)
                raise
        else:
            self.broker_address = mqtt_broker_address
            self.broker_port = mqtt_broker_port

        # Wire adapter for message format
        self.wire = StandardWireAdapter

        # Unique group ID for this run
        group_id = f"coordinator-{int(time.time() * 1000)}"
        self.request_timeout = request_timeout

        # Dependency injection: use provided proxy classes or defaults
        StreamProxyClass = stream_proxy_class or MqttStreamProxy
        ReceiverProxyClass = receiver_proxy_class or MqttReceiverProxy

        # Instantiate proxies
        self._stream_proxy = StreamProxyClass(
            self.broker_address,
            self.broker_port,
            client_id=f"coordinator-{group_id}",
            wire_adapter=self.wire,
        )

        self._receiver_proxy = ReceiverProxyClass(
            self.broker_address,
            self.broker_port,
            client_id=f"receiver-{group_id}",
            wire_adapter=self.wire,
        )

        # Subscribe to output topic
        self._receiver_proxy.subscribe([MS4MeMqttWorker.OUT_TOPIC])

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

        logger.info("MqttMS4Me SimStrategy initialized")
        logger.info("  Broker: %s:%d", self.broker_address, self.broker_port)
        logger.info("  Consumer group: %s", group_id)
        logger.info("  Number of atomic models: %d", self._num_atomics)
        logger.info("  Index Mapping:")
        for i, m in enumerate(self._atomic_models):
            logger.info("    Index %d -> %s (%s)", i, m.myID, m.getBlockModel().label)

    # ------------------------------------------------------------------
    #  Topics & Workers
    # ------------------------------------------------------------------

    def _create_workers(self):
        """Spawn in-memory worker threads for each atomic model"""
        logger.info("Creating workers for %d atomic models...", self._num_atomics)

        for i, atomic_model in enumerate(self._atomic_models):
            label = atomic_model.getBlockModel().label
            in_topic = f"ms4me{label}In"
            out_topic = f"ms4me{label}Out"

            worker = MS4MeMqttWorker(
                model_name=label,
                aDEVS=atomic_model,
                broker_address=self.broker_address,
                broker_port=self.broker_port,
                in_topic=in_topic,
                out_topic=out_topic,
                wire_adapter=self.wire,
            )

            self._workers.add([atomic_model, i], worker)
            worker.start()

            logger.info(
                "  Worker %d: %s (in=%s, out=%s)",
                i, label, in_topic, out_topic
            )

        logger.info("All %d workers started", self._num_atomics)

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

    def _send_msg_to_mqtt(self, topic: str, msg: BaseMessage):
        """Send a message via the StreamProxy."""
        self._stream_proxy.send_message(topic, msg)

    def _await_msgs_from_mqtt(self, pending: Optional[List] = None) -> Dict:
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
        """Simulate using standard MQTT MS4Me message routing."""
        try:
            # STEP 0: distributed init
            logger.info("Initializing atomic models...")

            st = SimTime(t=self.ts.Get())

            for worker in self._workers.values():
                self._send_msg_to_mqtt(
                    msg=InitSim(st),
                    topic=worker.get_topic_to_write(),
                )

            init_workers_results = self._await_msgs_from_mqtt()

            for model in self._atomic_models:
                label = model.getBlockModel().label
                devs_msg = init_workers_results[model]
                assert isinstance(devs_msg, NextTime)
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
                )

                imminents_model = list(imminents_model)

                logger.info("=" * 60)
                logger.info("Iteration %d: t=%s", iteration, tmin)
                logger.info("  Imminent models: %s", list(map(str, imminents_model)))
                logger.info("=" * 60)

                # STEP 1: execute output functions
                logger.info("[1/4] Executing output functions...")
                st = SimTime(t=tmin)
                for w in imminents_worker:
                    self._send_msg_to_mqtt(
                        msg=SendOutput(st),
                        topic=w.get_topic_to_write(),
                    )

                output_msgs = self._await_msgs_from_mqtt(imminents_model)
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

                        self._send_msg_to_mqtt(
                            msg=ExecuteTransition(st, pv_list),
                            topic=current_worker.get_topic_to_write(),
                        )

                    td_ext = self._await_msgs_from_mqtt(
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
                    self._send_msg_to_mqtt(
                        msg=ExecuteTransition(st),
                        topic=w.get_topic_to_write(),
                    )

                td_int = self._await_msgs_from_mqtt(imminents_model)
                assert all(
                    isinstance(msg, TransitionDone) for msg in td_int.values()
                )

                # Update tmin
                all_next_times = [t.nextTime.t for t in td_int.values()] + [
                    t.nextTime.t for t in td_ext.values()
                ]
                tmin = min(all_next_times) if all_next_times else float("inf")

                # Update progress
                cpu_time = time.time() - t_start
                logger.info(
                    "[4/4] Iteration completed (sim_time=%.4f, cpu_time=%.2fs, delta=%.2fs)",
                    tmin,
                    cpu_time,
                    cpu_time - old_cpu_time,
                )
                old_cpu_time = cpu_time

            # Simulation complete - inform all workers
            logger.info("=" * 60)
            logger.info("SIMULATION COMPLETE - Notifying workers")
            logger.info("=" * 60)

            for w in self._workers.values():
                self._send_msg_to_mqtt(
                    msg=SimulationDone(time=st),
                    topic=w.get_topic_to_write(),
                )

            self._terminate_workers()
            logger.info("MS4Me MqttMS4Me Simulation Ended")

        except Exception as e:
            logger.error("Simulation error: %s", e, exc_info=True)
            self._terminate_workers()
            raise

    # ------------------------------------------------------------------
    #  Simulation entry point
    # ------------------------------------------------------------------

    def simulate(self, T=1e8, **kwargs):
        """Main simulation loop with MQTT coordination and message routing"""
        if self._simulator is None:
            raise ValueError("Simulator instance must be provided.")

        logger.info("=" * 60)
        logger.info("  MqttMS4Me Simulation Starting")
        logger.info("=" * 60)

        self._create_workers()

        logger.info("Waiting for workers to initialize (2s)...")
        time.sleep(2)

        # Purge old messages via proxy
        flushed = self._receiver_proxy.purge_old_messages(max_seconds=2.0)
        logger.info("System ready (flushed %d old messages)", flushed)

        return self._simulate_for_ms4me(T)

    def __del__(self):
        """Cleanup: close proxies properly"""
        try:
            if hasattr(self, '_stream_proxy'):
                self._stream_proxy.close()
            if hasattr(self, '_receiver_proxy'):
                self._receiver_proxy.close()
        except Exception as e:
            logger.error("Cleanup error: %s", e)
