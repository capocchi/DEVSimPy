# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# InMemoryMqttWorker.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/28/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# MQTT-specific implementation of InMemoryMessagingWorker
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time
from typing import Dict, Any, Optional

from DEVSKernel.BrokerDEVS.Workers.InMemoryMessagingWorker import InMemoryMessagingWorker, MessageAdapter, MessageConsumer, MessageProducer
from DEVSKernel.BrokerDEVS.logconfig import LOGGING_LEVEL

logger = logging.getLogger("DEVSKernel.BrokerDEVS.InMemoryMqttWorker")
logger.setLevel(LOGGING_LEVEL)

try:
	import paho.mqtt.client as mqtt
	MQTT_AVAILABLE = True
except Exception:
	MQTT_AVAILABLE = False
	logger.warning("paho-mqtt not available. Install with: pip install paho-mqtt")


class MqttMessageConsumer:
	"""MQTT consumer wrapper providing consumer-like interface."""
	
	def __init__(self, broker_address: str, port: int = 1883, **kwargs):
		"""
		Initialize MQTT consumer.
		
		Args:
			broker_address: MQTT broker address
			port: MQTT broker port (default: 1883)
			**kwargs: Additional paho-mqtt client options (client_id, username, password, etc.)
		"""
		self.broker_address = broker_address
		self.port = port
		self.client = mqtt.Client()
		self.subscribed_topics = []
		self.last_message = None
		
		# Set up callbacks
		self.client.on_connect = self._on_connect
		self.client.on_message = self._on_message
		
		# Apply additional options
		if 'client_id' in kwargs:
			self.client._client_id = kwargs['client_id']
		if 'username' in kwargs and 'password' in kwargs:
			self.client.username_pw_set(kwargs['username'], kwargs['password'])
		
		# Connect to broker
		self._connect()
	
	def _on_connect(self, client, userdata, flags, rc):
		"""Callback for when client connects to broker."""
		if rc == 0:
			logger.debug("MQTT consumer connected successfully")
		else:
			logger.error("Failed to connect to MQTT broker, return code: %d", rc)
	
	def _on_message(self, client, userdata, msg):
		"""Callback for when a PUBLISH message is received from the broker."""
		self.last_message = msg
	
	def _connect(self) -> None:
		"""Connect to MQTT broker."""
		try:
			self.client.connect(self.broker_address, self.port, keepalive=60)
			self.client.loop_start()
			logger.debug("MQTT consumer connected to broker: %s:%d", self.broker_address, self.port)
		except Exception as e:
			logger.error("Failed to connect to MQTT broker: %s", e)
	
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
				self.client.subscribe(topic, qos=1)
				self.subscribed_topics.append(topic)
				logger.debug("Subscribed to topic: %s", topic)
			except Exception as e:
				logger.error("Failed to subscribe to topic %s: %s", topic, e)
	
	def poll(self, timeout: float = 1.0) -> Optional[Any]:
		"""
		Poll for messages.
		
		Args:
			timeout: Timeout in seconds
			
		Returns:
			Message if available, None otherwise
		"""
		if self.last_message is not None:
			msg = self.last_message
			self.last_message = None
			return msg
		
		# Wait for a message
		time.sleep(min(timeout, 0.1))
		return self.last_message
	
	def close(self) -> None:
		"""Close the consumer connection."""
		try:
			self.client.loop_stop()
			self.client.disconnect()
			logger.debug("MQTT consumer closed")
		except Exception as e:
			logger.error("Error closing MQTT consumer: %s", e)


class MqttMessageProducer:
	"""MQTT producer wrapper providing producer-like interface."""
	
	def __init__(self, broker_address: str, port: int = 1883, **kwargs):
		"""
		Initialize MQTT producer.
		
		Args:
			broker_address: MQTT broker address
			port: MQTT broker port (default: 1883)
			**kwargs: Additional paho-mqtt client options (client_id, username, password, etc.)
		"""
		self.broker_address = broker_address
		self.port = port
		self.client = mqtt.Client()
		
		# Set up callbacks
		self.client.on_connect = self._on_connect
		
		# Apply additional options
		if 'client_id' in kwargs:
			self.client._client_id = kwargs['client_id']
		if 'username' in kwargs and 'password' in kwargs:
			self.client.username_pw_set(kwargs['username'], kwargs['password'])
		
		# Connect to broker
		self._connect()
	
	def _on_connect(self, client, userdata, flags, rc):
		"""Callback for when client connects to broker."""
		if rc == 0:
			logger.debug("MQTT producer connected successfully")
		else:
			logger.error("Failed to connect to MQTT broker, return code: %d", rc)
	
	def _connect(self) -> None:
		"""Connect to MQTT broker."""
		try:
			self.client.connect(self.broker_address, self.port, keepalive=60)
			self.client.loop_start()
			logger.debug("MQTT producer connected to broker: %s:%d", self.broker_address, self.port)
		except Exception as e:
			logger.error("Failed to connect to MQTT broker: %s", e)
	
	def produce(self, topic: str, value: bytes, **kwargs) -> None:
		"""
		Produce a message to a topic.
		
		Args:
			topic: Topic name
			value: Message payload
			**kwargs: Additional options (ignored for MQTT)
		"""
		try:
			self.client.publish(topic, payload=value, qos=1)
			logger.debug("Published message to topic: %s (size=%d bytes)", topic, len(value))
		except Exception as e:
			logger.error("Failed to publish message: %s", e)
	
	def flush(self, timeout: Optional[float] = None) -> None:
		"""Flush pending messages (no-op for MQTT)."""
		pass
	
	def close(self) -> None:
		"""Close the producer connection."""
		try:
			self.client.loop_stop()
			self.client.disconnect()
			logger.debug("MQTT producer closed")
		except Exception as e:
			logger.error("Error closing MQTT producer: %s", e)


