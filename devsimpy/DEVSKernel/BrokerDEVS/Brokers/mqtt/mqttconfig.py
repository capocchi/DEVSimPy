# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# mqttconfig.py ---
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
# MQTT configuration management utilities for DEVS simulation.
# Provides:
#   - Default configuration presets
#   - Configuration builders
#   - Environment variable support
#   - Common topology setups (local, Docker, cloud)
#   - TLS/SSL and authentication configuration
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MQTT CONFIGURATION CLASSES
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


@dataclass
class MqttConsumerConfig:
    """MQTT consumer (subscriber) configuration dataclass."""
    
    broker_address: str = "localhost"
    broker_port: int = 1883
    client_id: str = "devsimpy-consumer"
    qos: int = 1
    keepalive: int = 60
    
    # Optional authentication
    username: Optional[str] = None
    password: Optional[str] = None
    
    # TLS/SSL options
    use_tls: bool = False
    tls_version: Optional[str] = None
    ca_certs: Optional[str] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    cert_reqs: Optional[int] = None
    ciphers: Optional[str] = None
    
    # Connection options
    clean_session: bool = True
    reconnect_max_delay: int = 32
    reconnect_min_delay: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to configuration dictionary."""
        config = {}
        
        for key, value in asdict(self).items():
            if value is None or key in ["use_tls", "ca_certs", "certfile", "keyfile", "cert_reqs", "ciphers"]:
                continue
            config[key] = value
        
        return config
    
    def get_tls_config(self) -> Optional[Dict[str, Any]]:
        """Get TLS configuration if enabled."""
        if not self.use_tls:
            return None
        
        tls_config = {}
        if self.ca_certs:
            tls_config["ca_certs"] = self.ca_certs
        if self.certfile:
            tls_config["certfile"] = self.certfile
        if self.keyfile:
            tls_config["keyfile"] = self.keyfile
        if self.cert_reqs is not None:
            tls_config["cert_reqs"] = self.cert_reqs
        if self.ciphers:
            tls_config["ciphers"] = self.ciphers
        if self.tls_version:
            tls_config["tls_version"] = self.tls_version
        
        return tls_config if tls_config else None


@dataclass
class MqttProducerConfig:
    """MQTT producer (publisher) configuration dataclass."""
    
    broker_address: str = "localhost"
    broker_port: int = 1883
    client_id: str = "devsimpy-producer"
    qos: int = 1
    keepalive: int = 60
    
    # Optional authentication
    username: Optional[str] = None
    password: Optional[str] = None
    
    # TLS/SSL options
    use_tls: bool = False
    tls_version: Optional[str] = None
    ca_certs: Optional[str] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    cert_reqs: Optional[int] = None
    ciphers: Optional[str] = None
    
    # Connection options
    clean_session: bool = True
    reconnect_max_delay: int = 32
    reconnect_min_delay: int = 1
    
    # Publishing options
    retain: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to configuration dictionary."""
        config = {}
        
        for key, value in asdict(self).items():
            if value is None or key in ["use_tls", "ca_certs", "certfile", "keyfile", "cert_reqs", "ciphers"]:
                continue
            config[key] = value
        
        return config
    
    def get_tls_config(self) -> Optional[Dict[str, Any]]:
        """Get TLS configuration if enabled."""
        if not self.use_tls:
            return None
        
        tls_config = {}
        if self.ca_certs:
            tls_config["ca_certs"] = self.ca_certs
        if self.certfile:
            tls_config["certfile"] = self.certfile
        if self.keyfile:
            tls_config["keyfile"] = self.keyfile
        if self.cert_reqs is not None:
            tls_config["cert_reqs"] = self.cert_reqs
        if self.ciphers:
            tls_config["ciphers"] = self.ciphers
        if self.tls_version:
            tls_config["tls_version"] = self.tls_version
        
        return tls_config if tls_config else None


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CONFIGURATION PRESETS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MqttConfigPresets:
    """Pre-configured MQTT setups for common scenarios."""
    
    @staticmethod
    def local() -> tuple[MqttConsumerConfig, MqttProducerConfig]:
        """Configuration for local MQTT broker (localhost:1883)."""
        consumer = MqttConsumerConfig(
            broker_address="localhost",
            broker_port=1883,
            client_id="devsimpy-local-consumer",
            qos=1,
        )
        producer = MqttProducerConfig(
            broker_address="localhost",
            broker_port=1883,
            client_id="devsimpy-local-producer",
            qos=1,
        )
        logger.info("Using local MQTT preset (localhost:1883)")
        return consumer, producer
    
    @staticmethod
    def docker(
        container_name: str = "mosquitto",
        port: int = 1883,
    ) -> tuple[MqttConsumerConfig, MqttProducerConfig]:
        """Configuration for Docker MQTT container (Mosquitto)."""
        consumer = MqttConsumerConfig(
            broker_address=container_name,
            broker_port=port,
            client_id="devsimpy-docker-consumer",
        )
        producer = MqttProducerConfig(
            broker_address=container_name,
            broker_port=port,
            client_id="devsimpy-docker-producer",
        )
        logger.info("Using Docker MQTT preset (%s:%d)", container_name, port)
        return consumer, producer
    
    @staticmethod
    def mosquitto_public(
        broker_address: str = "test.mosquitto.org",
        port: int = 1883,
    ) -> tuple[MqttConsumerConfig, MqttProducerConfig]:
        """Configuration for public Mosquitto test broker."""
        consumer = MqttConsumerConfig(
            broker_address=broker_address,
            broker_port=port,
            client_id="devsimpy-mosquitto-consumer",
        )
        producer = MqttProducerConfig(
            broker_address=broker_address,
            broker_port=port,
            client_id="devsimpy-mosquitto-producer",
        )
        logger.info("Using public Mosquitto preset (%s:%d)", broker_address, port)
        return consumer, producer
    
    @staticmethod
    def aws_iot(
        endpoint: str,
        region: str = "us-east-1",
        ca_cert_path: str = None,
        client_cert_path: str = None,
        client_key_path: str = None,
        client_id: str = "devsimpy-aws",
    ) -> tuple[MqttConsumerConfig, MqttProducerConfig]:
        """Configuration for AWS IoT Core."""
        consumer = MqttConsumerConfig(
            broker_address=endpoint,
            broker_port=8883,
            client_id=f"{client_id}-consumer",
            use_tls=True,
            ca_certs=ca_cert_path,
            certfile=client_cert_path,
            keyfile=client_key_path,
        )
        producer = MqttProducerConfig(
            broker_address=endpoint,
            broker_port=8883,
            client_id=f"{client_id}-producer",
            use_tls=True,
            ca_certs=ca_cert_path,
            certfile=client_cert_path,
            keyfile=client_key_path,
        )
        logger.info("Using AWS IoT Core preset (endpoint=%s, region=%s)", endpoint, region)
        return consumer, producer
    
    @staticmethod
    def azure_iot_hub(
        hostname: str,
        device_id: str,
        shared_access_key: str,
        ca_cert_path: str = None,
    ) -> tuple[MqttConsumerConfig, MqttProducerConfig]:
        """Configuration for Azure IoT Hub."""
        import base64
        import hashlib
        
        # Generate SAS token if needed
        username = f"{hostname}/{device_id}/?api-version=2021-04-12"
        
        consumer = MqttConsumerConfig(
            broker_address=hostname,
            broker_port=8883,
            client_id=device_id,
            username=username,
            password=shared_access_key,
            use_tls=True,
            ca_certs=ca_cert_path,
        )
        producer = MqttProducerConfig(
            broker_address=hostname,
            broker_port=8883,
            client_id=device_id,
            username=username,
            password=shared_access_key,
            use_tls=True,
            ca_certs=ca_cert_path,
        )
        logger.info("Using Azure IoT Hub preset (hostname=%s, device=%s)", hostname, device_id)
        return consumer, producer
    
    @staticmethod
    def gcp_iot_core(
        project_id: str,
        region: str,
        registry_id: str,
        device_id: str,
        private_key_path: str,
        ca_cert_path: str = None,
    ) -> tuple[MqttConsumerConfig, MqttProducerConfig]:
        """Configuration for Google Cloud IoT Core."""
        hostname = f"mqtt.googleapis.com"
        client_id = f"projects/{project_id}/locations/{region}/registries/{registry_id}/devices/{device_id}"
        
        consumer = MqttConsumerConfig(
            broker_address=hostname,
            broker_port=8883,
            client_id=client_id,
            username="unused",
            password=private_key_path,  # JWT token would be loaded from this path
            use_tls=True,
            ca_certs=ca_cert_path,
        )
        producer = MqttProducerConfig(
            broker_address=hostname,
            broker_port=8883,
            client_id=client_id,
            username="unused",
            password=private_key_path,  # JWT token would be loaded from this path
            use_tls=True,
            ca_certs=ca_cert_path,
        )
        logger.info("Using GCP IoT Core preset (project=%s, region=%s)", project_id, region)
        return consumer, producer


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# ENVIRONMENT-BASED CONFIGURATION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MqttConfigFromEnv:
    """Create MQTT configuration from environment variables."""
    
    PREFIX = "MQTT_"
    
    @staticmethod
    def create_consumer_config() -> MqttConsumerConfig:
        """
        Create consumer config from environment variables.
        
        Supported variables:
        - MQTT_BROKER_ADDRESS (default: localhost)
        - MQTT_BROKER_PORT (default: 1883)
        - MQTT_CLIENT_ID (default: devsimpy-consumer)
        - MQTT_QOS (default: 1)
        - MQTT_KEEPALIVE (default: 60)
        - MQTT_USERNAME (optional)
        - MQTT_PASSWORD (optional)
        - MQTT_USE_TLS (default: false)
        - MQTT_CA_CERTS (optional)
        - MQTT_CERTFILE (optional)
        - MQTT_KEYFILE (optional)
        """
        broker_address = os.getenv(f"{MqttConfigFromEnv.PREFIX}BROKER_ADDRESS", "localhost")
        broker_port = int(os.getenv(f"{MqttConfigFromEnv.PREFIX}BROKER_PORT", "1883"))
        client_id = os.getenv(f"{MqttConfigFromEnv.PREFIX}CLIENT_ID", "devsimpy-consumer")
        qos = int(os.getenv(f"{MqttConfigFromEnv.PREFIX}QOS", "1"))
        keepalive = int(os.getenv(f"{MqttConfigFromEnv.PREFIX}KEEPALIVE", "60"))
        username = os.getenv(f"{MqttConfigFromEnv.PREFIX}USERNAME")
        password = os.getenv(f"{MqttConfigFromEnv.PREFIX}PASSWORD")
        use_tls = os.getenv(f"{MqttConfigFromEnv.PREFIX}USE_TLS", "false").lower() == "true"
        ca_certs = os.getenv(f"{MqttConfigFromEnv.PREFIX}CA_CERTS")
        certfile = os.getenv(f"{MqttConfigFromEnv.PREFIX}CERTFILE")
        keyfile = os.getenv(f"{MqttConfigFromEnv.PREFIX}KEYFILE")
        
        config = MqttConsumerConfig(
            broker_address=broker_address,
            broker_port=broker_port,
            client_id=client_id,
            qos=qos,
            keepalive=keepalive,
            username=username,
            password=password,
            use_tls=use_tls,
            ca_certs=ca_certs,
            certfile=certfile,
            keyfile=keyfile,
        )
        
        logger.info(
            "Created consumer config from environment: %s:%d (qos=%d, tls=%s)",
            broker_address, broker_port, qos, use_tls
        )
        return config
    
    @staticmethod
    def create_producer_config() -> MqttProducerConfig:
        """
        Create producer config from environment variables.
        
        Supported variables: same as create_consumer_config()
        """
        broker_address = os.getenv(f"{MqttConfigFromEnv.PREFIX}BROKER_ADDRESS", "localhost")
        broker_port = int(os.getenv(f"{MqttConfigFromEnv.PREFIX}BROKER_PORT", "1883"))
        client_id = os.getenv(f"{MqttConfigFromEnv.PREFIX}CLIENT_ID", "devsimpy-producer")
        qos = int(os.getenv(f"{MqttConfigFromEnv.PREFIX}QOS", "1"))
        keepalive = int(os.getenv(f"{MqttConfigFromEnv.PREFIX}KEEPALIVE", "60"))
        username = os.getenv(f"{MqttConfigFromEnv.PREFIX}USERNAME")
        password = os.getenv(f"{MqttConfigFromEnv.PREFIX}PASSWORD")
        use_tls = os.getenv(f"{MqttConfigFromEnv.PREFIX}USE_TLS", "false").lower() == "true"
        ca_certs = os.getenv(f"{MqttConfigFromEnv.PREFIX}CA_CERTS")
        certfile = os.getenv(f"{MqttConfigFromEnv.PREFIX}CERTFILE")
        keyfile = os.getenv(f"{MqttConfigFromEnv.PREFIX}KEYFILE")
        
        config = MqttProducerConfig(
            broker_address=broker_address,
            broker_port=broker_port,
            client_id=client_id,
            qos=qos,
            keepalive=keepalive,
            username=username,
            password=password,
            use_tls=use_tls,
            ca_certs=ca_certs,
            certfile=certfile,
            keyfile=keyfile,
        )
        
        logger.info(
            "Created producer config from environment: %s:%d (qos=%d, tls=%s)",
            broker_address, broker_port, qos, use_tls
        )
        return config


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CONFIGURATION BUILDER (FLUENT API)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MqttConfigBuilder:
    """Fluent API for building MQTT configurations."""
    
    def __init__(self, config_type: str = "consumer"):
        """Initialize builder."""
        if config_type == "consumer":
            self._config = MqttConsumerConfig()
        elif config_type == "producer":
            self._config = MqttProducerConfig()
        else:
            raise ValueError(f"Unknown config type: {config_type}")
    
    def broker(self, address: str, port: int = 1883) -> "MqttConfigBuilder":
        """Set broker address and port."""
        self._config.broker_address = address
        self._config.broker_port = port
        return self
    
    def client_id(self, client_id: str) -> "MqttConfigBuilder":
        """Set client ID."""
        self._config.client_id = client_id
        return self
    
    def qos(self, qos: int) -> "MqttConfigBuilder":
        """Set QoS level (0, 1, or 2)."""
        if not 0 <= qos <= 2:
            raise ValueError("QoS must be 0, 1, or 2")
        self._config.qos = qos
        return self
    
    def keepalive(self, seconds: int) -> "MqttConfigBuilder":
        """Set keepalive interval in seconds."""
        self._config.keepalive = seconds
        return self
    
    def auth(self, username: str, password: str) -> "MqttConfigBuilder":
        """Set authentication credentials."""
        self._config.username = username
        self._config.password = password
        return self
    
    def tls(
        self,
        ca_certs: str = None,
        certfile: str = None,
        keyfile: str = None,
        cert_reqs: int = None,
        tls_version: str = None,
    ) -> "MqttConfigBuilder":
        """Enable TLS/SSL with optional certificates."""
        self._config.use_tls = True
        if ca_certs:
            self._config.ca_certs = ca_certs
        if certfile:
            self._config.certfile = certfile
        if keyfile:
            self._config.keyfile = keyfile
        if cert_reqs is not None:
            self._config.cert_reqs = cert_reqs
        if tls_version:
            self._config.tls_version = tls_version
        return self
    
    def clean_session(self, clean: bool = True) -> "MqttConfigBuilder":
        """Set clean session flag."""
        self._config.clean_session = clean
        return self
    
    def reconnect_delays(self, min_delay: int = 1, max_delay: int = 32) -> "MqttConfigBuilder":
        """Set reconnection delay bounds."""
        self._config.reconnect_min_delay = min_delay
        self._config.reconnect_max_delay = max_delay
        return self
    
    def build(self) -> Any:
        """Build and return the configuration."""
        return self._config


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# HELPER FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def create_local_mqtt_config() -> tuple[MqttConsumerConfig, MqttProducerConfig]:
    """Create configuration for local MQTT broker."""
    return MqttConfigPresets.local()


def create_docker_mqtt_config(
    container_name: str = "mosquitto",
) -> tuple[MqttConsumerConfig, MqttProducerConfig]:
    """Create configuration for Docker MQTT broker."""
    return MqttConfigPresets.docker(container_name)


def build_consumer_config() -> MqttConfigBuilder:
    """Start building a consumer configuration."""
    return MqttConfigBuilder("consumer")


def build_producer_config() -> MqttConfigBuilder:
    """Start building a producer configuration."""
    return MqttConfigBuilder("producer")
