# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# MqttWorker.py ---
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
# MQTT-specific worker implementation for distributed DEVS simulation.
# Uses the generic MqttAdapter to manage publisher/subscriber instances.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time
import threading
from typing import Dict, Any, Optional

from DEVSKernel.BrokerDEVS.Core.BrokerAdapter import BrokerAdapter
from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import BaseMessage
from DEVSKernel.BrokerDEVS.Brokers.mqtt.MqttAdapter import MqttAdapter, MqttConfig

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MQTT WORKER THREAD
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MqttWorker(threading.Thread):
    """
    MQTT-specific worker thread for distributed DEVS simulation.
    
    Manages one atomic DEVS model running in-memory while communicating
    with the simulation coordinator via MQTT topics.
    
    Features:
    - Receives commands from coordinator on input topic
    - Sends model outputs to coordinator on output topic
    - Handles message serialization/deserialization
    - Thread-safe operations
    - Automatic reconnection on disconnect
    """

    def __init__(
        self,
        model_name: str,
        aDEVS,
        broker_address: str = "localhost",
        broker_port: int = 1883,
        in_topic: str = None,
        out_topic: str = None,
        consumer_config: Optional[Dict[str, Any]] = None,
        producer_config: Optional[Dict[str, Any]] = None,
        mqtt_adapter: Optional[MqttAdapter] = None,
    ):
        """
        Initialize MQTT worker.
        
        Args:
            model_name: Name/identifier for the DEVS model
            aDEVS: The atomic DEVS model instance
            broker_address: MQTT broker address (default: localhost)
            broker_port: MQTT broker port (default: 1883)
            in_topic: Topic to receive commands from coordinator
            out_topic: Topic to send model outputs to coordinator
            consumer_config: Custom consumer configuration (overrides defaults)
            producer_config: Custom producer configuration (overrides defaults)
            mqtt_adapter: Custom MqttAdapter instance (if None, creates default)
            
        Raises:
            ValueError: If topics are not provided
            ImportError: If paho-mqtt is not installed
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

        # Create or use provided MQTT adapter
        self.mqtt_adapter = mqtt_adapter or MqttAdapter(broker_address, broker_port)

        # Consumer and producer configuration
        consumer_cfg = consumer_config or {}
        producer_cfg = producer_config or {}

        # Create MQTT producer and consumer
        self.consumer = self.mqtt_adapter.create_consumer(consumer_cfg)
        self.producer = self.mqtt_adapter.create_producer(producer_cfg)

        # Subscribe to input topic
        try:
            self.consumer.subscribe(self.in_topic)
            logger.info(
                "MQTT worker initialized for model '%s' "
                "(broker=%s:%d, in_topic=%s, out_topic=%s)",
                model_name,
                broker_address,
                broker_port,
                in_topic,
                out_topic,
            )
        except Exception as e:
            logger.error("Failed to subscribe to topic %s: %s", in_topic, e)
            raise

    def run(self):
        """
        Main worker thread loop.
        Polls for messages from coordinator and processes them.
        """
        logger.info("Starting MQTT worker for model '%s'", self.model_name)

        try:
            while self.running:
                # Poll for message with timeout
                message = self.consumer.poll(timeout=1.0)

                if message is None:
                    continue

                # Check for errors
                if self.mqtt_adapter.has_error(message):
                    error = message.error()
                    logger.error("MQTT error: %s", error)
                    continue

                # Extract message value and deserialize
                try:
                    msg_bytes = self.mqtt_adapter.extract_message_value(message)
                    if msg_bytes is None:
                        continue

                    # Deserialize message
                    msg = BaseMessage.from_bytes(msg_bytes)
                    logger.debug(
                        "Received message type=%s from topic=%s",
                        msg.devsType,
                        self.in_topic,
                    )

                    # Process message (to be implemented by subclass or caller)
                    self._handle_message(msg)

                except Exception as e:
                    logger.error("Error processing message: %s", e, exc_info=True)

        except Exception as e:
            logger.error("Worker thread error: %s", e, exc_info=True)
        finally:
            self.stop()

    def _handle_message(self, msg: BaseMessage):
        """
        Handle a received message.
        
        Args:
            msg: The deserialized message
            
        Note:
            Override this method in subclasses to implement specific behavior.
        """
        # Default implementation: log the message
        logger.debug("Handling message: %s", msg)

    def send_message(self, msg: BaseMessage) -> bool:
        """
        Send a message to the coordinator via output topic.
        
        Args:
            msg: Message to send
            
        Returns:
            True if send was successful, False otherwise
        """
        if not self.running:
            logger.warning("Worker not running, cannot send message")
            return False

        try:
            with self._lock:
                msg_bytes = msg.to_bytes()
                self.producer.produce(
                    self.out_topic,
                    value=msg_bytes,
                    key=self.model_name,
                )
                self.producer.flush()
                logger.debug(
                    "Sent message type=%s to topic=%s",
                    msg.devsType,
                    self.out_topic,
                )
                return True
        except Exception as e:
            logger.error("Failed to send message: %s", e)
            return False

    def stop(self):
        """Stop the worker and cleanup resources."""
        with self._lock:
            self.running = False

        try:
            self.consumer.close()
            self.producer.flush()
            self.producer.close()
            logger.info("MQTT worker stopped for model '%s'", self.model_name)
        except Exception as e:
            logger.error("Error stopping worker: %s", e)

    def get_model(self):
        """Return the atomic DEVS model managed by this worker."""
        return self.aDEVS

    def get_model_label(self):
        """Return the model name/label."""
        return self.model_name

    def is_running(self) -> bool:
        """Check if worker is running."""
        return self.running


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# SPECIALIZED MQTT WORKER VARIANTS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MqttWorkerWithAdapter(MqttWorker):
    """
    Extended MQTT worker that handles wire adapter for serialization.
    
    Allows customization of message serialization format (JSON, MessagePack, etc.)
    through a pluggable wire format adapter.
    """

    def __init__(
        self,
        model_name: str,
        aDEVS,
        broker_address: str = "localhost",
        broker_port: int = 1883,
        in_topic: str = None,
        out_topic: str = None,
        wire_adapter=None,
        consumer_config: Optional[Dict[str, Any]] = None,
        producer_config: Optional[Dict[str, Any]] = None,
        mqtt_adapter: Optional[MqttAdapter] = None,
    ):
        """
        Initialize MQTT worker with wire adapter.
        
        Args:
            model_name: Name/identifier for the DEVS model
            aDEVS: The atomic DEVS model instance
            broker_address: MQTT broker address
            broker_port: MQTT broker port
            in_topic: Topic to receive commands
            out_topic: Topic to send outputs
            wire_adapter: Serialization format adapter (JSON, MessagePack, etc.)
            consumer_config: Custom consumer configuration
            producer_config: Custom producer configuration
            mqtt_adapter: Custom MqttAdapter instance
        """
        super().__init__(
            model_name,
            aDEVS,
            broker_address,
            broker_port,
            in_topic,
            out_topic,
            consumer_config,
            producer_config,
            mqtt_adapter,
        )
        self.wire_adapter = wire_adapter

    def send_message(self, msg: BaseMessage) -> bool:
        """
        Send a message with wire adapter serialization.
        
        Args:
            msg: Message to send
            
        Returns:
            True if send was successful, False otherwise
        """
        if not self.running:
            logger.warning("Worker not running, cannot send message")
            return False

        try:
            with self._lock:
                # Use wire adapter if available
                if self.wire_adapter:
                    msg_bytes = self.wire_adapter.serialize(msg)
                else:
                    msg_bytes = msg.to_bytes()

                self.producer.produce(
                    self.out_topic,
                    value=msg_bytes,
                    key=self.model_name,
                )
                self.producer.flush()
                logger.debug(
                    "Sent message type=%s to topic=%s",
                    msg.devsType,
                    self.out_topic,
                )
                return True
        except Exception as e:
            logger.error("Failed to send message: %s", e)
            return False

    def _handle_message(self, msg: BaseMessage):
        """
        Handle message with potential wire adapter deserialization.
        
        Args:
            msg: Message to handle
        """
        # If wire adapter is available, it has already been used during deserialization
        logger.debug("Handling message with wire adapter: %s", msg)


class MqttWorkerFactory:
    """Factory for creating MQTT workers with various configurations."""

    @staticmethod
    def create_worker(
        model_name: str,
        aDEVS,
        broker_address: str = "localhost",
        broker_port: int = 1883,
        in_topic: str = None,
        out_topic: str = None,
        with_adapter: bool = False,
        wire_adapter=None,
    ) -> MqttWorker:
        """
        Create an MQTT worker.
        
        Args:
            model_name: Model name/identifier
            aDEVS: Atomic DEVS model instance
            broker_address: MQTT broker address
            broker_port: MQTT broker port
            in_topic: Input topic name
            out_topic: Output topic name
            with_adapter: If True, create MqttWorkerWithAdapter
            wire_adapter: Wire format adapter for serialization
            
        Returns:
            Configured MqttWorker instance
        """
        if with_adapter:
            return MqttWorkerWithAdapter(
                model_name,
                aDEVS,
                broker_address,
                broker_port,
                in_topic,
                out_topic,
                wire_adapter,
            )
        else:
            return MqttWorker(
                model_name,
                aDEVS,
                broker_address,
                broker_port,
                in_topic,
                out_topic,
            )

    @staticmethod
    def create_local_worker(
        model_name: str,
        aDEVS,
        in_topic: str = None,
        out_topic: str = None,
        **kwargs
    ) -> MqttWorker:
        """
        Create worker for local MQTT broker (localhost:1883).
        
        Args:
            model_name: Model name/identifier
            aDEVS: Atomic DEVS model instance
            in_topic: Input topic name
            out_topic: Output topic name
            **kwargs: Additional arguments passed to worker
            
        Returns:
            Configured MqttWorker instance
        """
        return MqttWorker(
            model_name,
            aDEVS,
            broker_address="localhost",
            broker_port=1883,
            in_topic=in_topic,
            out_topic=out_topic,
            **kwargs
        )

    @staticmethod
    def create_docker_worker(
        model_name: str,
        aDEVS,
        container_name: str = "mosquitto",
        in_topic: str = None,
        out_topic: str = None,
        **kwargs
    ) -> MqttWorker:
        """
        Create worker for Docker MQTT container.
        
        Args:
            model_name: Model name/identifier
            aDEVS: Atomic DEVS model instance
            container_name: Docker container name
            in_topic: Input topic name
            out_topic: Output topic name
            **kwargs: Additional arguments passed to worker
            
        Returns:
            Configured MqttWorker instance
        """
        return MqttWorker(
            model_name,
            aDEVS,
            broker_address=container_name,
            broker_port=1883,
            in_topic=in_topic,
            out_topic=out_topic,
            **kwargs
        )
