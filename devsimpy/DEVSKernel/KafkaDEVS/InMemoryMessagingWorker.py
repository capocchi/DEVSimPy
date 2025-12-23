# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# InMemoryMessagingWorker.py ---
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

import threading
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Protocol

from DEVSKernel.KafkaDEVS.logconfig import LOGGING_LEVEL, worker_kafka_logger

logger = logging.getLogger("DEVSKernel.KafkaDEVS.InMemoryMessagingWorker")
logger.setLevel(LOGGING_LEVEL)


class MessageConsumer(Protocol):
    """Protocol for message consumer (Kafka, RabbitMQ, Redis, etc.)"""
    
    def subscribe(self, topics: list) -> None:
        """Subscribe to topics/channels"""
        ...
    
    def poll(self, timeout: float) -> Any:
        """Poll for messages with timeout"""
        ...
    
    def close(self) -> None:
        """Close the consumer connection"""
        ...


class MessageProducer(Protocol):
    """Protocol for message producer (Kafka, RabbitMQ, Redis, etc.)"""
    
    def produce(self, topic: str, value: bytes, **kwargs) -> None:
        """Produce a message to a topic/channel"""
        ...
    
    def flush(self) -> None:
        """Flush pending messages"""
        ...


class MessageAdapter(ABC):
    """Abstract adapter for different messaging systems"""
    
    @abstractmethod
    def create_consumer(self, config: Dict[str, Any]) -> MessageConsumer:
        """Create a consumer instance"""
        ...
    
    @abstractmethod
    def create_producer(self, config: Dict[str, Any]) -> MessageProducer:
        """Create a producer instance"""
        ...
    
    @abstractmethod
    def extract_message_value(self, message: Any) -> bytes:
        """Extract message value from the messaging system's message format"""
        ...
    
    @abstractmethod
    def has_error(self, message: Any) -> bool:
        """Check if message has an error"""
        ...
    
    @abstractmethod
    def get_topic(self, message: Any) -> str:
        """Get topic/channel name from message"""
        ...


class InMemoryMessagingWorker(threading.Thread, ABC):
    """
    Generic worker thread that manages one atomic model in memory.
    Can work with any messaging system (Kafka, RabbitMQ, Redis, etc.)
    through the MessageAdapter interface.
    """

    def __init__(
        self, 
        model_name: str, 
        aDEVS, 
        adapter: MessageAdapter,
        consumer_config: Dict[str, Any],
        producer_config: Dict[str, Any],
        in_topic: str = None, 
        out_topic: str = None
    ):
        """
        Initialize the messaging worker.
        
        Args:
            model_name: Name of the DEVS model
            aDEVS: The atomic DEVS model instance
            adapter: Messaging system adapter (Kafka, RabbitMQ, etc.)
            consumer_config: Configuration for the consumer
            producer_config: Configuration for the producer
            in_topic: Topic/channel to receive messages from coordinator
            out_topic: Topic/channel to send messages to coordinator
        """
        super().__init__(daemon=True)
        self.aDEVS = aDEVS
        self.model_name = model_name
        self.adapter = adapter
        self.running = True

        # Topics explicitly provided by the strategy
        self.in_topic = in_topic
        self.out_topic = out_topic

        # Create consumer and producer using the adapter
        self.consumer = adapter.create_consumer(consumer_config)
        self.consumer.subscribe([self.in_topic])

        self.producer = adapter.create_producer(producer_config)

        logger.info(
            "  [Thread-%s] Created for model %s (in topic=%s, out topic=%s)",
            self.aDEVS.myID, self.model_name, self.in_topic, self.out_topic
        )
    
    def get_model(self):
        """Returns the atomic DEVS model managed by this worker."""
        return self.aDEVS
    
    def get_model_label(self):
        """Returns the model name."""
        return self.model_name
    
    def get_model_time_next(self):
        """Returns the next scheduled time for the model."""
        return self.aDEVS.timeNext
    
    # ------------------------------------------------------------------
    #  DEVS message translation -> model calls
    # ------------------------------------------------------------------

    def do_initialize(self, t: float):
        """Initialize the atomic model before starting the loop."""
        self.aDEVS.sigma = 0.0
        self.aDEVS.timeLast = 0.0
        self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
        self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance
    
        if self.aDEVS.myTimeAdvance != float("inf"): 
            self.aDEVS.myTimeAdvance += t

    def do_external_transition(self, t, msg):
        """Perform an external transition on the atomic model."""
        
        port_inputs = {}

        # Build dict {port_obj -> Message(value, time)}
        from DomainInterface.Object import Message
        for pv in msg.portValueList:
            # pv.portIdentifier must match the input port name
            for iport in self.aDEVS.IPorts:
                if iport.name == pv.portIdentifier:
                    m = Message(pv.value, t)
                    port_inputs[iport] = m
                    break
        
        self.aDEVS.myInput = port_inputs

        # Update elapsed time. This is necessary for the call to the external
        # transition function, which is used to update the DEVS' state.
        self.aDEVS.elapsed = t - self.aDEVS.timeLast

        self.aDEVS.extTransition()

        # Update time variables
        self.aDEVS.timeLast = t
        self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
        self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance
        if self.aDEVS.myTimeAdvance != float("inf"): 
            self.aDEVS.myTimeAdvance += t
        self.aDEVS.elapsed = 0

    def do_internal_transition(self, t: float):
        """Perform an internal transition on the atomic model."""
        
        time_last = self.aDEVS.timeLast
        self.aDEVS.elapsed = t - time_last

        self.aDEVS.intTransition()

        self.aDEVS.timeLast = t
        self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
        self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance
        if self.aDEVS.myTimeAdvance != float('inf'): 
            self.aDEVS.myTimeAdvance += t
        self.aDEVS.elapsed = 0

    def do_output_function(self):
        """Call outputFnc() on the atomic model and return the outputs."""
        self.aDEVS.outputFnc()

    @abstractmethod
    def _process_standard(self, data: Dict[str, Any]) -> None:
        """
        Process standard DEVS message format.
        Must be implemented by subclasses.
        
        Args:
            data: Parsed JSON message data
        """
        ...

    # ------------------------------------------------------------------
    #  Main loop
    # ------------------------------------------------------------------

    def run(self):
        """Main worker loop that processes incoming messages."""
        logger.info(f"  [Thread-{self.aDEVS.myID}] Started")

        while self.running:
            msg = self.consumer.poll(timeout=0.5)
            if msg is None or self.adapter.has_error(msg):
                continue

            try:
                raw_value = self.adapter.extract_message_value(msg)
                raw = raw_value.decode("utf-8")
                data = json.loads(raw)

                topic = self.adapter.get_topic(msg)
                worker_kafka_logger.debug(
                    f"[Thread-{self.aDEVS.myID}] IN: topic={topic} value={raw}"
                )
                
                self._process_standard(data)

            except Exception as e:
                logger.exception(
                    "[Thread-%s] Error in run loop: %s", 
                    self.aDEVS.myID, e
                )

        self.consumer.close()
        logger.info(f"  [Thread-{self.aDEVS.myID}] Stopped")

    def stop(self):
        """Stop the worker thread."""
        self.running = False
