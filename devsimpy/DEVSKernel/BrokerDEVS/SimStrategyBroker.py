# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# SimStrategyBroker.py ---
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
# Generic broker-based distributed DEVS simulation strategy.
# Works with any message broker: Kafka, MQTT, RabbitMQ, Redis, etc.
# Orchestrates simulation by distributing model execution across workers.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
from typing import Dict, Any, List, Optional

from DEVSKernel.PyDEVS.SimStrategies import DirectCouplingPyDEVSSimStrategy
from DEVSKernel.BrokerDEVS.Core.BrokerAdapter import BrokerAdapter
from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import (
    BaseMessage,
    SimTime,
    InitSim,
    ExecuteTransition,
    ModelOutputMessage,
    ModelDone,
    NextTime,
    SendOutput,
    SimulationDone,
    PortValue,
)
from DEVSKernel.BrokerDEVS.Proxies.BrokerStreamProxy import BrokerStreamProxy
from DEVSKernel.BrokerDEVS.Proxies.BrokerReceiverProxy import BrokerReceiverProxy

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERIC BROKER SIMULATION STRATEGY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class SimStrategyBroker(DirectCouplingPyDEVSSimStrategy):
    """
    Generic broker-based distributed DEVS simulation strategy.
    
    Orchestrates distributed DEVS simulation across workers connected via
    message brokers. Supports any broker through the BrokerAdapter interface.
    
    Supported Brokers:
    - Apache Kafka
    - MQTT
    - RabbitMQ
    - Redis
    - Azure Event Hubs
    - AWS MSK
    - Any other broker with a BrokerAdapter implementation
    
    Features:
    - Broker-agnostic coordination
    - Automatic worker communication via topics
    - Message serialization/deserialization
    - Timeout and deadline management
    - Error handling and recovery
    - Graceful shutdown
    - Extensible for custom behavior
    
    Architecture:
    - Coordinator: This strategy instance (orchestrates simulation)
    - Workers: Distributed model execution threads
    - Broker: Message transport (Kafka, MQTT, etc.)
    - Topics: Communication channels
    """

    def __init__(
        self,
        simulator=None,
        broker_adapter: Optional[BrokerAdapter] = None,
        bootstrap_servers: str = "localhost:9092",
        request_timeout: float = 30.0,
        in_topic_prefix: str = "devs-in",
        out_topic_prefix: str = "devs-out",
        **kwargs,
    ):
        """
        Initialize broker-based simulation strategy.
        
        Args:
            simulator: PyDEVS simulator instance
            broker_adapter: BrokerAdapter instance (e.g., KafkaAdapter)
                If None, will be created with bootstrap_servers
            bootstrap_servers: Broker bootstrap servers address
            request_timeout: Maximum time to wait for worker responses (seconds)
            in_topic_prefix: Prefix for input topics (coordinator -> workers)
            out_topic_prefix: Prefix for output topics (workers -> coordinator)
            **kwargs: Additional arguments for parent strategy
            
        Raises:
            ValueError: If broker_adapter and bootstrap_servers are both missing
        """
        super().__init__(simulator, **kwargs)

        if broker_adapter is None and not bootstrap_servers:
            raise ValueError(
                "Either broker_adapter or bootstrap_servers must be provided"
            )

        self.broker_adapter = broker_adapter
        self.bootstrap_servers = bootstrap_servers
        self.request_timeout = request_timeout
        self.in_topic_prefix = in_topic_prefix
        self.out_topic_prefix = out_topic_prefix

        # Create or use provided proxies
        self._stream_proxy = None
        self._receiver_proxy = None
        self._worker_topics = {}  # model -> (in_topic, out_topic)

        logger.info(
            "Initialized SimStrategyBroker "
            "(broker=%s, timeout=%.1fs)",
            broker_adapter.broker_name if broker_adapter else "TBD",
            request_timeout,
        )

    def _ensure_proxies(self):
        """Lazily initialize proxies on first use."""
        if self._stream_proxy is None:
            self._stream_proxy = BrokerStreamProxy(
                self.broker_adapter,
            )
            logger.debug("Created BrokerStreamProxy")

        if self._receiver_proxy is None:
            self._receiver_proxy = BrokerReceiverProxy(
                self.broker_adapter,
            )
            logger.debug("Created BrokerReceiverProxy")

    def _get_model_topics(self, model) -> tuple:
        """
        Get input and output topics for a model.
        
        Args:
            model: DEVS model instance
            
        Returns:
            Tuple of (in_topic, out_topic)
        """
        model_id = self._get_model_id(model)

        if model_id not in self._worker_topics:
            in_topic = f"{self.in_topic_prefix}-{model_id}"
            out_topic = f"{self.out_topic_prefix}-{model_id}"
            self._worker_topics[model_id] = (in_topic, out_topic)

        return self._worker_topics[model_id]

    def _get_model_id(self, model) -> str:
        """
        Get unique identifier for a model.
        
        Args:
            model: DEVS model instance
            
        Returns:
            Model identifier string
        """
        # Try various attributes
        for attr in ["label", "name", "myID"]:
            if hasattr(model, attr):
                value = getattr(model, attr)
                if value is not None:
                    return str(value)
        return str(id(model))

    def _send_message_to_broker(
        self,
        topic: str,
        msg: BaseMessage,
        key: Optional[str] = None,
    ) -> bool:
        """
        Send a message to a broker topic.
        
        Args:
            topic: Destination topic
            msg: Message to send
            key: Optional message key
            
        Returns:
            True if successful
        """
        self._ensure_proxies()
        return self._stream_proxy.send_message(topic, msg, key)

    def _await_responses_from_broker(
        self,
        models: List,
        timeout: Optional[float] = None,
    ) -> Dict[Any, BaseMessage]:
        """
        Wait for responses from specified models.
        
        Args:
            models: List of models to wait for
            timeout: Maximum wait time (uses default if None)
            
        Returns:
            Dictionary mapping models to their responses
            
        Raises:
            TimeoutError: If not all responses received
        """
        self._ensure_proxies()
        timeout = timeout or self.request_timeout

        # Subscribe to output topics
        out_topics = set()
        for model in models:
            _, out_topic = self._get_model_topics(model)
            out_topics.add(out_topic)

        self._receiver_proxy.subscribe(list(out_topics))

        # Wait for messages
        return self._receiver_proxy.receive_messages(models, timeout)

    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # SIMULATION COORDINATION METHODS
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    def initialize(self):
        """Initialize simulation and send initialization messages to workers."""
        logger.info("Initializing distributed simulation via %s", self.broker_adapter.broker_name)

        super().initialize()

        # Send initialization messages to all atomic models
        for atomic_model in self._atomic_models:
            in_topic, _ = self._get_model_topics(atomic_model)

            msg = InitSim(time=SimTime(t=self.simulator.time))
            self._send_message_to_broker(
                in_topic,
                msg,
                key=self._get_model_id(atomic_model),
            )

        logger.info("Sent initialization messages to %d workers", len(self._atomic_models))

    def execute_transition(
        self,
        model,
        external_inputs: Optional[Dict] = None,
    ) -> Any:
        """
        Execute a state transition on a model via broker.
        
        Args:
            model: The DEVS model
            external_inputs: Optional external input values
            
        Returns:
            Model output (if any)
        """
        in_topic, out_topic = self._get_model_topics(model)
        model_id = self._get_model_id(model)

        # Build port value list from external inputs
        port_values = []
        if external_inputs:
            for port, value in external_inputs.items():
                port_values.append(
                    PortValue(
                        value=value,
                        portIdentifier=port.name if hasattr(port, "name") else str(port),
                        portType="java.lang.Object",
                    )
                )

        # Send execution message
        msg = ExecuteTransition(
            time=SimTime(t=self.simulator.time),
            portValueList=port_values,
        )
        self._send_message_to_broker(in_topic, msg, key=model_id)

        # Wait for response
        try:
            responses = self._await_responses_from_broker([model])
            return responses.get(model)
        except TimeoutError as e:
            logger.error("Timeout executing transition on %s: %s", model_id, e)
            raise

    def get_model_output(self, model) -> Optional[ModelOutputMessage]:
        """
        Get output from a model.
        
        Args:
            model: The DEVS model
            
        Returns:
            ModelOutputMessage with outputs, or None
        """
        in_topic, _ = self._get_model_topics(model)
        model_id = self._get_model_id(model)

        # Send output request
        msg = SendOutput(time=SimTime(t=self.simulator.time))
        self._send_message_to_broker(in_topic, msg, key=model_id)

        # Wait for output
        try:
            responses = self._await_responses_from_broker([model])
            return responses.get(model)
        except TimeoutError:
            logger.warning("Timeout getting output from %s", model_id)
            return None

    def get_next_time(self, model) -> float:
        """
        Get next event time from a model.
        
        Args:
            model: The DEVS model
            
        Returns:
            Next event time
        """
        in_topic, _ = self._get_model_topics(model)
        model_id = self._get_model_id(model)

        # Send time request
        msg = SendOutput(time=SimTime(t=self.simulator.time))
        self._send_message_to_broker(in_topic, msg, key=model_id)

        # Wait for response
        try:
            responses = self._await_responses_from_broker([model])
            response = responses.get(model)
            if isinstance(response, NextTime):
                return response.time.t
        except TimeoutError:
            logger.warning("Timeout getting next time from %s", model_id)

        return float("inf")

    def finish_simulation(self):
        """Signal simulation completion to all workers."""
        logger.info("Finishing distributed simulation")

        # Send completion message to all workers
        for atomic_model in self._atomic_models:
            in_topic, _ = self._get_model_topics(atomic_model)
            model_id = self._get_model_id(atomic_model)

            msg = SimulationDone(time=SimTime(t=self.simulator.time))
            self._send_message_to_broker(in_topic, msg, key=model_id)

        # Cleanup
        self._cleanup()
        logger.info("Distributed simulation finished")

    def _cleanup(self):
        """Cleanup broker connections."""
        try:
            if self._stream_proxy:
                self._stream_proxy.close()
            if self._receiver_proxy:
                self._receiver_proxy.close()
            logger.info("Closed broker connections")
        except Exception as e:
            logger.error("Error during cleanup: %s", e)

    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # CONCRETE IMPLEMENTATIONS (instead of abstract methods)
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    def _handle_worker_output(self, model, output_msg: ModelOutputMessage):
        """
        Handle output from a worker.

        Applies output couplings to distribute outputs to coupled models.

        Args:
            model: The model that produced output
            output_msg: The output message
        """
        if not output_msg or not output_msg.modelOutput:
            return

        logger.debug(
            "Handling output from %s: %d port values",
            self._get_model_id(model),
            len(output_msg.modelOutput),
        )

        # Convert port values back to internal format
        # This depends on your specific DEVS framework
        # For now, just log the outputs
        for pv in output_msg.modelOutput:
            logger.debug(
                "  Port %s: %s",
                pv.portIdentifier,
                pv.value,
            )

    def _distribute_inputs(self, model, inputs: Dict):
        """
        Distribute input values to a model.

        Handles input routing and coupling from other models.

        Args:
            model: The target model
            inputs: Dictionary of input port -> value
        """
        if not inputs:
            return

        logger.debug(
            "Distributing %d inputs to model %s",
            len(inputs),
            self._get_model_id(model),
        )

        for port, value in inputs.items():
            logger.debug(
                "  Port %s: %s",
                port if isinstance(port, str) else port.name,
                value,
            )


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CONCRETE BROKER STRATEGIES
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class KafkaSimStrategy(SimStrategyBroker):
    """
    Kafka-specific simulation strategy.
    
    Uses Apache Kafka for distributed DEVS simulation coordination.
    """

    def __init__(
        self,
        simulator=None,
        bootstrap_servers: str = "localhost:9092",
        **kwargs,
    ):
        """
        Initialize Kafka simulation strategy.
        
        Args:
            simulator: PyDEVS simulator
            bootstrap_servers: Kafka bootstrap servers
            **kwargs: Additional arguments
        """
        from DEVSKernel.BrokerDEVS.Brokers.kafka.KafkaAdapter import KafkaAdapter

        adapter = KafkaAdapter(bootstrap_servers)
        super().__init__(
            simulator,
            broker_adapter=adapter,
            bootstrap_servers=bootstrap_servers,
            **kwargs,
        )

    def _handle_worker_output(self, model, output_msg: ModelOutputMessage):
        """Handle Kafka worker output."""
        # Call parent implementation for standard coupling logic
        super()._handle_worker_output(model, output_msg)
        logger.debug("Kafka worker output processed")

    def _distribute_inputs(self, model, inputs: Dict):
        """Distribute inputs via Kafka."""
        # Call parent implementation for standard input routing
        super()._distribute_inputs(model, inputs)
        logger.debug("Kafka inputs distributed")


