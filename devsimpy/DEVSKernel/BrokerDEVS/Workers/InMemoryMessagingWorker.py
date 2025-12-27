# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# InMemoryMessagingWorker.py ---
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
# Generic in-memory worker for distributed DEVS simulation.
# Works with any broker (Kafka, MQTT, RabbitMQ, etc.) via BrokerAdapter.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import threading
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Protocol, Optional

from DEVSKernel.BrokerDEVS.logconfig import LOGGING_LEVEL, worker_kafka_logger
from DEVSKernel.BrokerDEVS.Core.BrokerAdapter import BrokerAdapter
from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import BaseMessage

logger = logging.getLogger("DEVSKernel.BrokerDEVS.InMemoryMessagingWorker")
logger.setLevel(LOGGING_LEVEL)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# BROKER-AGNOSTIC MESSAGE PROTOCOLS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MessageConsumer(Protocol):
    """
    Protocol for message consumer abstraction.
    Compatible with Kafka, RabbitMQ, Redis, MQTT, etc.
    """
    
    def subscribe(self, topics: list) -> None:
        """Subscribe to topics/channels."""
        ...
    
    def poll(self, timeout: float) -> Any:
        """Poll for messages with timeout in seconds."""
        ...
    
    def close(self) -> None:
        """Close the consumer connection."""
        ...


class MessageProducer(Protocol):
    """
    Protocol for message producer abstraction.
    Compatible with Kafka, RabbitMQ, Redis, MQTT, etc.
    """
    
    def produce(self, topic: str, value: bytes, **kwargs) -> None:
        """Produce a message to a topic/channel."""
        ...
    
    def flush(self, timeout: Optional[float] = None) -> None:
        """Flush pending messages."""
        ...


class MessageAdapter(ABC):
    """
    Abstract adapter for different messaging systems.
    
    Deprecation Note:
        This class is maintained for backward compatibility.
        New code should use BrokerAdapter from BrokerDEVS.Core.BrokerAdapter
    """
    
    @abstractmethod
    def create_consumer(self, config: Dict[str, Any]) -> MessageConsumer:
        """Create a consumer instance."""
        ...
    
    @abstractmethod
    def create_producer(self, config: Dict[str, Any]) -> MessageProducer:
        """Create a producer instance."""
        ...
    
    @abstractmethod
    def extract_message_value(self, message: Any) -> bytes:
        """Extract message value from the messaging system's message format."""
        ...
    
    @abstractmethod
    def has_error(self, message: Any) -> bool:
        """Check if message has an error."""
        ...
    
    @abstractmethod
    def get_topic(self, message: Any) -> str:
        """Get topic/channel name from message."""
        ...




class InMemoryMessagingWorker(threading.Thread, ABC):
    """
    Generic in-memory worker thread for distributed DEVS simulation.
    
    Manages one atomic DEVS model and communicates with coordinator via messages.
    Works with any message broker (Kafka, MQTT, RabbitMQ, etc.) through adapters.
    
    Attributes:
        aDEVS: The atomic DEVS model instance
        model_name: Identifier for the model
        in_topic: Topic to receive commands from coordinator
        out_topic: Topic to send outputs to coordinator
        running: Thread control flag
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
            model_name: Name/identifier of the DEVS model
            aDEVS: The atomic DEVS model instance
            adapter: Messaging system adapter (Kafka, RabbitMQ, etc.)
            consumer_config: Configuration dictionary for consumer
            producer_config: Configuration dictionary for producer
            in_topic: Topic to receive commands from coordinator
            out_topic: Topic to send model outputs to coordinator
            
        Raises:
            ValueError: If topics are not provided
        """
        super().__init__(daemon=True)
        
        if not in_topic or not out_topic:
            raise ValueError("Both in_topic and out_topic must be provided")
        
        self.aDEVS = aDEVS
        self.model_name = model_name
        self.adapter = adapter
        self.running = True
        self._lock = threading.Lock()

        # Topics for coordinator communication
        self.in_topic = in_topic
        self.out_topic = out_topic

        # Create consumer and producer using adapter
        self.consumer = adapter.create_consumer(consumer_config)
        self.consumer.subscribe([self.in_topic])

        self.producer = adapter.create_producer(producer_config)

        logger.info(
            "InMemoryMessagingWorker initialized for model '%s' "
            "(in_topic=%s, out_topic=%s)",
            model_name, in_topic, out_topic
        )
    
    def get_model(self):
        """Return the atomic DEVS model managed by this worker."""
        return self.aDEVS
    
    def get_model_label(self) -> str:
        """Return the model name/label."""
        return self.model_name
    
    def get_model_time_next(self) -> float:
        """Return the next scheduled time for the model."""
        return self.aDEVS.timeNext
    
    def is_running(self) -> bool:
        """Check if the worker thread is running."""
        return self.running


    
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # DEVS TRANSITION HANDLERS
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    def do_initialize(self, t: float):
        """
        Initialize the atomic model before simulation starts.
        
        Args:
            t: Current simulation time
        """
        self.aDEVS.sigma = 0.0
        self.aDEVS.timeLast = 0.0
        self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
        self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance
    
        if self.aDEVS.myTimeAdvance != float("inf"): 
            self.aDEVS.myTimeAdvance += t

    def do_external_transition(self, t: float, msg: Any):
        """
        Perform an external transition with input values.
        
        Args:
            t: Time of transition
            msg: Message containing input values
        """
        port_inputs = {}

        # Build dict {port_obj -> Message(value, time)}
        from DomainInterface.Object import Message
        
        # Handle both old message format and new BaseMessage format
        port_value_list = self._extract_port_values(msg)
        
        for pv in port_value_list:
            # pv.portIdentifier must match the input port name
            for iport in self.aDEVS.IPorts:
                if iport.name == pv.portIdentifier:
                    m = Message(pv.value, t)
                    port_inputs[iport] = m
                    break
        
        self.aDEVS.myInput = port_inputs

        # Update elapsed time
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
        """
        Perform an internal transition (no external inputs).
        
        Args:
            t: Time of transition
        """
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
        """
        Call the output function on the atomic model.
        Returns list of output values on ports.
        """
        self.aDEVS.outputFnc()

    def _extract_port_values(self, msg: Any) -> list:
        """
        Extract port values from message (compatible with both old and new formats).
        
        Args:
            msg: Message object
            
        Returns:
            List of port values
        """
        # Check if it's a BaseMessage with portValueList
        if hasattr(msg, 'portValueList'):
            return msg.portValueList
        # Check if it's a dict with modelInputsOption
        elif isinstance(msg, dict) and 'modelInputsOption' in msg:
            pvl = msg['modelInputsOption'].get('portValueList', [])
            # Convert dicts back to PortValue objects if needed
            from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import PortValue
            return [
                PortValue.from_dict(pv) if isinstance(pv, dict) else pv
                for pv in pvl
            ]
        return []



## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # MESSAGE PROCESSING (Abstract - implement in subclasses)
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    @abstractmethod
    def _process_standard(self, data: Dict[str, Any]) -> None:
        """
        Process a standard DEVS message.
        Must be implemented by subclasses to handle specific message types.
        
        Args:
            data: Parsed message data (dict or BaseMessage)
        """
        ...

    def process_message(self, msg_bytes: bytes) -> None:
        """
        Deserialize and process a message.
        
        Args:
            msg_bytes: Serialized message bytes
        """
        try:
            # Try new BaseMessage format first
            try:
                msg = BaseMessage.from_bytes(msg_bytes)
                logger.debug("Received %s message", msg.devsType)
                self._process_standard(msg)
            except (ValueError, json.JSONDecodeError):
                # Fall back to old dict format
                raw = msg_bytes.decode("utf-8")
                data = json.loads(raw)
                self._process_standard(data)
        except Exception as e:
            logger.error("Error processing message: %s", e, exc_info=True)

    
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # MAIN WORKER LOOP
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    def run(self):
        """
        Main worker thread loop.
        Continuously polls for messages and processes them.
        """
        logger.info("InMemoryMessagingWorker started for model '%s'", self.model_name)

        try:
            while self.running:
                # Poll for message with timeout
                msg = self.consumer.poll(timeout=0.5)
                
                if msg is None:
                    continue
                
                # Check for errors
                if self.adapter.has_error(msg):
                    error = msg.error() if hasattr(msg, 'error') else 'Unknown error'
                    logger.warning("Message error: %s", error)
                    continue

                try:
                    raw_value = self.adapter.extract_message_value(msg)
                    if raw_value is None:
                        continue
                    
                    topic = self.adapter.get_topic(msg)
                    worker_kafka_logger.debug(
                        "Received message from topic=%s (size=%d bytes)",
                        topic, len(raw_value)
                    )
                    
                    self.process_message(raw_value)

                except Exception as e:
                    logger.error("Error processing message: %s", e, exc_info=True)

        except Exception as e:
            logger.error("Worker loop error: %s", e, exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """Stop the worker thread and cleanup resources."""
        with self._lock:
            self.running = False
        
        try:
            self.consumer.close()
            logger.info("InMemoryMessagingWorker stopped for model '%s'", self.model_name)
        except Exception as e:
            logger.error("Error closing consumer: %s", e)

    def send_message(self, data: bytes, key: Optional[str] = None) -> bool:
        """
        Send a message to the coordinator.
        
        Args:
            data: Message bytes to send
            key: Optional message key (e.g., model name)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.running:
            logger.warning("Worker not running, cannot send message")
            return False
        
        try:
            with self._lock:
                key_bytes = key.encode("utf-8") if key else self.model_name.encode("utf-8")
                self.producer.produce(self.out_topic, value=data, key=key_bytes)
                self.producer.flush()
                return True
        except Exception as e:
            logger.error("Failed to send message: %s", e)
            return False
