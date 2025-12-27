# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# MS4MeMqttWorker.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/26/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# MQTT-specific worker for MS4Me distributed DEVS simulation.
# Mirrors MS4MeKafkaWorker but uses MQTT as the message broker.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time
import threading
from typing import Dict, Any, Optional

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise ImportError("paho-mqtt package required. Install with: pip install paho-mqtt")

from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import (
    BaseMessage,
    SimTime,
    InitSim,
    NextTime,
    ExecuteTransition,
    SendOutput,
    ModelOutputMessage,
    ModelDone,
    TransitionDone,
    SimulationDone,
    PortValue,
)

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MQTT WORKER THREAD
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MS4MeMqttWorker(threading.Thread):
    """
    MQTT-based worker thread for MS4Me distributed DEVS simulation.
    
    Manages one atomic DEVS model running in-memory while communicating
    with the coordinator via MQTT topics.
    
    Features:
    - Receives commands from coordinator on input topic
    - Sends model outputs to coordinator on output topic
    - Handles MS4Me message serialization/deserialization
    - Thread-safe operations
    - Automatic reconnection on disconnect
    """

    OUT_TOPIC = "ms4me-outputs"  # Shared output topic for all workers

    def __init__(
        self,
        model_name: str,
        aDEVS,
        broker_address: str = "localhost",
        broker_port: int = 1883,
        in_topic: str = None,
        out_topic: str = None,
        wire_adapter=None,
        qos: int = 1,
        keepalive: int = 60,
    ):
        """
        Initialize MQTT worker.
        
        Args:
            model_name: Name/identifier for the DEVS model
            aDEVS: The atomic DEVS model instance
            broker_address: MQTT broker address
            broker_port: MQTT broker port
            in_topic: Topic to receive commands from coordinator
            out_topic: Topic to send model outputs to coordinator
            wire_adapter: Message serialization adapter (StandardWireAdapter)
            qos: MQTT QoS level (0, 1, or 2)
            keepalive: MQTT keepalive interval in seconds
        """
        super().__init__(daemon=True)

        if not in_topic or not out_topic:
            raise ValueError("Both in_topic and out_topic must be provided")

        self.aDEVS = aDEVS
        self.model_name = model_name
        self.in_topic = in_topic
        self.out_topic = out_topic
        self.running = True
        self._lock = threading.Lock()

        # MQTT configuration
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.qos = qos
        self.keepalive = keepalive

        # Wire adapter for message serialization
        self.wire_adapter = wire_adapter

        # MQTT client
        self.client = mqtt.Client(
            client_id=f"worker-{model_name}-{int(time.time() * 1000)}",
            protocol=mqtt.MQTTv311,
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Message queue for received commands
        self._message_queue = []
        self._message_ready = threading.Event()

        # Connection state
        self._connected = False
        self._connection_timeout = 10.0
        self._last_message_time = 0.0

        logger.info(
            "MS4MeMqttWorker initialized: %s (in=%s, out=%s, broker=%s:%d)",
            model_name, in_topic, out_topic, broker_address, broker_port
        )

    # ------------------------------------------------------------------
    #  MQTT Callbacks
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc):
        """Called when connected to MQTT broker"""
        if rc == 0:
            logger.info("Worker %s: Connected to MQTT broker", self.model_name)
            self._connected = True
            # Subscribe to input topic
            self.client.subscribe(self.in_topic, qos=self.qos)
            logger.info("Worker %s: Subscribed to %s", self.model_name, self.in_topic)
        else:
            logger.error(
                "Worker %s: Failed to connect to MQTT broker (code: %d)",
                self.model_name, rc
            )

    def _on_disconnect(self, client, userdata, rc):
        """Called when disconnected from MQTT broker"""
        self._connected = False
        if rc != 0:
            logger.warning(
                "Worker %s: Unexpected disconnection from MQTT broker (code: %d)",
                self.model_name, rc
            )

    def _on_message(self, client, userdata, msg):
        """Called when a message is received"""
        try:
            # Deserialize message using wire adapter
            if self.wire_adapter:
                devs_msg = self.wire_adapter.deserialize(msg.payload)
            else:
                # Fallback if no wire adapter
                import pickle
                devs_msg = pickle.loads(msg.payload)

            with self._lock:
                self._message_queue.append(devs_msg)
                self._message_ready.set()

            logger.debug(
                "Worker %s: Received %s",
                self.model_name,
                type(devs_msg).__name__
            )
        except Exception as e:
            logger.error(
                "Worker %s: Error deserializing message: %s",
                self.model_name, e
            )

    # ------------------------------------------------------------------
    #  Public Interface
    # ------------------------------------------------------------------

    def get_model(self):
        """Get the DEVS model"""
        return self.aDEVS

    def get_model_label(self):
        """Get the model's label"""
        return self.model_name

    def get_model_time_next(self):
        """Get the model's next transition time"""
        return self.aDEVS.timeNext if hasattr(self.aDEVS, 'timeNext') else float("inf")

    def get_topic_to_write(self):
        """Get the topic to send commands to this worker"""
        return self.in_topic

    def get_topic_to_read(self):
        """Get the topic to read outputs from this worker"""
        return self.out_topic

    def stop(self):
        """Stop the worker thread"""
        with self._lock:
            self.running = False
        self.client.disconnect()

    # ------------------------------------------------------------------
    #  Message Sending
    # ------------------------------------------------------------------

    def _send_message(self, msg: BaseMessage, topic: str) -> bool:
        """
        Send a message to a topic.
        
        Args:
            msg: The message to send
            topic: The MQTT topic
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._connected:
            logger.warning(
                "Worker %s: Not connected to broker, cannot send message",
                self.model_name
            )
            return False

        try:
            # Serialize message using wire adapter
            if self.wire_adapter:
                payload = self.wire_adapter.serialize(msg)
            else:
                # Fallback if no wire adapter
                import pickle
                payload = pickle.dumps(msg)

            result = self.client.publish(topic, payload, qos=self.qos)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(
                    "Worker %s: Failed to publish to %s (code: %d)",
                    self.model_name, topic, result.rc
                )
                return False

            logger.debug(
                "Worker %s: Sent %s to %s",
                self.model_name,
                type(msg).__name__,
                topic
            )
            return True
        except Exception as e:
            logger.error(
                "Worker %s: Error sending message: %s",
                self.model_name, e
            )
            return False

    # ------------------------------------------------------------------
    #  Message Receiving
    # ------------------------------------------------------------------

    def _get_message(self, timeout: float = 30.0) -> Optional[BaseMessage]:
        """
        Get the next message from the queue.
        
        Args:
            timeout: How long to wait for a message (seconds)
            
        Returns:
            The message, or None if timeout
        """
        self._message_ready.clear()

        # Check if there's already a message
        with self._lock:
            if self._message_queue:
                return self._message_queue.pop(0)

        # Wait for a message
        if self._message_ready.wait(timeout=timeout):
            with self._lock:
                if self._message_queue:
                    return self._message_queue.pop(0)

        logger.warning(
            "Worker %s: Timeout waiting for message (timeout=%.1fs)",
            self.model_name, timeout
        )
        return None

    # ------------------------------------------------------------------
    #  Model Execution
    # ------------------------------------------------------------------

    def _handle_init_sim(self, msg: InitSim) -> NextTime:
        """Handle InitSim command"""
        logger.info("Worker %s: Handling InitSim at t=%s", self.model_name, msg.time.t)

        self.aDEVS.init(msg.time.t)

        next_time = NextTime(
            time=msg.time,
            nextTime=SimTime(t=self.aDEVS.timeNext)
        )
        logger.info(
            "Worker %s: InitSim complete, next transition at t=%s",
            self.model_name, self.aDEVS.timeNext
        )
        return next_time

    def _handle_send_output(self, msg: SendOutput) -> ModelOutputMessage:
        """Handle SendOutput command"""
        logger.info("Worker %s: Handling SendOutput at t=%s", self.model_name, msg.time.t)

        # Execute output function
        self.aDEVS.outputFnc()

        # Collect port values
        port_values = []
        for port in getattr(self.aDEVS, 'OPorts', []):
            if port.values:
                for value in port.values:
                    pv = PortValue(value, port.name, type(value).__name__)
                    port_values.append(pv)

        output_msg = ModelOutputMessage(
            time=msg.time,
            modelOutput=port_values
        )
        logger.info(
            "Worker %s: SendOutput complete, produced %d outputs",
            self.model_name, len(port_values)
        )
        return output_msg

    def _handle_execute_transition(self, msg: ExecuteTransition) -> TransitionDone:
        """Handle ExecuteTransition command"""
        logger.info(
            "Worker %s: Handling ExecuteTransition at t=%s",
            self.model_name, msg.time.t
        )

        # Apply external inputs if provided
        if msg.inputs:
            for pv in msg.inputs:
                for port in getattr(self.aDEVS, 'IPorts', []):
                    if port.name == pv.portIdentifier:
                        port.put(pv.value)

        # Execute internal transition
        self.aDEVS.intTransition()

        transition_done = TransitionDone(
            time=msg.time,
            nextTime=SimTime(t=self.aDEVS.timeNext)
        )
        logger.info(
            "Worker %s: ExecuteTransition complete, next transition at t=%s",
            self.model_name, self.aDEVS.timeNext
        )
        return transition_done

    def _handle_simulation_done(self, msg: SimulationDone):
        """Handle SimulationDone command"""
        logger.info("Worker %s: Simulation done at t=%s", self.model_name, msg.time.t)
        self.stop()

    # ------------------------------------------------------------------
    #  Main Worker Loop
    # ------------------------------------------------------------------

    def run(self):
        """Main worker thread loop"""
        try:
            # Connect to MQTT broker
            logger.info(
                "Worker %s: Connecting to MQTT broker at %s:%d",
                self.model_name, self.broker_address, self.broker_port
            )
            self.client.connect(
                self.broker_address,
                self.broker_port,
                keepalive=self.keepalive
            )
            self.client.loop_start()

            # Wait for connection
            start_time = time.time()
            while not self._connected and (time.time() - start_time) < self._connection_timeout:
                time.sleep(0.1)

            if not self._connected:
                raise RuntimeError(
                    f"Worker {self.model_name}: Failed to connect to MQTT broker"
                )

            logger.info("Worker %s: Ready and waiting for commands", self.model_name)

            # Main command loop
            while self.running:
                msg = self._get_message(timeout=30.0)

                if msg is None:
                    if self.running:
                        logger.warning("Worker %s: Message timeout", self.model_name)
                    continue

                if not self.running:
                    break

                # Process command
                response = None

                try:
                    if isinstance(msg, InitSim):
                        response = self._handle_init_sim(msg)
                    elif isinstance(msg, SendOutput):
                        response = self._handle_send_output(msg)
                    elif isinstance(msg, ExecuteTransition):
                        response = self._handle_execute_transition(msg)
                    elif isinstance(msg, SimulationDone):
                        self._handle_simulation_done(msg)
                        break
                    else:
                        logger.warning(
                            "Worker %s: Unknown message type: %s",
                            self.model_name, type(msg).__name__
                        )
                        continue

                    # Send response
                    if response:
                        self._send_message(response, self.OUT_TOPIC)

                except Exception as e:
                    logger.error(
                        "Worker %s: Error processing message: %s",
                        self.model_name, e, exc_info=True
                    )

        except Exception as e:
            logger.error(
                "Worker %s: Fatal error: %s",
                self.model_name, e, exc_info=True
            )
        finally:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception as e:
                logger.error("Worker %s: Cleanup error: %s", self.model_name, e)

            logger.info("Worker %s: Thread terminated", self.model_name)