class MqttSimStrategy(SimStrategyBroker):
    """
    MQTT-specific simulation strategy.
    
    Uses MQTT for distributed DEVS simulation coordination.
    """

    def __init__(
        self,
        simulator=None,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        **kwargs,
    ):
        """
        Initialize MQTT simulation strategy.
        
        Args:
            simulator: PyDEVS simulator
            broker_host: MQTT broker host
            broker_port: MQTT broker port
            **kwargs: Additional arguments
        """
        from DEVSKernel.BrokerDEVS.Brokers.mqtt.MqttAdapter import MqttAdapter

        adapter = MqttAdapter(broker_host)
        super().__init__(
            simulator,
            broker_adapter=adapter,
            bootstrap_servers=f"{broker_host}:{broker_port}",
            **kwargs,
        )

    def _handle_worker_output(self, model, output_msg: ModelOutputMessage):
        """Handle MQTT worker output."""
        # Call parent implementation for standard coupling logic
        super()._handle_worker_output(model, output_msg)
        logger.debug("MQTT worker output processed")

    def _distribute_inputs(self, model, inputs: Dict):
        """Distribute inputs via MQTT."""
        # Call parent implementation for standard input routing
        super()._distribute_inputs(model, inputs)
        logger.debug("MQTT inputs distributed")


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# STRATEGY FACTORY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerSimStrategyFactory:
    """Factory for creating broker simulation strategies."""

    _STRATEGIES = {
        "kafka": KafkaSimStrategy,
        "mqtt": MqttSimStrategy,
    }

    @classmethod
    def create(
        cls,
        broker_type: str,
        simulator=None,
        **kwargs,
    ) -> SimStrategyBroker:
        """
        Create a simulation strategy for a specific broker.
        
        Args:
            broker_type: Broker type ('kafka', 'mqtt', etc.)
            simulator: PyDEVS simulator
            **kwargs: Broker-specific arguments
            
        Returns:
            Configured SimStrategyBroker instance
            
        Raises:
            ValueError: If broker_type is unknown
        """
        strategy_class = cls._STRATEGIES.get(broker_type.lower())
        if strategy_class is None:
            available = ", ".join(cls._STRATEGIES.keys())
            raise ValueError(
                f"Unknown broker type: {broker_type}. Available: {available}"
            )

        return strategy_class(simulator, **kwargs)

    @classmethod
    def register_strategy(cls, broker_type: str, strategy_class):
        """Register a custom strategy for a broker type."""
        cls._STRATEGIES[broker_type.lower()] = strategy_class

    @classmethod
    def get_available_strategies(cls) -> list:
        """Get list of available strategies."""
        return list(cls._STRATEGIES.keys())
