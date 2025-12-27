# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# InMemoryBrokerWorker.py ---
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
# Modern generic in-memory worker for distributed DEVS simulation.
# Uses the new BrokerAdapter interface for broker-agnostic communication.
# Supports Kafka, MQTT, RabbitMQ, and any other message broker.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import threading
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from DEVSKernel.BrokerDEVS.Core.BrokerAdapter import BrokerAdapter
from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import BaseMessage, PortValue

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERIC BROKER WORKER
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class InMemoryBrokerWorker(threading.Thread, ABC):
    """
    Modern generic in-memory worker for distributed DEVS simulation.
    
    Uses the generic BrokerAdapter interface to work with any message broker:
    - Apache Kafka
    - MQTT
    - RabbitMQ
    - Redis
    - Azure Event Hubs
    - AWS MSK
    - etc.
    
    Features:
    - Thread-based in-memory model execution
    - Broker-agnostic message communication
    - Automatic message serialization/deserialization
    - Thread-safe operations
    - Graceful shutdown and cleanup
    
    Attributes:
        model_name: Identifier for the DEVS model
        aDEVS: The atomic DEVS model instance
        broker_adapter: The broker adapter for message operations
        in_topic: Topic to receive commands from coordinator
        out_topic: Topic to send outputs to coordinator
        running: Thread control flag
    """

    def __init__(
        self,
        model_name: str,
        aDEVS,
        broker_adapter: BrokerAdapter,
        bootstrap_servers: str,
        in_topic: str,
        out_topic: str,
        consumer_config: Optional[Dict[str, Any]] = None,
        producer_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the broker worker.
        
        Args:
            model_name: Name/identifier for the DEVS model
            aDEVS: The atomic DEVS model instance
            broker_adapter: BrokerAdapter instance (e.g., KafkaAdapter, MqttAdapter)
            bootstrap_servers: Broker bootstrap servers address
            in_topic: Topic to receive commands from coordinator
            out_topic: Topic to send outputs to coordinator
            consumer_config: Custom consumer configuration dictionary
            producer_config: Custom producer configuration dictionary
            
        Raises:
            ValueError: If topics are not provided
            ImportError: If broker dependencies are not installed
        """
        super().__init__(daemon=True)

        if not in_topic or not out_topic:
            raise ValueError("Both in_topic and out_topic must be provided")

        self.model_name = model_name
        self.aDEVS = aDEVS
        self.broker_adapter = broker_adapter
        self.bootstrap_servers = bootstrap_servers
        self.in_topic = in_topic
        self.out_topic = out_topic
        self.running = True
        self._lock = threading.Lock()

        logger.info(
            "Initializing InMemoryBrokerWorker for model '%s' "
            "(broker=%s, in_topic=%s, out_topic=%s)",
            model_name,
            broker_adapter.broker_name,
            in_topic,
            out_topic,
        )

        # Create broker consumer and producer
        self.consumer = broker_adapter.create_consumer(consumer_config)
        self.producer = broker_adapter.create_producer(producer_config)

        # Subscribe to input topic
        try:
            self.consumer.subscribe([in_topic])
        except Exception as e:
            logger.error("Failed to subscribe to topic %s: %s", in_topic, e)
            raise

    def run(self):
        """
        Main worker thread loop.
        Continuously polls for messages and processes them.
        """
        logger.info(
            "Starting worker thread for model '%s' (broker=%s)",
            self.model_name,
            self.broker_adapter.broker_name,
        )

        try:
            while self.running:
                # Poll for message from broker
                message = self.consumer.poll(timeout=1.0)

                if message is None:
                    continue

                # Check for errors
                if self.broker_adapter.has_error(message):
                    error = message.error() if hasattr(message, "error") else "Unknown"
                    logger.warning("Message error from broker: %s", error)
                    continue

                try:
                    # Extract and deserialize message
                    topic = self.broker_adapter.get_topic(message)
                    msg_bytes = self.broker_adapter.extract_message_value(message)

                    if msg_bytes is None:
                        continue

                    # Deserialize to BaseMessage
                    msg = BaseMessage.from_bytes(msg_bytes)
                    logger.debug(
                        "Received message type=%s from topic=%s",
                        msg.devsType,
                        topic,
                    )

                    # Process the message
                    self._handle_message(msg)

                except Exception as e:
                    logger.error(
                        "Error processing message: %s", e, exc_info=True
                    )

        except Exception as e:
            logger.error("Worker thread error: %s", e, exc_info=True)
        finally:
            self.stop()

    @abstractmethod
    def _handle_message(self, msg: BaseMessage) -> None:
        """
        Handle a received message from the coordinator.
        
        This method must be implemented by subclasses to define
        specific behavior for different message types.
        
        Args:
            msg: The deserialized BaseMessage instance
            
        Note:
            Override this in subclasses for custom message handling.
            Example message types:
            - InitSim: Initialize simulation
            - ExecuteTransition: Execute state transition
            - SendOutput: Output phase
            - SimulationDone: Simulation complete
        """
        ...

    def send_message(self, msg: BaseMessage) -> bool:
        """
        Send a message to the coordinator.
        
        Args:
            msg: The BaseMessage to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.running:
            logger.warning("Worker not running, cannot send message")
            return False

        try:
            with self._lock:
                # Serialize message
                msg_bytes = msg.to_bytes()

                # Send via broker
                self.producer.produce(
                    self.out_topic,
                    value=msg_bytes,
                    key=self.model_name.encode("utf-8"),
                )
                self.producer.flush()

                logger.debug(
                    "Sent message type=%s to topic=%s (broker=%s)",
                    msg.devsType,
                    self.out_topic,
                    self.broker_adapter.broker_name,
                )
                return True

        except Exception as e:
            logger.error("Failed to send message: %s", e)
            return False

    def stop(self):
        """
        Stop the worker thread and cleanup resources.
        """
        with self._lock:
            self.running = False

        try:
            self.consumer.close()
            logger.info(
                "Worker stopped for model '%s' (broker=%s)",
                self.model_name,
                self.broker_adapter.broker_name,
            )
        except Exception as e:
            logger.error("Error closing consumer: %s", e)

    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # DEVS TRANSITION HANDLERS
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    def do_initialize(self, t: float):
        """
        Initialize the atomic model before simulation.
        
        Args:
            t: Initial simulation time
        """
        self.aDEVS.sigma = 0.0
        self.aDEVS.timeLast = 0.0
        self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
        self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance

        if self.aDEVS.myTimeAdvance != float("inf"):
            self.aDEVS.myTimeAdvance += t

    def do_external_transition(self, t: float, port_values: list):
        """
        Perform an external transition with input values.
        
        Args:
            t: Time of transition
            port_values: List of PortValue objects with inputs
        """
        from DomainInterface.Object import Message

        port_inputs = {}

        # Map port values to model input ports
        for pv in port_values:
            for iport in self.aDEVS.IPorts:
                if iport.name == pv.portIdentifier:
                    msg = Message(pv.value, t)
                    port_inputs[iport] = msg
                    break

        self.aDEVS.myInput = port_inputs
        self.aDEVS.elapsed = t - self.aDEVS.timeLast

        # Execute external transition
        self.aDEVS.extTransition()

        # Update state variables
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
        self.aDEVS.elapsed = t - self.aDEVS.timeLast

        # Execute internal transition
        self.aDEVS.intTransition()

        # Update state variables
        self.aDEVS.timeLast = t
        self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
        self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance

        if self.aDEVS.myTimeAdvance != float("inf"):
            self.aDEVS.myTimeAdvance += t

        self.aDEVS.elapsed = 0

    def do_output_function(self):
        """
        Execute the output function on the atomic model.
        """
        self.aDEVS.outputFnc()

    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # ACCESSORS
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

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

    def get_broker_name(self) -> str:
        """Return the name of the broker being used."""
        return self.broker_adapter.broker_name


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# WORKER FACTORY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class InMemoryBrokerWorkerFactory:
    """Factory for creating InMemoryBrokerWorker instances."""

    @staticmethod
    def create(
        model_name: str,
        aDEVS,
        broker_adapter: BrokerAdapter,
        bootstrap_servers: str,
        in_topic: str,
        out_topic: str,
        consumer_config: Optional[Dict[str, Any]] = None,
        producer_config: Optional[Dict[str, Any]] = None,
        worker_class: type = None,
    ) -> "InMemoryBrokerWorker":
        """
        Create a broker worker with validation.
        
        Args:
            model_name: Model identifier
            aDEVS: DEVS model instance
            broker_adapter: BrokerAdapter instance
            bootstrap_servers: Broker address
            in_topic: Input topic
            out_topic: Output topic
            consumer_config: Consumer configuration
            producer_config: Producer configuration
            worker_class: Custom worker class (must inherit from InMemoryBrokerWorker)
            
        Returns:
            Configured worker instance
            
        Raises:
            ValueError: If validation fails
            TypeError: If worker_class doesn't inherit from InMemoryBrokerWorker
        """
        if not model_name or not aDEVS or not broker_adapter:
            raise ValueError(
                "model_name, aDEVS, and broker_adapter are required"
            )

        if worker_class and not issubclass(
            worker_class, InMemoryBrokerWorker
        ):
            raise TypeError(
                "worker_class must inherit from InMemoryBrokerWorker"
            )

        # Use default worker class if not provided
        if worker_class is None:
            from DEVSKernel.BrokerDEVS.Workers.DefaultBrokerWorker import (
                DefaultBrokerWorker,
            )

            worker_class = DefaultBrokerWorker

        # Create and return worker
        return worker_class(
            model_name=model_name,
            aDEVS=aDEVS,
            broker_adapter=broker_adapter,
            bootstrap_servers=bootstrap_servers,
            in_topic=in_topic,
            out_topic=out_topic,
            consumer_config=consumer_config,
            producer_config=producer_config,
        )