class MqttMessageAdapter(MessageAdapter):
	"""MQTT-specific implementation of MessageAdapter"""
	
	def __init__(self, broker_address: str = "localhost", port: int = 1883, **kwargs):
		"""
		Initialize MQTT adapter.
		
		Args:
			broker_address: MQTT broker address
			port: MQTT broker port
			**kwargs: Additional MQTT options
		"""
		self.broker_address = broker_address
		self.port = port
		self.mqtt_options = kwargs
	
	def create_consumer(self, config: Dict[str, Any]) -> MessageConsumer:
		"""Create an MQTT consumer"""
		# Extract broker info from config if provided, otherwise use adapter defaults
		broker = config.get('broker_address', self.broker_address)
		port = config.get('port', self.port)
		
		# Extract MQTT options
		mqtt_opts = {k: v for k, v in config.items() if k not in ['broker_address', 'port']}
		mqtt_opts.update(self.mqtt_options)
		
		return MqttMessageConsumer(broker, port, **mqtt_opts)
	
	def create_producer(self, config: Dict[str, Any]) -> MessageProducer:
		"""Create an MQTT producer"""
		# Extract broker info from config if provided, otherwise use adapter defaults
		broker = config.get('broker_address', self.broker_address)
		port = config.get('port', self.port)
		
		# Extract MQTT options
		mqtt_opts = {k: v for k, v in config.items() if k not in ['broker_address', 'port']}
		mqtt_opts.update(self.mqtt_options)
		
		return MqttMessageProducer(broker, port, **mqtt_opts)
	
	def extract_message_value(self, message: Any) -> bytes:
		"""Extract value from MQTT message"""
		return message.payload
	
	def has_error(self, message: Any) -> bool:
		"""MQTT messages don't have errors in the same way (this is a no-op)"""
		return False
	
	def get_topic(self, message: Any) -> str:
		"""Get topic from MQTT message"""
		return message.topic


class InMemoryMqttWorker(InMemoryMessagingWorker):
	"""
	MQTT-specific worker thread that manages one atomic model in memory.
	This is a concrete implementation of InMemoryMessagingWorker for MQTT.
	"""
	
	def __init__(
		self, 
		model_name: str, 
		aDEVS, 
		broker_host: str = "localhost",
		broker_port: int = 1883,
		in_topic: str = None, 
		out_topic: str = None,
		client_id: str = None,
		username: str = None,
		password: str = None
	):
		"""
		Initialize the MQTT worker.
		
		Args:
			model_name: Name of the DEVS model
			aDEVS: The atomic DEVS model instance
			broker_host: MQTT broker hostname (default: localhost)
			broker_port: MQTT broker port (default: 1883)
			in_topic: Topic to receive messages from coordinator
			out_topic: Topic to send messages to coordinator
			client_id: MQTT client ID (default: auto-generated)
			username: MQTT username for authentication (optional)
			password: MQTT password for authentication (optional)
		"""
		if client_id is None:
			client_id = f"worker-{model_name}-{aDEVS.myID}-{int(time.time() * 1000)}"
		
		consumer_config = {
			"broker_address": broker_host,
			"port": broker_port,
			"client_id": client_id,
		}
		
		producer_config = {
			"broker_address": broker_host,
			"port": broker_port,
			"client_id": f"{client_id}-producer",
		}
		
		# Add authentication if provided
		if username is not None:
			consumer_config["username"] = username
			producer_config["username"] = username
		if password is not None:
			consumer_config["password"] = password
			producer_config["password"] = password
		
		adapter = MqttMessageAdapter(broker_host, broker_port)
		
		super().__init__(
			model_name=model_name,
			aDEVS=aDEVS,
			adapter=adapter,
			consumer_config=consumer_config,
			producer_config=producer_config,
			in_topic=in_topic,
			out_topic=out_topic
		)
