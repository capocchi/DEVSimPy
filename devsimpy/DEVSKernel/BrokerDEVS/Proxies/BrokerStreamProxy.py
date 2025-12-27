# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# BrokerStreamProxy.py ---
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
# Generic sending proxy for distributed DEVS simulation.
# Works with any broker (Kafka, MQTT, RabbitMQ, etc.) via BrokerAdapter.
# Encapsulates all message sending logic in a broker-agnostic way.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import json
from typing import Dict, Any, Optional

from Patterns.Proxy import AbstractStreamProxy
from DEVSKernel.BrokerDEVS.Core.BrokerAdapter import BrokerAdapter
from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import BaseMessage
from DEVSKernel.BrokerDEVS.Core.BrokerWireAdapter import (
    WireAdapterFactory,
    BrokerWireAdapter,
)

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERIC BROKER STREAM PROXY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerStreamProxy(AbstractStreamProxy):
    """
    Generic message-sending proxy for any message broker.
    
    Works with:
    - Apache Kafka
    - MQTT
    - RabbitMQ
    - Redis
    - Azure Event Hubs
    - AWS MSK
    - Any other broker supported by a BrokerAdapter
    
    Encapsulates:
    - Producer creation and lifecycle
    - Message serialization
    - Topic management
    - Error handling and logging
    
    Features:
    - Broker-agnostic API
    - Automatic message serialization
    - Configurable wire formats (JSON, MessagePack, CloudEvents)
    - Thread-safe operations
    - Graceful shutdown
    """

    def __init__(
        self,
        broker_adapter: BrokerAdapter,
        producer_config: Optional[Dict[str, Any]] = None,
        wire_adapter: Optional[BrokerWireAdapter] = None,
    ):
        """
        Initialize the broker stream proxy.
        
        Args:
            broker_adapter: BrokerAdapter instance (e.g., KafkaAdapter, MqttAdapter)
            producer_config: Producer configuration dictionary (optional)
            wire_adapter: Message serialization adapter (default: JSON)
                Use WireAdapterFactory.create() for other formats
            
        Raises:
            ValueError: If broker_adapter is None
            ImportError: If broker dependencies are not installed
        """
        if broker_adapter is None:
            raise ValueError("broker_adapter must be provided")

        self.broker_adapter = broker_adapter
        self.producer = broker_adapter.create_producer(producer_config)

        # Use provided wire adapter or default to JSON
        if wire_adapter is None:
            self.wire_adapter = WireAdapterFactory.get_default()
        else:
            self.wire_adapter = wire_adapter

        # Get format name (compatible with both old and new wire adapters)
        format_name = getattr(self.wire_adapter, 'format_name', 'unknown')
        
        logger.info(
            "Initialized BrokerStreamProxy (broker=%s, wire_format=%s)",
            broker_adapter.broker_name,
            format_name,
        )

    def send_message(
        self,
        topic: str,
        msg: BaseMessage,
        key: Optional[str] = None,
    ) -> bool:
        """
        Send a message to a broker topic.
        
        Args:
            topic: Destination topic/channel
            msg: The BaseMessage to send
            key: Optional message key (e.g., model ID for Kafka partitioning)
            
        Returns:
            True if send was successful, False otherwise
            
        Raises:
            ValueError: If topic or msg is invalid
        """
        if not topic or not isinstance(topic, str):
            raise ValueError("topic must be a non-empty string")

        if not isinstance(msg, BaseMessage):
            raise ValueError("msg must be a BaseMessage instance")

        try:
            # Serialize message using wire adapter
            msg_data = self.wire_adapter.to_wire(msg)

            # Convert to bytes if needed (handle both dict and bytes returns)
            if isinstance(msg_data, dict):
                msg_bytes = json.dumps(msg_data).encode("utf-8")
            elif isinstance(msg_data, bytes):
                msg_bytes = msg_data
            else:
                msg_bytes = str(msg_data).encode("utf-8")

            # Encode key if provided
            key_bytes = key.encode("utf-8") if key else None

            # Send via broker producer
            self.producer.produce(topic, value=msg_bytes, key=key_bytes)
            self.producer.flush()

            logger.debug(
                "Sent message type=%s to topic=%s (broker=%s, size=%d bytes)",
                msg.devsType,
                topic,
                self.broker_adapter.broker_name,
                len(msg_bytes),
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to send message to topic %s: %s", topic, e, exc_info=True
            )
            return False

    def send_messages(self, topic: str, messages: list, key: Optional[str] = None) -> int:
        """
        Send multiple messages to a topic.
        
        Args:
            topic: Destination topic
            messages: List of BaseMessage objects
            key: Optional message key applied to all messages
            
        Returns:
            Number of messages sent successfully
        """
        sent_count = 0
        for msg in messages:
            if self.send_message(topic, msg, key):
                sent_count += 1
        return sent_count

    def flush(self, timeout: Optional[float] = None):
        """
        Flush pending messages to the broker.
        
        Args:
            timeout: Flush timeout in seconds (broker-dependent)
        """
        try:
            self.producer.flush(timeout)
            logger.debug("Flushed pending messages (broker=%s)", self.broker_adapter.broker_name)
        except Exception as e:
            logger.error("Error flushing messages: %s", e)

    def close(self):
        """
        Close the producer and cleanup resources.
        """
        try:
            self.flush()
            self.producer.close() if hasattr(self.producer, "close") else None
            logger.info(
                "BrokerStreamProxy closed (broker=%s)", self.broker_adapter.broker_name
            )
        except Exception as e:
            logger.error("Error closing producer: %s", e)

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
        """Return the wire format name (json, msgpack, cloudevents, etc.)."""
        return getattr(self.wire_adapter, 'format_name', 'unknown')

    def set_wire_adapter(self, wire_adapter: BrokerWireAdapter):
        """
        Change the message serialization format.
        
        Args:
            wire_adapter: New BrokerWireAdapter instance
        """
        self.wire_adapter = wire_adapter
        logger.info("Changed wire format to: %s", wire_adapter.format_name)

    def set_wire_format(self, format_name: str):
        """
        Change the message serialization format by name.
        
        Args:
            format_name: Format name ('json', 'msgpack', 'cloudevents', etc.)
        """
        self.wire_adapter = WireAdapterFactory.create(format_name)
        logger.info("Changed wire format to: %s", format_name)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# BROKER-SPECIFIC STREAM PROXIES (Convenience Classes)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class KafkaStreamProxy(BrokerStreamProxy):
    """
    Kafka-specific stream proxy.
    Convenience class for Kafka usage.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        producer_config: Optional[Dict[str, Any]] = None,
        wire_adapter: Optional[BrokerWireAdapter] = None,
    ):
        """
        Initialize Kafka stream proxy.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            producer_config: Custom producer configuration
            wire_adapter: Message serialization adapter
        """
        from DEVSKernel.BrokerDEVS.Brokers.kafka.KafkaAdapter import KafkaAdapter

        kafka_adapter = KafkaAdapter(bootstrap_servers)
        super().__init__(kafka_adapter, producer_config, wire_adapter)


class MqttStreamProxy(BrokerStreamProxy):
    """
    MQTT-specific stream proxy.
    Convenience class for MQTT usage.
    """

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        producer_config: Optional[Dict[str, Any]] = None,
        wire_adapter: Optional[BrokerWireAdapter] = None,
    ):
        """
        Initialize MQTT stream proxy.
        
        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            producer_config: Custom producer configuration
            wire_adapter: Message serialization adapter
        """
        from DEVSKernel.BrokerDEVS.Brokers.mqtt.MqttAdapter import MqttAdapter

        mqtt_config = producer_config or {}
        mqtt_config.update({
            "broker": broker_host,
            "port": broker_port,
        })
        mqtt_adapter = MqttAdapter(broker_host)
        super().__init__(mqtt_adapter, mqtt_config, wire_adapter)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# STREAM PROXY FACTORY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerStreamProxyFactory:
    """Factory for creating stream proxies."""

    @staticmethod
    def create(
        broker_type: str,
        wire_format: str = "json",
        **kwargs,
    ) -> BrokerStreamProxy:
        """
        Create a stream proxy for a specific broker.
        
        Args:
            broker_type: Broker type ('kafka', 'mqtt', 'rabbitmq', etc.)
            wire_format: Message format ('json', 'msgpack', 'cloudevents')
            **kwargs: Broker-specific arguments
            
        Returns:
            Configured BrokerStreamProxy instance
            
        Raises:
            ValueError: If broker_type is unknown
        """
        wire_adapter = WireAdapterFactory.create(wire_format)

        broker_type = broker_type.lower()

        if broker_type == "kafka":
            bootstrap = kwargs.get("bootstrap_servers", "localhost:9092")
            return KafkaStreamProxy(bootstrap, wire_adapter=wire_adapter)

        elif broker_type == "mqtt":
            host = kwargs.get("host", "localhost")
            port = kwargs.get("port", 1883)
            return MqttStreamProxy(host, port, wire_adapter=wire_adapter)

        elif broker_type == "rabbitmq":
            from DEVSKernel.BrokerDEVS.Brokers.rabbitmq.RabbitmqAdapter import (
                RabbitmqAdapter,
            )

            url = kwargs.get("url", "amqp://localhost")
            adapter = RabbitmqAdapter(url)
            return BrokerStreamProxy(adapter, wire_adapter=wire_adapter)

        else:
            raise ValueError(
                f"Unknown broker type: {broker_type}. "
                f"Supported: kafka, mqtt, rabbitmq"
            )

    @staticmethod
    def create_kafka(
        bootstrap_servers: str = "localhost:9092",
        wire_format: str = "json",
    ) -> BrokerStreamProxy:
        """Create a Kafka stream proxy."""
        return BrokerStreamProxyFactory.create(
            "kafka",
            bootstrap_servers=bootstrap_servers,
            wire_format=wire_format,
        )

    @staticmethod
    def create_mqtt(
        host: str = "localhost",
        port: int = 1883,
        wire_format: str = "json",
    ) -> BrokerStreamProxy:
        """Create an MQTT stream proxy."""
        return BrokerStreamProxyFactory.create(
            "mqtt",
            host=host,
            port=port,
            wire_format=wire_format,
        )
