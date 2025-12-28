# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# BrokerReceiverProxy.py ---
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
# Generic receiving proxy for distributed DEVS simulation.
# Works with any broker (Kafka, MQTT, RabbitMQ, etc.) via BrokerAdapter.
# Encapsulates all message receiving and correlation logic in a broker-agnostic way.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time
from typing import Dict, Any, List, Optional
from collections import defaultdict

from Patterns.Proxy import AbstractReceiverProxy
from DEVSKernel.BrokerDEVS.Core.BrokerAdapter import BrokerAdapter
from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import BaseMessage
from DEVSKernel.BrokerDEVS.Core.BrokerWireAdapter import (
    WireAdapterFactory,
    BrokerWireAdapter,
)

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERIC BROKER RECEIVER PROXY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerReceiverProxy(AbstractReceiverProxy):
    """
    Generic message-receiving proxy for any message broker.
    
    Works with:
    - Apache Kafka
    - MQTT
    - RabbitMQ
    - Redis
    - Azure Event Hubs
    - AWS MSK
    - Any other broker supported by a BrokerAdapter
    
    Encapsulates:
    - Consumer creation and lifecycle
    - Message deserialization
    - Topic subscription management
    - Message correlation and timeout handling
    - Message buffering and filtering
    
    Features:
    - Broker-agnostic API
    - Automatic message deserialization
    - Configurable wire formats (JSON, MessagePack, CloudEvents)
    - Timeout and deadline management
    - Message filtering by sender
    - Purge old messages functionality
    - Thread-safe operations
    """

    def __init__(
        self,
        broker_adapter: BrokerAdapter,
        consumer_config: Optional[Dict[str, Any]] = None,
        wire_adapter: Optional[BrokerWireAdapter] = None,
    ):
        """
        Initialize the broker receiver proxy.
        
        Args:
            broker_adapter: BrokerAdapter instance (e.g., KafkaAdapter, MqttAdapter)
            consumer_config: Consumer configuration dictionary (optional)
            wire_adapter: Message deserialization adapter (default: JSON)
                Use WireAdapterFactory.create() for other formats
            
        Raises:
            ValueError: If broker_adapter is None
            ImportError: If broker dependencies are not installed
        """
        if broker_adapter is None:
            raise ValueError("broker_adapter must be provided")

        self.broker_adapter = broker_adapter
        self.consumer = broker_adapter.create_consumer(consumer_config)

        # Use provided wire adapter or default to JSON
        if wire_adapter is None:
            self.wire_adapter = WireAdapterFactory.get_default()
        else:
            self.wire_adapter = wire_adapter

        self._subscribed_topics = []
        self._message_buffer = defaultdict(list)  # topic -> [messages]

        # Get format name (compatible with both old and new wire adapters)
        format_name = getattr(self.wire_adapter, 'format_name', 'unknown')
        
        logger.info(
            "Initialized BrokerReceiverProxy (broker=%s, wire_format=%s)",
            broker_adapter.broker_name,
            format_name,
        )

    def subscribe(self, topics: List[str], seek_to_end: bool = True) -> None:
        """
        Subscribe to one or more topics/channels.
        
        Args:
            topics: List of topic names to subscribe to
            seek_to_end: If True, seek to end of topics so only NEW messages are received
                        (default: True, prevents receiving old messages from topic history)
            
        Raises:
            ValueError: If topics list is empty
        """
        if not topics:
            raise ValueError("topics list cannot be empty")

        try:
            self.consumer.subscribe(topics)
            self._subscribed_topics = topics.copy()
            
            # Seek to end if requested (prevents reading old messages)
            if seek_to_end:
                self._seek_to_end(topics)
            
            logger.info(
                "Subscribed to topics: %s (broker=%s, seek_to_end=%s)",
                topics,
                self.broker_adapter.broker_name,
                seek_to_end,
            )
        except Exception as e:
            logger.error("Failed to subscribe to topics %s: %s", topics, e)
            raise

    def _seek_to_end(self, topics: List[str]) -> None:
        """
        Seek to the end of topics so consumer only reads NEW messages.
        This prevents reading old messages from topic history when using 'earliest' offset reset.
        
        Args:
            topics: List of topics to seek to end
        """
        try:
            import time as time_module
            from confluent_kafka import TopicPartition, OFFSET_END
            
            # Give consumer time to join group and get partition assignments
            time_module.sleep(0.5)
            
            # Get partitions for subscribed topics
            partitions = self.consumer.assignment()
            if not partitions:
                # If no partitions assigned yet, poll once to trigger assignment
                self.consumer.poll(timeout=100)
                partitions = self.consumer.assignment()
            
            if partitions:
                # Seek each partition to its end
                for partition in partitions:
                    # Create TopicPartition with OFFSET_END to go to end
                    tp = TopicPartition(partition.topic, partition.partition, OFFSET_END)
                    self.consumer.seek(tp)
                
                # Force a commit so the group remembers we're at the end
                self.consumer.commit(asynchronous=False)
                logger.debug("Sought to end of %d partitions and committed offset", len(partitions))
            else:
                logger.warning("No partitions assigned - consumer may not be ready")
        except Exception as e:
            logger.warning("Failed to seek to end: %s (will read from history)", e)

    def receive_messages(
        self,
        pending: List[Any],
        timeout: float,
    ) -> Dict[Any, BaseMessage]:
        """
        Wait for and collect messages from specified workers/models.
        
        Args:
            pending: List of DEVS models/workers from which responses are expected
            timeout: Maximum wait time in seconds
            
        Returns:
            Dictionary mapping each model to its received message
            
        Raises:
            TimeoutError: If not all expected messages are received within timeout
        """
        if not pending:
            return {}

        received = {}
        remaining = list(pending)
        deadline = time.time() + timeout
        pending_senders = set()

        # Extract expected sender identifiers
        for model in pending:
            sender_id = self._get_model_identifier(model)
            if sender_id:
                pending_senders.add(sender_id)

        logger.debug(
            "Waiting for messages from %d models (timeout=%.1fs)",
            len(pending),
            timeout,
        )

        while remaining and time.time() < deadline:
            time_remaining = deadline - time.time()
            poll_timeout = min(0.5, max(0.1, time_remaining))

            try:
                # Poll for message
                message = self.consumer.poll(timeout=poll_timeout)

                if message is None:
                    continue

                # Check for errors
                if self.broker_adapter.has_error(message):
                    error = message.error() if hasattr(message, "error") else "Unknown"
                    logger.warning("Message error from broker: %s", error)
                    continue

                # Extract and deserialize message
                topic = self.broker_adapter.get_topic(message)
                msg_bytes = self.broker_adapter.extract_message_value(message)

                if msg_bytes is None:
                    continue

                try:
                    # Use wire adapter to deserialize (supports pickle, JSON, etc.)
                    msg = self.wire_adapter.from_wire(msg_bytes)
                except Exception as e:
                    logger.error(
                        "Failed to deserialize message from bytes: %s. Raw data: %s",
                        e,
                        msg_bytes[:200] if msg_bytes else None,
                        exc_info=True,
                    )
                    continue

                sender_id = getattr(msg, "sender", None)

                logger.debug(
                    "Received message type=%s from sender=%s (topic=%s)",
                    msg.devsType if hasattr(msg, "devsType") else "UNKNOWN",
                    sender_id,
                    topic,
                )

                # Find and match to pending model
                if sender_id:
                    for i, model in enumerate(remaining):
                        model_id = self._get_model_identifier(model)
                        if model_id == sender_id:
                            matched_model = remaining.pop(i)
                            received[matched_model] = msg
                            pending_senders.discard(sender_id)
                            logger.debug(
                                "Matched message to model %s",
                                model_id,
                            )
                            break
                else:
                    logger.warning("Received message without sender identifier")

            except Exception as e:
                logger.error("Error processing message: %s", e, exc_info=True)

        # Check if timeout occurred
        if remaining:
            missing_ids = [
                self._get_model_identifier(m) for m in remaining
            ]
            logger.error(
                "Timeout waiting for messages from: %s", missing_ids
            )
            raise TimeoutError(
                f"Timeout after {timeout}s: missing responses from models {missing_ids}"
            )

        logger.debug("Received messages from all %d models", len(received))
        return received

    def receive_message(
        self,
        timeout: float = 5.0,
        sender_id: Optional[str] = None,
    ) -> Optional[BaseMessage]:
        """
        Receive a single message (optionally filtered by sender).
        
        Args:
            timeout: Maximum wait time in seconds
            sender_id: Filter by sender identifier (optional)
            
        Returns:
            Received BaseMessage, or None if timeout
        """
        deadline = time.time() + timeout

        while time.time() < deadline:
            time_remaining = deadline - time.time()
            poll_timeout = min(0.5, max(0.1, time_remaining))

            try:
                message = self.consumer.poll(timeout=poll_timeout)

                if message is None:
                    continue

                if self.broker_adapter.has_error(message):
                    continue

                msg_bytes = self.broker_adapter.extract_message_value(message)
                if msg_bytes is None:
                    continue

                msg = self.wire_adapter.from_wire(msg_bytes)

                # Filter by sender if specified
                if sender_id:
                    if getattr(msg, "sender", None) != sender_id:
                        # Buffer this message for later
                        topic = self.broker_adapter.get_topic(message)
                        self._message_buffer[topic].append(msg)
                        continue

                logger.debug("Received message type=%s", msg.devsType)
                return msg

            except Exception as e:
                logger.error("Error receiving message: %s", e, exc_info=True)

        logger.warning("Timeout receiving message after %.1fs", timeout)
        return None

    def purge_old_messages(
        self,
        max_time: float = None,
        max_count: int = None,
        max_seconds: float = None,
    ) -> int:
        """
        Purge old/stale messages from the topic.
        
        Useful for clearing accumulated messages before starting fresh.
        
        Args:
            max_time: Maximum time to spend purging (seconds). Default 2.0.
            max_count: Maximum number of messages to purge (None = unlimited)
            max_seconds: (Deprecated) Alias for max_time, provided for backward compatibility
            
        Returns:
            Number of messages purged
        """
        # Handle backward compatibility: max_seconds is alias for max_time
        if max_seconds is not None:
            max_time = max_seconds
        if max_time is None:
            max_time = 2.0
        purged = 0
        start_time = time.time()
        deadline = start_time + max_time

        logger.info(
            "Purging old messages (max_time=%.1fs, broker=%s)",
            max_time,
            self.broker_adapter.broker_name,
        )

        while time.time() < deadline:
            if max_count is not None and purged >= max_count:
                break

            message = self.consumer.poll(timeout=0.1)

            if message is None:
                # No messages available for 100ms - good sign
                logger.debug("No messages available during purge (purged so far: %d)", purged)
                continue

            if not self.broker_adapter.has_error(message):
                purged += 1
                logger.debug("Purged message #%d", purged)

        if purged > 0:
            logger.info("Purged %d old messages from topic", purged)
        else:
            logger.info("No old messages to purge - topic is clean")
        
        return purged

        # After purging, reset consumer to beginning so new messages aren't missed
        # This is critical because purging removes messages that the consumer's offset points to
        self._reset_to_beginning()
        
        return purged

    def _reset_to_beginning(self) -> None:
        """
        Reset consumer to beginning of assigned partitions.
        This is needed after purging messages to ensure the consumer doesn't get stuck.
        """
        try:
            import time as time_module
            from confluent_kafka import TopicPartition, OFFSET_BEGINNING
            
            # Give consumer a moment to process the poll calls from purging
            time_module.sleep(0.1)
            
            # Get current partition assignments
            partitions = self.consumer.assignment()
            if partitions:
                # Seek each partition to the beginning
                for partition in partitions:
                    tp = TopicPartition(partition.topic, partition.partition, OFFSET_BEGINNING)
                    self.consumer.seek(tp)
                
                logger.debug("Reset consumer to beginning of %d partitions", len(partitions))
        except Exception as e:
            logger.warning("Failed to reset to beginning: %s", e)

    def flush_buffer(self) -> List[BaseMessage]:
        """
        Get all buffered messages and clear the buffer.
        
        Returns:
            List of all buffered messages
        """
        buffered = []
        for messages in self._message_buffer.values():
            buffered.extend(messages)
        self._message_buffer.clear()
        return buffered

    def close(self):
        """
        Close the consumer and cleanup resources.
        """
        try:
            self.consumer.close()
            logger.info(
                "BrokerReceiverProxy closed (broker=%s)",
                self.broker_adapter.broker_name,
            )
        except Exception as e:
            logger.error("Error closing consumer: %s", e)

    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # PROPERTIES AND ACCESSORS
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    @property
    def broker_name(self) -> str:
        """Return the name of the broker being used."""
        return self.broker_adapter.broker_name

    @property
    def wire_format(self) -> str:
        """Return the wire format name."""
        return getattr(self.wire_adapter, 'format_name', 'unknown')

    @property
    def subscribed_topics(self) -> List[str]:
        """Return list of subscribed topics."""
        return self._subscribed_topics.copy()

    def set_wire_adapter(self, wire_adapter: BrokerWireAdapter):
        """
        Change the message deserialization format.
        
        Args:
            wire_adapter: New BrokerWireAdapter instance
        """
        self.wire_adapter = wire_adapter
        logger.info("Changed wire format to: %s", wire_adapter.format_name)

    def set_wire_format(self, format_name: str):
        """
        Change the message deserialization format by name.
        
        Args:
            format_name: Format name ('json', 'msgpack', 'cloudevents', etc.)
        """
        self.wire_adapter = WireAdapterFactory.create(format_name)
        logger.info("Changed wire format to: %s", format_name)

    @staticmethod
    def _get_model_identifier(model: Any) -> Optional[str]:
        """
        Extract identifier from a DEVS model.
        
        Args:
            model: DEVS model object
            
        Returns:
            Model identifier string, or None if not found
        """
        # Try different attribute names
        for attr in ["label", "name", "myID", "id"]:
            if hasattr(model, attr):
                value = getattr(model, attr)
                if value is not None:
                    return str(value)

        # Try getBlockModel().label pattern
        if hasattr(model, "getBlockModel"):
            try:
                block = model.getBlockModel()
                if hasattr(block, "label"):
                    return str(block.label)
            except Exception:
                pass

        return None





## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# RECEIVER PROXY FACTORY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerReceiverProxyFactory:
    """Factory for creating receiver proxies."""

    @staticmethod
    def create(
        broker_type: str,
        wire_format: str = "json",
        **kwargs,
    ) -> BrokerReceiverProxy:
        """
        Create a receiver proxy for a specific broker.
        
        Args:
            broker_type: Broker type ('kafka', 'mqtt', 'rabbitmq', etc.)
            wire_format: Message format ('json', 'msgpack', 'cloudevents')
            **kwargs: Broker-specific arguments
            
        Returns:
            Configured BrokerReceiverProxy instance
            
        Raises:
            ValueError: If broker_type is unknown
        """
        wire_adapter = WireAdapterFactory.create(wire_format)

        broker_type = broker_type.lower()

        if broker_type == "kafka":
            from Proxies.kafka import KafkaReceiverProxy
            bootstrap = kwargs.get("bootstrap_servers", "localhost:9092")
            group_id = kwargs.get("group_id", "devsimpy-receiver")
            return KafkaReceiverProxy(bootstrap, group_id, wire_adapter=wire_adapter)

        elif broker_type == "mqtt":
            from Proxies.mqtt import MqttReceiverProxy
            host = kwargs.get("host", "localhost")
            port = kwargs.get("port", 1883)
            client_id = kwargs.get("client_id", "devsimpy-receiver")
            return MqttReceiverProxy(host, port, client_id, wire_adapter=wire_adapter)

        elif broker_type == "rabbitmq":
            from Proxies.rabbitmq import RabbitmqReceiverProxy
            url = kwargs.get("url", "amqp://localhost")
            return RabbitmqReceiverProxy(url, wire_adapter=wire_adapter)

        else:
            raise ValueError(
                f"Unknown broker type: {broker_type}. "
                f"Supported: kafka, mqtt, rabbitmq"
            )

    @staticmethod
    def create_kafka(
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "devsimpy-receiver",
        wire_format: str = "json",
    ) -> BrokerReceiverProxy:
        """Create a Kafka receiver proxy."""
        return BrokerReceiverProxyFactory.create(
            "kafka",
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            wire_format=wire_format,
        )

    @staticmethod
    def create_mqtt(
        host: str = "localhost",
        port: int = 1883,
        client_id: str = "devsimpy-receiver",
        wire_format: str = "json",
    ) -> BrokerReceiverProxy:
        """Create an MQTT receiver proxy."""
        return BrokerReceiverProxyFactory.create(
            "mqtt",
            host=host,
            port=port,
            client_id=client_id,
            wire_format=wire_format,
        )
