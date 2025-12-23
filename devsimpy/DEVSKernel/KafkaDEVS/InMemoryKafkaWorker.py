# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# InMemoryKafkaWorker.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/22/25
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

# ------------------------------------------------------------------
#  Kafka-specific implementation
# ------------------------------------------------------------------

import logging
import time

from DEVSKernel.KafkaDEVS.InMemoryMessagingWorker import InMemoryMessagingWorker, MessageAdapter, MessageConsumer, MessageProducer
from typing import Dict, Any

from DEVSKernel.KafkaDEVS.logconfig import LOGGING_LEVEL

logger = logging.getLogger("DEVSKernel.KafkaDEVS.InMemoryKafkaWorker")
logger.setLevel(LOGGING_LEVEL)

try:
	from confluent_kafka import Producer, Consumer
except Exception:
	Producer = None
	Consumer = None

class KafkaMessageAdapter(MessageAdapter):
    """Kafka-specific implementation of MessageAdapter"""
    
    def create_consumer(self, config: Dict[str, Any]) -> MessageConsumer:
        """Create a Kafka consumer"""
        return Consumer(config)
    
    def create_producer(self, config: Dict[str, Any]) -> MessageProducer:
        """Create a Kafka producer"""
        return Producer(config)
    
    def extract_message_value(self, message: Any) -> bytes:
        """Extract value from Kafka message"""
        return message.value()
    
    def has_error(self, message: Any) -> bool:
        """Check if Kafka message has an error"""
        return message.error() is not None
    
    def get_topic(self, message: Any) -> str:
        """Get topic from Kafka message"""
        return message.topic()

class InMemoryKafkaWorker(InMemoryMessagingWorker):
    """
    Kafka-specific worker thread that manages one atomic model in memory.
    This is a concrete implementation of InMemoryMessagingWorker for Kafka.
    """
    
    def __init__(
        self, 
        model_name: str, 
        aDEVS, 
        bootstrap_server: str, 
        in_topic: str = None, 
        out_topic: str = None
    ):
        """
        Initialize the Kafka worker.
        
        Args:
            model_name: Name of the DEVS model
            aDEVS: The atomic DEVS model instance
            bootstrap_server: Kafka bootstrap server address
            in_topic: Topic to receive messages from coordinator
            out_topic: Topic to send messages to coordinator
        """
        group_id = f"worker-thread-{aDEVS.myID}-{int(time.time() * 1000)}"
        
        consumer_config = {
            "bootstrap.servers": bootstrap_server,
            "group.id": group_id,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        }
        
        producer_config = {
            "bootstrap.servers": bootstrap_server
        }
        
        adapter = KafkaMessageAdapter()
        
        super().__init__(
            model_name=model_name,
            aDEVS=aDEVS,
            adapter=adapter,
            consumer_config=consumer_config,
            producer_config=producer_config,
            in_topic=in_topic,
            out_topic=out_topic
        )