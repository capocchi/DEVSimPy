# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Proxies.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/21/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import time
from typing import Protocol, Dict, Any, List
import json

from confluent_kafka import Producer, Consumer
from DEVSKernel.KafkaDEVS.logconfig import coord_kafka_logger
from Patterns.Proxy import AbstractStreamProxy, AbstractReceiverProxy

class BaseMessage(Protocol):
    """Protocol for any message type with serialization support"""
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        ...

    def from_dict(d: Dict[str, Any]) -> "BaseMessage":
        """Create message from dictionary"""
        ...

class StandardWireAdapter:
    """
    Msg adaptator.
    """

    @staticmethod
    def to_wire(msg: BaseMessage) -> Dict[str, Any]:
        """
        Transform BaseMessage to dict in order to be sended on Broker.
        """
        ...

    @staticmethod
    def from_wire(d: Dict[str, Any]) -> BaseMessage:
        """
        Transform  a dict in BaseMessage.
        """
        ...
    
class KafkaStreamProxy(AbstractStreamProxy):
    """
    Concrete implementation of the sending proxy using Kafka Producer.
    Encapsulates all message sending logic to Kafka.
    """
    
    def __init__(self, bootstrap_servers: str, wire_adapter=None):
        """
        Initialize the Kafka sending proxy.
        
        Args:
            bootstrap_servers: Kafka broker address
            wire_adapter: Adapter for serialization (default: StandardWireAdapter)
        """
        self._producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "enable.idempotence": True,
            "acks": "all",
            "max.in.flight.requests.per.connection": 5,
            "retries": 10,
        })
        self.wire = wire_adapter or StandardWireAdapter
        self._logger = coord_kafka_logger
    
    def send_message(self, topic: str, msg: BaseMessage):
        """
        Send a typed DEVS message to a Kafka topic.
        
        Args:
            topic: The destination Kafka topic
            msg: The typed DEVS message to send
        """
        msg_dict = msg.to_dict()
        payload = json.dumps(msg_dict).encode("utf-8")
        
        self._producer.produce(topic, value=payload)
        self._producer.flush()
        
        self._logger.debug("OUT: topic=%s value=%s", topic, payload)
    
    def flush(self):
        """Force immediate sending of all pending messages"""
        self._producer.flush()
    
    def close(self):
        """Cleanly close the Kafka producer"""
        self._producer.flush()
        self._logger.info("KafkaStreamProxy closed")


class KafkaReceiverProxy(AbstractReceiverProxy):
    """
    Concrete implementation of the receiving proxy using Kafka Consumer.
    Encapsulates all Kafka message reception and processing logic.
    """
    
    def __init__(self, bootstrap_servers: str, group_id: str, wire_adapter=None):
        """
        Initialize the Kafka receiving proxy.
        
        Args:
            bootstrap_servers: Kafka broker address
            group_id: Consumer group identifier
            wire_adapter: Adapter for deserialization (default: StandardWireAdapter)
        """
        self._consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
            "session.timeout.ms": 30000,
            "max.poll.interval.ms": 300000,
        })
        self.wire = wire_adapter or StandardWireAdapter
        self._logger = coord_kafka_logger
        self._subscribed_topics = []
    
    def subscribe(self, topics: List[str]):
        """
        Subscribe to a list of Kafka topics.
        
        Args:
            topics: List of topic names to listen to
        """
        self._consumer.subscribe(topics)
        self._subscribed_topics = topics
        self._logger.info("Subscribed to topics: %s", topics)
    
    def receive_messages(self, pending: List, timeout: float) -> Dict:
        """
        Wait for and collect messages from specified workers.
        
        Args:
            pending: List of DEVS models from which a response is expected
            timeout: Maximum wait time in seconds
            
        Returns:
            Dictionary mapping each model to its received message
            
        Raises:
            TimeoutError: If all expected messages are not received
        """
        received = {}
        deadline = time.time() + timeout
        
        # Copy the list to avoid modifying the original
        remaining = list(pending)
        
        while remaining and time.time() < deadline:
            msg = self._consumer.poll(timeout=0.5)
            if msg is None or msg.error():
                continue
            
            try:
                data = json.loads(msg.value().decode("utf-8"))
                
                self._logger.debug(
                    "IN: topic=%s value=%s",
                    msg.topic(),
                    json.dumps(data),
                )
                
                # Deserialize the DEVS message
                devs_msg = self.wire.from_wire(data)
                model_name = data.get('sender')
                
                if not model_name:
                    self._logger.warning("Message without sender field: %s", data)
                    continue
                
                # Find and remove the corresponding model
                for i, model in enumerate(remaining):
                    if model.getBlockModel().label == model_name:
                        matched_model = remaining.pop(i)
                        received[matched_model] = devs_msg
                        break
                        
            except json.JSONDecodeError as e:
                self._logger.error("JSON decode error: %s", e)
            except Exception as e:
                self._logger.error("Error processing message: %s", e)
        
        if remaining:
            missing_labels = [m.getBlockModel().label for m in remaining]
            raise TimeoutError(
                f"Kafka timeout: missing responses from models {missing_labels}"
            )
        
        return received
    
    def purge_old_messages(self, max_seconds: float = 2.0) -> int:
        """
        Purge old messages present in the topic.
        
        Args:
            max_seconds: Maximum time to purge messages
            
        Returns:
            Number of purged messages
        """
        flushed = 0
        start_flush = time.time()
        
        self._logger.info("Purging old messages...")
        
        while time.time() - start_flush < max_seconds:
            msg = self._consumer.poll(timeout=0.1)
            if msg is None:
                break
            if not msg.error():
                flushed += 1
        
        if flushed > 0:
            self._logger.info("Flushed %s old messages", flushed)
        
        return flushed
    
    def close(self):
        """Cleanly close the Kafka consumer"""
        self._consumer.close()
        self._logger.info("KafkaReceiverProxy closed")