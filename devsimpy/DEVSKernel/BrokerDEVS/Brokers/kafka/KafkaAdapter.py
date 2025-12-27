# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# KafkaAdapter.py ---
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
# Kafka-specific implementation of the BrokerAdapter interface.
# Handles creation of Kafka producer/consumer instances and message operations.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time
from typing import Any, Dict, Optional

from DEVSKernel.BrokerDEVS.Core.BrokerAdapter import BrokerAdapter

logger = logging.getLogger(__name__)

try:
    from confluent_kafka import Producer, Consumer, KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("confluent_kafka not available. Install with: pip install confluent-kafka")


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# KAFKA ADAPTER IMPLEMENTATION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class KafkaAdapter(BrokerAdapter):
    """
    Kafka-specific implementation of BrokerAdapter.
    
    Handles creation and configuration of Kafka producer/consumer instances
    for DEVS simulation distribution using Apache Kafka as the message broker.
    """

    # Default Kafka configuration
    DEFAULT_CONSUMER_CONFIG = {
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
        "session.timeout.ms": 6000,
        "heartbeat.interval.ms": 3000,
    }

    DEFAULT_PRODUCER_CONFIG = {
        "enable.idempotence": True,
        "acks": "all",
        "max.in.flight.requests.per.connection": 5,
        "retries": 10,
    }

    def __init__(self, bootstrap_servers: str, **kwargs):
        """
        Initialize Kafka adapter.
        
        Args:
            bootstrap_servers: Comma-separated list of Kafka brokers (e.g., "localhost:9092")
            **kwargs: Additional configuration options
            
        Raises:
            ImportError: If confluent_kafka is not installed
            ValueError: If bootstrap_servers is invalid
        """
        if not KAFKA_AVAILABLE:
            raise ImportError(
                "Kafka adapter requires 'confluent-kafka' library. "
                "Install with: pip install confluent-kafka"
            )

        if not bootstrap_servers or not isinstance(bootstrap_servers, str):
            raise ValueError("bootstrap_servers must be a non-empty string")

        self.bootstrap_servers = bootstrap_servers
        self.additional_config = kwargs
        logger.info("Initialized Kafka adapter with brokers: %s", bootstrap_servers)

    def create_consumer(self, config: Optional[Dict[str, Any]] = None) -> Consumer:
        """
        Create a Kafka consumer instance.
        
        Args:
            config: Consumer configuration dictionary. If None, uses defaults.
            
        Returns:
            Configured Kafka Consumer instance
            
        Raises:
            KafkaError: If consumer creation fails
        """
        if config is None:
            config = {}

        # Merge default + provided + additional config
        full_config = {
            "bootstrap.servers": self.bootstrap_servers,
            **self.DEFAULT_CONSUMER_CONFIG,
            **self.additional_config,
            **config,
        }

        # Ensure group.id is set (required for consumers)
        if "group.id" not in full_config:
            full_config["group.id"] = f"devsimpy-worker-{int(time.time() * 1000)}"

        logger.debug("Creating Kafka consumer with config: %s", full_config)
        return Consumer(full_config)

    def create_producer(self, config: Optional[Dict[str, Any]] = None) -> Producer:
        """
        Create a Kafka producer instance.
        
        Args:
            config: Producer configuration dictionary. If None, uses defaults.
            
        Returns:
            Configured Kafka Producer instance
            
        Raises:
            KafkaError: If producer creation fails
        """
        if config is None:
            config = {}

        # Merge default + provided + additional config
        full_config = {
            "bootstrap.servers": self.bootstrap_servers,
            **self.DEFAULT_PRODUCER_CONFIG,
            **self.additional_config,
            **config,
        }

        logger.debug("Creating Kafka producer with config: %s", full_config)
        return Producer(full_config)

    def extract_message_value(self, message: Any) -> bytes:
        """
        Extract the value from a Kafka message.
        
        Args:
            message: Kafka message object
            
        Returns:
            Message value as bytes
        """
        if message is None:
            return None
        return message.value()

    def get_topic(self, message: Any) -> str:
        """
        Get the topic from a Kafka message.
        
        Args:
            message: Kafka message object
            
        Returns:
            Topic name as string
        """
        if message is None:
            return None
        return message.topic()

    def has_error(self, message: Any) -> bool:
        """
        Check if a Kafka message contains an error.
        
        Args:
            message: Kafka message object
            
        Returns:
            True if message has an error, False otherwise
        """
        if message is None:
            return True
        error = message.error()
        return error is not None

    @property
    def broker_name(self) -> str:
        """Return broker name identifier."""
        return "kafka"

    def get_default_consumer_config(self) -> Dict[str, Any]:
        """Get default consumer configuration for this broker."""
        return self.DEFAULT_CONSUMER_CONFIG.copy()

    def get_default_producer_config(self) -> Dict[str, Any]:
        """Get default producer configuration for this broker."""
        return self.DEFAULT_PRODUCER_CONFIG.copy()

    def create_topics(
        self,
        topics: list,
        num_partitions: int = 1,
        replication_factor: int = 1,
    ) -> bool:
        """
        Create Kafka topics if they don't exist.
        
        Args:
            topics: List of topic names to create
            num_partitions: Number of partitions per topic
            replication_factor: Replication factor for topics
            
        Returns:
            True if topics were created successfully, False otherwise
            
        Note:
            Requires admin permissions on Kafka cluster.
            May fail if topics already exist (expected behavior).
        """
        try:
            from confluent_kafka.admin import AdminClient, NewTopic

            admin = AdminClient({"bootstrap.servers": self.bootstrap_servers})

            new_topics = [
                NewTopic(topic, num_partitions, replication_factor)
                for topic in topics
            ]

            fs = admin.create_topics(new_topics, validate_only=False)

            for topic, f in fs.items():
                try:
                    f.result()
                    logger.info("Topic created: %s", topic)
                except Exception as e:
                    if "already exists" in str(e):
                        logger.debug("Topic already exists: %s", topic)
                    else:
                        logger.warning("Failed to create topic %s: %s", topic, e)

            return True

        except ImportError:
            logger.warning(
                "AdminClient not available in confluent_kafka. "
                "Topics may need to be created manually."
            )
            return False
        except Exception as e:
            logger.error("Error creating topics: %s", e)
            return False

    def validate_connection(self) -> bool:
        """
        Validate connection to Kafka cluster.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            consumer = self.create_consumer({"group.id": "test-connection"})
            consumer.list_topics(timeout=5)
            consumer.close()
            logger.info("Kafka connection validation successful")
            return True
        except Exception as e:
            logger.error("Kafka connection validation failed: %s", e)
            return False


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# KAFKA CONFIGURATION HELPERS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class KafkaConfig:
    """Helper class for Kafka configuration."""

    @staticmethod
    def create_adapter(
        bootstrap_servers: str = "localhost:9092",
        **kwargs
    ) -> KafkaAdapter:
        """
        Create a KafkaAdapter with common defaults.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            **kwargs: Additional configuration
            
        Returns:
            Configured KafkaAdapter instance
        """
        return KafkaAdapter(bootstrap_servers, **kwargs)

    @staticmethod
    def create_local_adapter() -> KafkaAdapter:
        """Create adapter for local Kafka (localhost:9092)."""
        return KafkaAdapter("localhost:9092")

    @staticmethod
    def create_docker_adapter(container_name: str = "kafka") -> KafkaAdapter:
        """
        Create adapter for Docker Kafka container.
        
        Args:
            container_name: Docker container name (default: "kafka")
            
        Returns:
            Configured KafkaAdapter instance
        """
        return KafkaAdapter(f"{container_name}:9092")

    @staticmethod
    def get_security_config(
        security_protocol: str = "SASL_SSL",
        sasl_mechanism: str = "PLAIN",
        sasl_username: str = None,
        sasl_password: str = None,
        ssl_ca_location: str = None,
    ) -> Dict[str, Any]:
        """
        Get Kafka security configuration.
        
        Args:
            security_protocol: Security protocol (PLAINTEXT, SSL, SASL_SSL, SASL_PLAINTEXT)
            sasl_mechanism: SASL mechanism (PLAIN, SCRAM-SHA-256, SCRAM-SHA-512)
            sasl_username: SASL username
            sasl_password: SASL password
            ssl_ca_location: Path to CA certificate
            
        Returns:
            Security configuration dictionary
        """
        config = {
            "security.protocol": security_protocol,
        }

        if security_protocol.startswith("SASL"):
            config["sasl.mechanism"] = sasl_mechanism
            if sasl_username:
                config["sasl.username"] = sasl_username
            if sasl_password:
                config["sasl.password"] = sasl_password

        if security_protocol.endswith("SSL") and ssl_ca_location:
            config["ssl.ca.location"] = ssl_ca_location

        return config
