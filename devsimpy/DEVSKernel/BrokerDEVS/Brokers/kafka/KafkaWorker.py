# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# KafkaWorker.py ---
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
# Kafka-specific worker implementation for distributed DEVS simulation.
# Uses the generic KafkaAdapter to manage producer/consumer instances.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time
import threading
from typing import Dict, Any, Optional

from DEVSKernel.BrokerDEVS.Core.BrokerAdapter import BrokerAdapter
from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import BaseMessage
from DEVSKernel.BrokerDEVS.Brokers.kafka.KafkaAdapter import KafkaAdapter, KafkaConfig

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# KAFKA WORKER THREAD
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class KafkaWorker(threading.Thread):
    """
    Kafka-specific worker thread for distributed DEVS simulation.
    
    Manages one atomic DEVS model running in-memory while communicating
    with the simulation coordinator via Kafka topics.
    
    Features:
    - Receives commands from coordinator on input topic
    - Sends model outputs to coordinator on output topic
    - Handles message serialization/deserialization
    - Thread-safe operations
    """

    def __init__(
        self,
        model_name: str,
        aDEVS,
        bootstrap_servers: str = "localhost:9092",
        in_topic: str = None,
        out_topic: str = None,
        consumer_config: Optional[Dict[str, Any]] = None,
        producer_config: Optional[Dict[str, Any]] = None,
        kafka_adapter: Optional[KafkaAdapter] = None,
    ):
        """
        Initialize Kafka worker.
        
        Args:
            model_name: Name/identifier for the DEVS model
            aDEVS: The atomic DEVS model instance
            bootstrap_servers: Kafka bootstrap server address
            in_topic: Topic to receive commands from coordinator
            out_topic: Topic to send model outputs to coordinator
            consumer_config: Custom consumer configuration (overrides defaults)
            producer_config: Custom producer configuration (overrides defaults)
            kafka_adapter: Custom KafkaAdapter instance (if None, creates default)
            
        Raises:
            ValueError: If topics are not provided
            ImportError: If confluent_kafka is not installed
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

        # Create or use provided Kafka adapter
        self.kafka_adapter = kafka_adapter or KafkaAdapter(bootstrap_servers)

        # Consumer configuration - set group_id to model-specific value
        consumer_cfg = consumer_config or {}
        if "group.id" not in consumer_cfg:
            consumer_cfg["group.id"] = (
                f"worker-{aDEVS.myID}-{int(time.time() * 1000)}"
            )

        # Create Kafka producer and consumer
        self.consumer = self.kafka_adapter.create_consumer(consumer_cfg)
        self.producer = self.kafka_adapter.create_producer(producer_config)

        # Subscribe to input topic
        try:
            self.consumer.subscribe([self.in_topic])
            logger.info(
                "Kafka worker initialized for model '%s' "
                "(consumer group=%s, in_topic=%s, out_topic=%s)",
                model_name,
                consumer_cfg.get("group.id"),
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
        logger.info("Starting Kafka worker for model '%s'", self.model_name)

        try:
            while self.running:
                # Poll for message with timeout
                message = self.consumer.poll(timeout=1.0)

                if message is None:
                    continue

                # Check for errors
                if self.kafka_adapter.has_error(message):
                    error = message.error()
                    logger.error("Kafka error: %s", error)
                    continue

                # Extract message value and deserialize
                try:
                    msg_bytes = self.kafka_adapter.extract_message_value(message)
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
                    key=self.model_name.encode("utf-8"),
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
            logger.info("Kafka worker stopped for model '%s'", self.model_name)
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
# SPECIALIZED KAFKA WORKER VARIANTS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class KafkaWorkerWithAdapter(KafkaWorker):
    """
    Extended Kafka worker that handles wire adapter for serialization.
    
    Allows customization of message serialization format (JSON, MessagePack, etc.)
    """

    def __init__(
        self,
        model_name: str,
        aDEVS,
        bootstrap_servers: str = "localhost:9092",
        in_topic: str = None,
        out_topic: str = None,
        wire_adapter=None,
        **kwargs,
    ):
        """
        Initialize with wire adapter support.
        
        Args:
            model_name: Model identifier
            aDEVS: DEVS model instance
            bootstrap_servers: Kafka bootstrap servers
            in_topic: Input topic
            out_topic: Output topic
            wire_adapter: Message serialization adapter (default: JSON)
            **kwargs: Additional arguments for KafkaWorker
        """
        super().__init__(
            model_name=model_name,
            aDEVS=aDEVS,
            bootstrap_servers=bootstrap_servers,
            in_topic=in_topic,
            out_topic=out_topic,
            **kwargs,
        )

        from DEVSKernel.BrokerDEVS.Core.BrokerWireAdapter import (
            WireAdapterFactory,
        )

        self.wire_adapter = (
            wire_adapter or WireAdapterFactory.get_default()
        )
        logger.debug(
            "Using wire adapter: %s", self.wire_adapter.format_name
        )

    def _handle_message(self, msg: BaseMessage):
        """Handle message with wire adapter."""
        logger.debug(
            "Processing %s message from %s",
            msg.devsType,
            msg.sender if hasattr(msg, "sender") else "unknown",
        )

    def send_message(self, msg: BaseMessage) -> bool:
        """Send message with wire adapter serialization."""
        if not self.running:
            logger.warning("Worker not running, cannot send message")
            return False

        try:
            with self._lock:
                msg_bytes = self.wire_adapter.to_wire(msg)
                self.producer.produce(
                    self.out_topic,
                    value=msg_bytes,
                    key=self.model_name.encode("utf-8"),
                )
                self.producer.flush()
                logger.debug(
                    "Sent %s message to topic=%s (format=%s)",
                    msg.devsType,
                    self.out_topic,
                    self.wire_adapter.format_name,
                )
                return True
        except Exception as e:
            logger.error("Failed to send message: %s", e)
            return False


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# KAFKA WORKER FACTORY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class KafkaWorkerFactory:
    """Factory for creating Kafka workers."""

    @staticmethod
    def create(
        model_name: str,
        aDEVS,
        bootstrap_servers: str = "localhost:9092",
        in_topic: str = None,
        out_topic: str = None,
        with_wire_adapter: bool = False,
        **kwargs,
    ) -> KafkaWorker:
        """
        Create a Kafka worker.
        
        Args:
            model_name: Model identifier
            aDEVS: DEVS model instance
            bootstrap_servers: Kafka brokers
            in_topic: Input topic
            out_topic: Output topic
            with_wire_adapter: Use wire adapter for custom serialization
            **kwargs: Additional configuration
            
        Returns:
            Configured KafkaWorker instance
        """
        if with_wire_adapter:
            return KafkaWorkerWithAdapter(
                model_name=model_name,
                aDEVS=aDEVS,
                bootstrap_servers=bootstrap_servers,
                in_topic=in_topic,
                out_topic=out_topic,
                **kwargs,
            )
        else:
            return KafkaWorker(
                model_name=model_name,
                aDEVS=aDEVS,
                bootstrap_servers=bootstrap_servers,
                in_topic=in_topic,
                out_topic=out_topic,
                **kwargs,
            )

    @staticmethod
    def create_local(
        model_name: str,
        aDEVS,
        in_topic: str,
        out_topic: str,
        **kwargs,
    ) -> KafkaWorker:
        """Create worker for local Kafka (localhost:9092)."""
        return KafkaWorkerFactory.create(
            model_name=model_name,
            aDEVS=aDEVS,
            bootstrap_servers="localhost:9092",
            in_topic=in_topic,
            out_topic=out_topic,
            **kwargs,
        )

    @staticmethod
    def create_docker(
        model_name: str,
        aDEVS,
        in_topic: str,
        out_topic: str,
        container_name: str = "kafka",
        **kwargs,
    ) -> KafkaWorker:
        """Create worker for Docker Kafka container."""
        return KafkaWorkerFactory.create(
            model_name=model_name,
            aDEVS=aDEVS,
            bootstrap_servers=f"{container_name}:9092",
            in_topic=in_topic,
            out_topic=out_topic,
            **kwargs,
        )
