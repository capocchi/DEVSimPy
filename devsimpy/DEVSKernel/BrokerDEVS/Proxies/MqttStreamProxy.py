# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# MqttStreamProxy.py ---
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
# MQTT producer proxy for sending messages to topics.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise ImportError("paho-mqtt package required. Install with: pip install paho-mqtt")

logger = logging.getLogger(__name__)


class MqttStreamProxy:
    """
    MQTT producer proxy for sending messages to topics.
    
    Wraps MQTT Publisher with connection management and message handling.
    """

    def __init__(
        self,
        broker_address: str = "localhost",
        broker_port: int = 1883,
        client_id: str = None,
        wire_adapter=None,
        qos: int = 1,
        keepalive: int = 60,
    ):
        """
        Initialize MQTT stream proxy (producer).
        
        Args:
            broker_address: MQTT broker address
            broker_port: MQTT broker port
            client_id: MQTT client ID
            wire_adapter: Message serialization adapter
            qos: MQTT QoS level
            keepalive: MQTT keepalive interval
        """
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.qos = qos
        self.keepalive = keepalive
        self.wire_adapter = wire_adapter

        # Create MQTT client - compatible with paho-mqtt 2.x
        client_id_str = client_id or f"producer-{int(time.time() * 1000)}"
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

        self._connected = False
        self._connection_timeout = 10.0

        # Connect to broker
        self._connect()

    def _on_connect(self, client, userdata, flags=None, rc=None, properties=None):
        """Called when connected (compatible with VERSION1 and VERSION2)"""
        # VERSION2 passes reason_code as 4th arg, VERSION1 passes rc as 3rd arg
        reason_code = rc if rc is not None else flags
        
        if reason_code == 0:
            logger.info("MqttStreamProxy: Connected to MQTT broker")
            self._connected = True
        else:
            logger.error("MqttStreamProxy: Connection failed with code %d: %s", reason_code, self._get_error_message(reason_code))

    def _on_disconnect(self, client, userdata, flags=None, rc=None, properties=None):
        """Called when disconnected (compatible with VERSION1 and VERSION2)"""
        # VERSION2 passes reason_code as 4th arg, VERSION1 passes rc as 3rd arg
        reason_code = rc if rc is not None else flags
        
        self._connected = False
        if reason_code != 0:
            logger.warning("MqttStreamProxy: Unexpected disconnection (code: %d): %s", reason_code, self._get_error_message(reason_code))
    
    @staticmethod
    def _get_error_message(rc):
        """Get human-readable MQTT error message"""
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
        return error_messages.get(rc, f"Unknown error code {rc}")

    def _connect(self):
        """Connect to MQTT broker"""
        logger.info(
            "MqttStreamProxy: Connecting to %s:%d",
            self.broker_address, self.broker_port
        )
        
        try:
            # Set socket options for better connection handling
            self.client.socket_options = None
            
            self.client.connect(
                self.broker_address,
                self.broker_port,
                keepalive=self.keepalive
            )
            self.client.loop_start()

            # Wait for connection with detailed logging
            start_time = time.time()
            while not self._connected and (time.time() - start_time) < self._connection_timeout:
                time.sleep(0.1)

            if not self._connected:
                self.client.loop_stop()
                raise RuntimeError(
                    f"Failed to connect to MQTT broker at {self.broker_address}:{self.broker_port} "
                    f"(timeout after {self._connection_timeout}s)"
                )
        except RuntimeError:
            raise
        except Exception as e:
            self.client.loop_stop()
            raise RuntimeError(
                f"Error connecting to MQTT broker at {self.broker_address}:{self.broker_port}: {str(e)}"
            )

    def send_message(self, topic: str, msg) -> bool:
        """
        Send a message to a topic.
        
        Args:
            topic: MQTT topic
            msg: Message to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            logger.warning("MqttStreamProxy: Not connected, cannot send to %s", topic)
            return False

        try:
            # Serialize message
            if self.wire_adapter:
                payload = self.wire_adapter.serialize(msg)
            else:
                import pickle
                payload = pickle.dumps(msg)

            result = self.client.publish(topic, payload, qos=self.qos)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(
                    "MqttStreamProxy: Failed to publish to %s (code: %d)",
                    topic, result.rc
                )
                return False

            logger.debug("MqttStreamProxy: Sent %s to %s", type(msg).__name__, topic)
            return True

        except Exception as e:
            logger.error("MqttStreamProxy: Error sending message: %s", e)
            return False

    def close(self):
        """Close the connection"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MqttStreamProxy: Closed")
        except Exception as e:
            logger.error("MqttStreamProxy: Error closing: %s", e)
