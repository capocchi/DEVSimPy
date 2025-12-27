# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# MqttReceiverProxy.py ---
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
# MQTT consumer proxy for receiving messages from topics.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time
import threading
from typing import Dict, List, Optional
from collections import defaultdict

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise ImportError("paho-mqtt package required. Install with: pip install paho-mqtt")

logger = logging.getLogger(__name__)


class MqttReceiverProxy:
    """
    MQTT consumer proxy for receiving messages from topics.
    
    Wraps MQTT Subscriber with message buffering and collection.
    """

    def __init__(
        self,
        broker_address: str = "localhost",
        broker_port: int = 1883,
        client_id: str = None,
        wire_adapter=None,
        qos: int = 1,
        keepalive: int = 60,
        username: str = None,
        password: str = None,
    ):
        """
        Initialize MQTT receiver proxy (consumer).
        
        Args:
            broker_address: MQTT broker address
            broker_port: MQTT broker port
            client_id: MQTT client ID
            wire_adapter: Message deserialization adapter
            qos: MQTT QoS level
            keepalive: MQTT keepalive interval
            username: MQTT username (optional)
            password: MQTT password (optional)
        """
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.qos = qos
        self.keepalive = keepalive
        self.wire_adapter = wire_adapter
        self.username = username
        self.password = password

        # Create MQTT client - compatible with paho-mqtt 2.x
        client_id_str = client_id or f"receiver-{int(time.time() * 1000)}"
        try:
            # Try paho-mqtt 2.x with VERSION2 API (preferred)
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id_str)
        except (TypeError, AttributeError):
            try:
                # Fallback to VERSION1 for paho-mqtt 2.x
                self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id_str)
            except (TypeError, AttributeError):
                # Fallback to older paho-mqtt 1.x API
                self.client = mqtt.Client(client_id=client_id_str, protocol=mqtt.MQTTv311)
        
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Set credentials if provided
        if self.username:
            self.client.username_pw_set(self.username, self.password or "")

        # Message buffer: topic -> list of messages
        self._message_buffer = defaultdict(list)
        self._buffer_lock = threading.Lock()
        self._subscribed_topics = set()

        self._connected = False
        self._connection_timeout = 10.0

        # Connect to broker
        self._connect()

    def _on_connect(self, client, userdata, flags=None, rc=None, properties=None):
        """Called when connected (compatible with VERSION1 and VERSION2)"""
        # VERSION2 passes reason_code as 4th arg, VERSION1 passes rc as 3rd arg
        reason_code = rc if rc is not None else flags
        
        # Convert ReasonCode to int for logging compatibility
        reason_code_int = reason_code.value if hasattr(reason_code, 'value') else (int(reason_code) if reason_code is not None else 0)
        
        if reason_code_int == 0:
            logger.info("MqttReceiverProxy: Connected to MQTT broker")
            self._connected = True
            # Resubscribe to topics if we have any
            for topic in self._subscribed_topics:
                self.client.subscribe(topic, qos=self.qos)
        else:
            logger.error("MqttReceiverProxy: Connection failed with code %d: %s", reason_code_int, self._get_error_message(reason_code))

    def _on_disconnect(self, client, userdata, flags=None, rc=None, properties=None):
        """Called when disconnected (compatible with VERSION1 and VERSION2)"""
        # VERSION2 passes reason_code as 4th arg, VERSION1 passes rc as 3rd arg
        reason_code = rc if rc is not None else flags
        
        # Convert ReasonCode to int for logging compatibility
        reason_code_int = reason_code.value if hasattr(reason_code, 'value') else (int(reason_code) if reason_code is not None else 0)
        
        self._connected = False
        if reason_code_int != 0:
            logger.warning("MqttReceiverProxy: Unexpected disconnection (code: %d): %s", reason_code_int, self._get_error_message(reason_code))
    
    @staticmethod
    def _get_error_message(rc):
        """Get human-readable MQTT error message"""
        # Convert ReasonCode object to int for paho-mqtt 2.x compatibility
        if hasattr(rc, 'value'):
            rc_int = rc.value
        else:
            rc_int = int(rc)
        
        error_messages = {
            0: "Connection successful",
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorised",
            6: "Currently unused",
            7: "Connection refused - bad protocol version or broker rejected",
        }
        return error_messages.get(rc_int, f"Unknown error code {rc_int}")
        

    def _on_message(self, client, userdata, msg):
        """Called when message received"""
        try:
            # Deserialize message
            if self.wire_adapter:
                deserialized = self.wire_adapter.deserialize(msg.payload)
            else:
                import pickle
                deserialized = pickle.loads(msg.payload)

            # Add to buffer
            with self._buffer_lock:
                self._message_buffer[msg.topic].append(deserialized)

            logger.debug(
                "MqttReceiverProxy: Received %s on %s",
                type(deserialized).__name__, msg.topic
            )

        except Exception as e:
            logger.error(
                "MqttReceiverProxy: Error deserializing message: %s", e
            )

    def _connect(self):
        """Connect to MQTT broker"""
        logger.info(
            "MqttReceiverProxy: Connecting to %s:%d",
            self.broker_address, self.broker_port
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
                f"Failed to connect to MQTT broker at {self.broker_address}:{self.broker_port}"
            )

    def subscribe(self, topics: List[str]):
        """
        Subscribe to MQTT topics.
        
        Args:
            topics: List of MQTT topics to subscribe to
        """
        for topic in topics:
            self._subscribed_topics.add(topic)
            self.client.subscribe(topic, qos=self.qos)
            logger.info("MqttReceiverProxy: Subscribed to %s", topic)

    def unsubscribe(self, topics: List[str]):
        """
        Unsubscribe from MQTT topics.
        
        Args:
            topics: List of MQTT topics to unsubscribe from
        """
        for topic in topics:
            self._subscribed_topics.discard(topic)
            self.client.unsubscribe(topic)
            logger.info("MqttReceiverProxy: Unsubscribed from %s", topic)

    def receive_messages(
        self,
        models: List,
        timeout: float = 30.0,
    ) -> Dict:
        """
        Wait for messages from all models.
        
        Args:
            models: List of models to wait responses from
            timeout: How long to wait (seconds)
            
        Returns:
            Dictionary {model: message} of received messages
        """
        logger.debug("MqttReceiverProxy: Waiting for %d messages (timeout=%.1f)", len(models), timeout)

        start_time = time.time()
        results = {}

        while len(results) < len(models) and (time.time() - start_time) < timeout:
            # Check all topics for messages
            with self._buffer_lock:
                for topic, messages in list(self._message_buffer.items()):
                    if messages and len(results) < len(models):
                        msg = messages.pop(0)

                        # Try to match message to a model
                        # (simplified: in real code would need topic→model mapping)
                        for model in models:
                            if model not in results:
                                results[model] = msg
                                break

            if len(results) < len(models):
                time.sleep(0.1)

        if len(results) < len(models):
            logger.warning(
                "MqttReceiverProxy: Timeout - got %d/%d messages",
                len(results), len(models)
            )

        return results

    def purge_old_messages(self, max_seconds: float = 2.0) -> int:
        """
        Purge old messages from buffer.
        
        Args:
            max_seconds: Remove messages older than this (not used for MQTT)
            
        Returns:
            Number of messages purged
        """
        with self._buffer_lock:
            total = sum(len(msgs) for msgs in self._message_buffer.values())
            self._message_buffer.clear()

        logger.info("MqttReceiverProxy: Purged %d old messages", total)
        return total

    def close(self):
        """Close the connection"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MqttReceiverProxy: Closed")
        except Exception as e:
            logger.error("MqttReceiverProxy: Error closing: %s", e)
