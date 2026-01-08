# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# MqttAdapter.py ---
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
# MQTT-specific implementation of the BrokerAdapter interface.
# Handles creation of MQTT publisher/subscriber instances and message operations.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time
import json
from typing import Any, Dict, Optional, Callable
from threading import Event
from queue import Queue

from DEVSKernel.BrokerDEVS.Core.BrokerAdapter import BrokerAdapter

logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("paho-mqtt not available. Install with: pip install paho-mqtt")


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MQTT MESSAGE WRAPPER
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MqttMessage:
    """Wrapper for MQTT messages to provide consistent interface."""
    
    def __init__(self, topic: str, payload: bytes, qos: int = 0):
        """
        Initialize MQTT message wrapper.
        
        Args:
            topic: Topic name
            payload: Message payload as bytes
            qos: Quality of Service level
        """
        self.topic_name = topic
        self.payload = payload
        self.qos = qos
        self.error_obj = None
    
    def topic(self) -> str:
        """Return topic name."""
        return self.topic_name
    
    def value(self) -> bytes:
        """Return message payload."""
        return self.payload
    
    def error(self) -> Optional[Any]:
        """Return error object (if any)."""
        return self.error_obj
    
    def set_error(self, error: Any) -> None:
        """Set error object."""
        self.error_obj = error


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MQTT CONSUMER WRAPPER
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MqttConsumer:
    """MQTT subscriber wrapper providing consumer-like interface."""
    
    def __init__(self, broker_address: str, port: int = 1883, **kwargs):
        """
        Initialize MQTT consumer.
        
        Args:
            broker_address: MQTT broker address
            port: MQTT broker port (default: 1883)
            **kwargs: Additional paho-mqtt client options
        """
        self.broker_address = broker_address
        self.port = port
        self.client = mqtt.Client()
        self.subscribed_topics = []
        self.message_queue = Queue()  # Thread-safe queue for messages
        self.connected_event = Event()
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Apply additional options
        for key, value in kwargs.items():
            self._set_client_option(key, value)
        
        # Connect to broker
        self._connect()
    
    def _set_client_option(self, key: str, value: Any) -> None:
        """Set paho-mqtt client option."""
        try:
            if hasattr(self.client, key):
                setattr(self.client, key, value)
        except Exception as e:
            logger.warning("Failed to set client option %s: %s", key, e)
    
    def _connect(self) -> None:
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker_address, self.port, keepalive=60)
            self.client.loop_start()
            # Wait for connection to establish
            self.connected_event.wait(timeout=5)
            logger.debug("Connected to MQTT broker: %s:%d", self.broker_address, self.port)
        except Exception as e:
            logger.error("Failed to connect to MQTT broker: %s", e)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker."""
        if rc == 0:
            logger.debug("MQTT client connected successfully")
            self.connected_event.set()
        else:
            logger.error("Failed to connect to MQTT broker, return code: %d", rc)
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a PUBLISH message is received from the broker."""
        mqtt_message = MqttMessage(msg.topic, msg.payload, msg.qos)
        self.message_queue.put(mqtt_message)
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker."""
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker, return code: %d", rc)
        self.connected_event.clear()
    
    def subscribe(self, topics: list) -> None:
        """
        Subscribe to topics.
        
        Args:
            topics: List of topic names to subscribe to
        """
        if isinstance(topics, str):
            topics = [topics]
        
        for topic in topics:
            try:
                self.client.subscribe(topic)
                self.subscribed_topics.append(topic)
                logger.debug("Subscribed to topic: %s", topic)
            except Exception as e:
                logger.error("Failed to subscribe to topic %s: %s", topic, e)
    
    def poll(self, timeout: float = 1.0) -> Optional[MqttMessage]:
        """
        Poll for messages.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            MqttMessage if available, None otherwise
        """
        try:
            # Try to get a message from the queue with timeout
            return self.message_queue.get(timeout=timeout)
        except:
            # Queue is empty or timeout occurred
            return None
    
    def close(self) -> None:
        """Close the consumer connection."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.debug("MQTT consumer closed")
        except Exception as e:
            logger.error("Error closing MQTT consumer: %s", e)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MQTT PRODUCER WRAPPER
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MqttProducer:
    """MQTT publisher wrapper providing producer-like interface."""
    
    def __init__(self, broker_address: str, port: int = 1883, **kwargs):
        """
        Initialize MQTT producer.
        
        Args:
            broker_address: MQTT broker address
            port: MQTT broker port (default: 1883)
            **kwargs: Additional paho-mqtt client options
        """
        self.broker_address = broker_address
        self.port = port
        self.client = mqtt.Client()
        self.connected_event = Event()
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        # Apply additional options
        for key, value in kwargs.items():
            self._set_client_option(key, value)
        
        # Connect to broker
        self._connect()
    
    def _set_client_option(self, key: str, value: Any) -> None:
        """Set paho-mqtt client option."""
        try:
            if hasattr(self.client, key):
                setattr(self.client, key, value)
        except Exception as e:
            logger.warning("Failed to set client option %s: %s", key, e)
    
    def _connect(self) -> None:
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker_address, self.port, keepalive=60)
            self.client.loop_start()
            # Wait for connection to establish
            self.connected_event.wait(timeout=5)
            logger.debug("Connected to MQTT broker: %s:%d", self.broker_address, self.port)
        except Exception as e:
            logger.error("Failed to connect to MQTT broker: %s", e)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker."""
        if rc == 0:
            logger.debug("MQTT producer connected successfully")
            self.connected_event.set()
        else:
            logger.error("Failed to connect to MQTT broker, return code: %d", rc)
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker."""
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker, return code: %d", rc)
        self.connected_event.clear()
    
    def produce(self, topic: str, value: bytes, key: str = None) -> None:
        """
        Publish a message.
        
        Args:
            topic: Topic name
            value: Message payload as bytes
            key: Optional key (not used in MQTT, for interface compatibility)
        """
        try:
            self.client.publish(topic, value, qos=1)
            logger.debug("Published message to topic: %s (size=%d bytes)", topic, len(value))
        except Exception as e:
            logger.error("Failed to publish to topic %s: %s", topic, e)
    
    def flush(self, timeout: float = None) -> None:
        """
        Flush any pending messages.
        
        Args:
            timeout: Timeout in seconds
        """
        try:
            # In paho-mqtt, messages are automatically sent
            # This is a no-op for interface compatibility
            if timeout:
                time.sleep(min(timeout, 0.1))
        except Exception as e:
            logger.error("Error flushing MQTT producer: %s", e)
    
    def close(self) -> None:
        """Close the producer connection."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.debug("MQTT producer closed")
        except Exception as e:
            logger.error("Error closing MQTT producer: %s", e)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MQTT ADAPTER IMPLEMENTATION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MqttAdapter(BrokerAdapter):
    """
    MQTT-specific implementation of BrokerAdapter.
    
    Handles creation and configuration of MQTT publisher/subscriber instances
    for DEVS simulation distribution using MQTT as the message broker.
    """

    # Default MQTT configuration
    DEFAULT_CONSUMER_CONFIG = {
        "qos": 1,
        "keepalive": 60,
    }

    DEFAULT_PRODUCER_CONFIG = {
        "qos": 1,
        "keepalive": 60,
    }

    def __init__(self, broker_address: str, port: int = 1883, **kwargs):
        """
        Initialize MQTT adapter.
        
        Args:
            broker_address: MQTT broker address (e.g., "localhost" or "mqtt.example.com")
            port: MQTT broker port (default: 1883 for unencrypted, 8883 for TLS)
            **kwargs: Additional configuration options
            
        Raises:
            ImportError: If paho-mqtt is not installed
            ValueError: If broker_address is invalid
        """
        if not MQTT_AVAILABLE:
            raise ImportError(
                "MQTT adapter requires 'paho-mqtt' library. "
                "Install with: pip install paho-mqtt"
            )

        if not broker_address or not isinstance(broker_address, str):
            raise ValueError("broker_address must be a non-empty string")

        self.broker_address = broker_address
        self.port = port
        self.additional_config = kwargs
        logger.info("Initialized MQTT adapter with broker: %s:%d", broker_address, port)

    def create_consumer(self, config: Optional[Dict[str, Any]] = None) -> MqttConsumer:
        """
        Create an MQTT consumer instance.
        
        Args:
            config: Consumer configuration dictionary. If None, uses defaults.
            
        Returns:
            Configured MqttConsumer instance
            
        Raises:
            Exception: If consumer creation fails
        """
        if config is None:
            config = {}

        # Merge default + provided + additional config
        full_config = {
            **self.DEFAULT_CONSUMER_CONFIG,
            **self.additional_config,
            **config,
        }

        logger.debug("Creating MQTT consumer with config: %s", full_config)
        return MqttConsumer(self.broker_address, self.port, **full_config)

    def create_producer(self, config: Optional[Dict[str, Any]] = None) -> MqttProducer:
        """
        Create an MQTT producer instance.
        
        Args:
            config: Producer configuration dictionary. If None, uses defaults.
            
        Returns:
            Configured MqttProducer instance
            
        Raises:
            Exception: If producer creation fails
        """
        if config is None:
            config = {}

        # Merge default + provided + additional config
        full_config = {
            **self.DEFAULT_PRODUCER_CONFIG,
            **self.additional_config,
            **config,
        }

        logger.debug("Creating MQTT producer with config: %s", full_config)
        return MqttProducer(self.broker_address, self.port, **full_config)

    def extract_message_value(self, message: Any) -> bytes:
        """
        Extract the value from an MQTT message.
        
        Args:
            message: MqttMessage object
            
        Returns:
            Message value as bytes
        """
        if message is None:
            return None
        return message.value()

    def get_topic(self, message: Any) -> str:
        """
        Get the topic from an MQTT message.
        
        Args:
            message: MqttMessage object
            
        Returns:
            Topic name as string
        """
        if message is None:
            return None
        return message.topic()

    def has_error(self, message: Any) -> bool:
        """
        Check if an MQTT message contains an error.
        
        Args:
            message: MqttMessage object
            
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
        return "mqtt"

    def get_default_consumer_config(self) -> Dict[str, Any]:
        """Get default consumer configuration for this broker."""
        return self.DEFAULT_CONSUMER_CONFIG.copy()

    def get_default_producer_config(self) -> Dict[str, Any]:
        """Get default producer configuration for this broker."""
        return self.DEFAULT_PRODUCER_CONFIG.copy()

    def validate_connection(self) -> bool:
        """
        Validate connection to MQTT broker.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            consumer = self.create_consumer()
            time.sleep(0.5)  # Give time for connection
            consumer.close()
            logger.info("MQTT connection validation successful")
            return True
        except Exception as e:
            logger.error("MQTT connection validation failed: %s", e)
            return False


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MQTT CONFIGURATION HELPERS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MqttConfig:
    """Helper class for MQTT configuration."""

    @staticmethod
    def create_adapter(
        broker_address: str = "localhost",
        port: int = 1883,
        **kwargs
    ) -> MqttAdapter:
        """
        Create an MqttAdapter with common defaults.
        
        Args:
            broker_address: MQTT broker address
            port: MQTT broker port
            **kwargs: Additional configuration
            
        Returns:
            Configured MqttAdapter instance
        """
        return MqttAdapter(broker_address, port, **kwargs)

    @staticmethod
    def create_local_adapter() -> MqttAdapter:
        """Create adapter for local MQTT (localhost:1883)."""
        return MqttAdapter("localhost", 1883)

    @staticmethod
    def create_docker_adapter(container_name: str = "mosquitto") -> MqttAdapter:
        """
        Create adapter for Docker MQTT container.
        
        Args:
            container_name: Docker container name (default: "mosquitto")
            
        Returns:
            Configured MqttAdapter instance
        """
        return MqttAdapter(container_name, 1883)

    @staticmethod
    def get_tls_config(
        ca_certs: str = None,
        certfile: str = None,
        keyfile: str = None,
        cert_reqs: int = None,
        tls_version: int = None,
        ciphers: str = None,
    ) -> Dict[str, Any]:
        """
        Get MQTT TLS configuration.
        
        Args:
            ca_certs: Path to CA certificate file
            certfile: Path to client certificate file
            keyfile: Path to client key file
            cert_reqs: Certificate requirements (from ssl module)
            tls_version: TLS version (from ssl module)
            ciphers: Cipher suite
            
        Returns:
            TLS configuration dictionary
        """
        config = {}
        
        if ca_certs:
            config["ca_certs"] = ca_certs
        if certfile:
            config["certfile"] = certfile
        if keyfile:
            config["keyfile"] = keyfile
        if cert_reqs is not None:
            config["cert_reqs"] = cert_reqs
        if tls_version is not None:
            config["tls_version"] = tls_version
        if ciphers:
            config["ciphers"] = ciphers
        
        return config

    @staticmethod
    def get_auth_config(
        username: str = None,
        password: str = None,
    ) -> Dict[str, Any]:
        """
        Get MQTT authentication configuration.
        
        Args:
            username: MQTT username
            password: MQTT password
            
        Returns:
            Authentication configuration dictionary
        """
        config = {}
        
        if username:
            config["username"] = username
        if password:
            config["password"] = password
        
        return config
