# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# kafkaconfig.py ---
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
# Kafka configuration management utilities for DEVS simulation.
# Provides:
#   - Default configuration presets
#   - Configuration builders
#   - Environment variable support
#   - Common topology setups (local, Docker, cloud)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# KAFKA CONFIGURATION CLASSES
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


@dataclass
class KafkaConsumerConfig:
    """Kafka consumer configuration dataclass."""
    
    bootstrap_servers: str = "localhost:9092"
    group_id: str = "devsimpy-consumer"
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    session_timeout_ms: int = 6000
    heartbeat_interval_ms: int = 3000
    max_poll_records: int = 500
    session_timeout_ms: int = 6000
    
    # Optional security
    security_protocol: Optional[str] = None
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_ca_location: Optional[str] = None
    
    # Advanced options
    connections_max_idle_ms: int = 540000
    request_timeout_ms: int = 30000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Kafka client configuration dictionary."""
        config = {}
        
        # Add all fields
        for key, value in asdict(self).items():
            if value is None:
                continue
            
            # Convert camelCase to kafka.config format
            kafka_key = self._to_kafka_key(key)
            config[kafka_key] = value
        
        return config
    
    @staticmethod
    def _to_kafka_key(key: str) -> str:
        """Convert Python snake_case to Kafka config format."""
        # Some special cases
        special_map = {
            "bootstrap_servers": "bootstrap.servers",
            "group_id": "group.id",
            "auto_offset_reset": "auto.offset.reset",
            "enable_auto_commit": "enable.auto.commit",
            "session_timeout_ms": "session.timeout.ms",
            "heartbeat_interval_ms": "heartbeat.interval.ms",
            "max_poll_records": "max.poll.records",
            "security_protocol": "security.protocol",
            "sasl_mechanism": "sasl.mechanism",
            "sasl_username": "sasl.username",
            "sasl_password": "sasl.password",
            "ssl_ca_location": "ssl.ca.location",
            "connections_max_idle_ms": "connections.max.idle.ms",
            "request_timeout_ms": "request.timeout.ms",
        }
        return special_map.get(key, key.replace("_", "."))


@dataclass
class KafkaProducerConfig:
    """Kafka producer configuration dataclass."""
    
    bootstrap_servers: str = "localhost:9092"
    acks: str = "all"
    enable_idempotence: bool = True
    max_in_flight_requests_per_connection: int = 5
    retries: int = 10
    retry_backoff_ms: int = 100
    compression_type: str = "snappy"
    
    # Optional security
    security_protocol: Optional[str] = None
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_ca_location: Optional[str] = None
    
    # Advanced options
    connections_max_idle_ms: int = 540000
    request_timeout_ms: int = 30000
    delivery_timeout_ms: int = 120000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Kafka client configuration dictionary."""
        config = {}
        
        for key, value in asdict(self).items():
            if value is None:
                continue
            
            kafka_key = self._to_kafka_key(key)
            config[kafka_key] = value
        
        return config
    
    @staticmethod
    def _to_kafka_key(key: str) -> str:
        """Convert Python snake_case to Kafka config format."""
        special_map = {
            "bootstrap_servers": "bootstrap.servers",
            "enable_idempotence": "enable.idempotence",
            "max_in_flight_requests_per_connection": "max.in.flight.requests.per.connection",
            "retry_backoff_ms": "retry.backoff.ms",
            "compression_type": "compression.type",
            "security_protocol": "security.protocol",
            "sasl_mechanism": "sasl.mechanism",
            "sasl_username": "sasl.username",
            "sasl_password": "sasl.password",
            "ssl_ca_location": "ssl.ca.location",
            "connections_max_idle_ms": "connections.max.idle.ms",
            "request_timeout_ms": "request.timeout.ms",
            "delivery_timeout_ms": "delivery.timeout.ms",
        }
        return special_map.get(key, key.replace("_", "."))


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CONFIGURATION PRESETS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class KafkaConfigPresets:
    """Pre-configured Kafka setups for common scenarios."""
    
    @staticmethod
    def local() -> tuple[KafkaConsumerConfig, KafkaProducerConfig]:
        """Configuration for local Kafka (localhost:9092)."""
        consumer = KafkaConsumerConfig(
            bootstrap_servers="localhost:9092",
            group_id="devsimpy-local",
            auto_offset_reset="latest",
        )
        producer = KafkaProducerConfig(
            bootstrap_servers="localhost:9092",
            acks="all",
            compression_type="snappy",
        )
        logger.info("Using local Kafka preset (localhost:9092)")
        return consumer, producer
    
    @staticmethod
    def docker(
        container_name: str = "kafka",
        port: int = 9092,
    ) -> tuple[KafkaConsumerConfig, KafkaProducerConfig]:
        """Configuration for Docker Kafka container."""
        bootstrap = f"{container_name}:{port}"
        consumer = KafkaConsumerConfig(
            bootstrap_servers=bootstrap,
            group_id="devsimpy-docker",
        )
        producer = KafkaProducerConfig(
            bootstrap_servers=bootstrap,
        )
        logger.info("Using Docker Kafka preset (%s)", bootstrap)
        return consumer, producer
    
    @staticmethod
    def confluent_cloud(
        cluster_id: str,
        api_key: str,
        api_secret: str,
        region: str = "us-east-1",
    ) -> tuple[KafkaConsumerConfig, KafkaProducerConfig]:
        """Configuration for Confluent Cloud."""
        bootstrap = f"pkc-{cluster_id}.{region}.provider.confluent.cloud:9092"
        
        security_config = {
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": "PLAIN",
            "sasl_username": api_key,
            "sasl_password": api_secret,
        }
        
        consumer = KafkaConsumerConfig(
            bootstrap_servers=bootstrap,
            group_id="devsimpy-confluent",
            **security_config,
        )
        producer = KafkaProducerConfig(
            bootstrap_servers=bootstrap,
            **security_config,
        )
        logger.info("Using Confluent Cloud preset (%s)", bootstrap)
        return consumer, producer
    
    @staticmethod
    def aws_msk(
        brokers: str,
        region: str = "us-east-1",
        certificate_path: Optional[str] = None,
    ) -> tuple[KafkaConsumerConfig, KafkaProducerConfig]:
        """Configuration for AWS MSK (Managed Streaming for Kafka)."""
        consumer = KafkaConsumerConfig(
            bootstrap_servers=brokers,
            group_id="devsimpy-msk",
            security_protocol="SSL",
            ssl_ca_location=certificate_path or "/etc/ssl/certs/ca-certificates.crt",
        )
        producer = KafkaProducerConfig(
            bootstrap_servers=brokers,
            security_protocol="SSL",
            ssl_ca_location=certificate_path or "/etc/ssl/certs/ca-certificates.crt",
        )
        logger.info("Using AWS MSK preset (region=%s)", region)
        return consumer, producer
    
    @staticmethod
    def azure_event_hubs(
        namespace: str,
        event_hub_name: str,
        connection_string: str,
    ) -> tuple[KafkaConsumerConfig, KafkaProducerConfig]:
        """Configuration for Azure Event Hubs (Kafka compatible)."""
        # Extract credentials from connection string
        # Format: Endpoint=sb://namespace.servicebus.windows.net/;SharedAccessKeyName=key;SharedAccessKey=value
        parts = connection_string.split(";")
        key_name = None
        key_value = None
        
        for part in parts:
            if "SharedAccessKeyName=" in part:
                key_name = part.split("=", 1)[1]
            elif "SharedAccessKey=" in part:
                key_value = part.split("=", 1)[1]
        
        bootstrap = f"{namespace}.servicebus.windows.net:9093"
        
        security_config = {
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": "PLAIN",
            "sasl_username": f"${key_name}",
            "sasl_password": key_value,
        }
        
        consumer = KafkaConsumerConfig(
            bootstrap_servers=bootstrap,
            group_id="devsimpy-eventhubs",
            **security_config,
        )
        producer = KafkaProducerConfig(
            bootstrap_servers=bootstrap,
            **security_config,
        )
        logger.info("Using Azure Event Hubs preset (namespace=%s)", namespace)
        return consumer, producer


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# ENVIRONMENT-BASED CONFIGURATION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class KafkaConfigFromEnv:
    """Load Kafka configuration from environment variables."""
    
    ENV_PREFIX = "KAFKA_"
    
    @staticmethod
    def get_consumer_config() -> KafkaConsumerConfig:
        """Load consumer config from KAFKA_* environment variables."""
        bootstrap = os.getenv(
            f"{KafkaConfigFromEnv.ENV_PREFIX}BOOTSTRAP_SERVERS",
            "localhost:9092"
        )
        group_id = os.getenv(
            f"{KafkaConfigFromEnv.ENV_PREFIX}GROUP_ID",
            "devsimpy-consumer"
        )
        
        config = KafkaConsumerConfig(
            bootstrap_servers=bootstrap,
            group_id=group_id,
        )
        
        logger.info(
            "Loaded consumer config from environment (bootstrap=%s)",
            bootstrap
        )
        return config
    
    @staticmethod
    def get_producer_config() -> KafkaProducerConfig:
        """Load producer config from KAFKA_* environment variables."""
        bootstrap = os.getenv(
            f"{KafkaConfigFromEnv.ENV_PREFIX}BOOTSTRAP_SERVERS",
            "localhost:9092"
        )
        
        config = KafkaProducerConfig(
            bootstrap_servers=bootstrap,
        )
        
        logger.info(
            "Loaded producer config from environment (bootstrap=%s)",
            bootstrap
        )
        return config
    
    @staticmethod
    def get_both() -> tuple[KafkaConsumerConfig, KafkaProducerConfig]:
        """Load both consumer and producer configs from environment."""
        return KafkaConfigFromEnv.get_consumer_config(), \
               KafkaConfigFromEnv.get_producer_config()


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CONFIGURATION BUILDER
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class KafkaConfigBuilder:
    """Fluent builder for Kafka configuration."""
    
    def __init__(self):
        """Initialize builder with default local config."""
        self.consumer_config = KafkaConsumerConfig()
        self.producer_config = KafkaProducerConfig()
    
    def bootstrap_servers(self, servers: str) -> "KafkaConfigBuilder":
        """Set bootstrap servers."""
        self.consumer_config.bootstrap_servers = servers
        self.producer_config.bootstrap_servers = servers
        return self
    
    def group_id(self, group_id: str) -> "KafkaConfigBuilder":
        """Set consumer group ID."""
        self.consumer_config.group_id = group_id
        return self
    
    def compression(self, compression_type: str) -> "KafkaConfigBuilder":
        """Set producer compression type (gzip, snappy, lz4, zstd)."""
        self.producer_config.compression_type = compression_type
        return self
    
    def security_sasl_plain(
        self,
        username: str,
        password: str,
    ) -> "KafkaConfigBuilder":
        """Enable SASL PLAIN security."""
        self.consumer_config.security_protocol = "SASL_SSL"
        self.consumer_config.sasl_mechanism = "PLAIN"
        self.consumer_config.sasl_username = username
        self.consumer_config.sasl_password = password
        
        self.producer_config.security_protocol = "SASL_SSL"
        self.producer_config.sasl_mechanism = "PLAIN"
        self.producer_config.sasl_username = username
        self.producer_config.sasl_password = password
        return self
    
    def security_ssl(self, ca_location: str) -> "KafkaConfigBuilder":
        """Enable SSL security."""
        self.consumer_config.security_protocol = "SSL"
        self.consumer_config.ssl_ca_location = ca_location
        
        self.producer_config.security_protocol = "SSL"
        self.producer_config.ssl_ca_location = ca_location
        return self
    
    def producer_acks(self, acks: str) -> "KafkaConfigBuilder":
        """Set producer acks (0, 1, all)."""
        self.producer_config.acks = acks
        return self
    
    def idempotent(self, enabled: bool = True) -> "KafkaConfigBuilder":
        """Enable/disable producer idempotence."""
        self.producer_config.enable_idempotence = enabled
        return self
    
    def timeouts(
        self,
        request_timeout_ms: int = 30000,
        session_timeout_ms: int = 6000,
    ) -> "KafkaConfigBuilder":
        """Configure timeouts."""
        self.consumer_config.request_timeout_ms = request_timeout_ms
        self.consumer_config.session_timeout_ms = session_timeout_ms
        
        self.producer_config.request_timeout_ms = request_timeout_ms
        return self
    
    def build(self) -> tuple[KafkaConsumerConfig, KafkaProducerConfig]:
        """Build the configuration."""
        return self.consumer_config, self.producer_config


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CONVENIENCE FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def get_config(
    bootstrap_servers: str = "localhost:9092",
    group_id: str = "devsimpy",
    preset: Optional[str] = None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Get Kafka configuration as dictionaries.
    
    Args:
        bootstrap_servers: Kafka bootstrap servers
        group_id: Consumer group ID
        preset: Use preset ('local', 'docker', etc.)
        
    Returns:
        Tuple of (consumer_config_dict, producer_config_dict)
    """
    if preset:
        preset_method = getattr(KafkaConfigPresets, preset, None)
        if preset_method:
            consumer, producer = preset_method()
            return consumer.to_dict(), producer.to_dict()
    
    consumer = KafkaConsumerConfig(
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
    )
    producer = KafkaProducerConfig(
        bootstrap_servers=bootstrap_servers,
    )
    
    return consumer.to_dict(), producer.to_dict()


def get_from_env() -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Get configuration from environment variables."""
    consumer, producer = KafkaConfigFromEnv.get_both()
    return consumer.to_dict(), producer.to_dict()
