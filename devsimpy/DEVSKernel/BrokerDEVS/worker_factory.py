# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# worker_factory.py ---
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
# Unified factory for creating DEVS workers with any (Standard + Broker) combination.
# Eliminates hard-coded conditionals and enables extensibility.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
from typing import Any, Optional

from .standard_registry import StandardRegistry, MessageStandard, BrokerType
from .simulation_config import SimulationConfig

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# WORKER FACTORY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class WorkerFactory:
    """
    Universal factory for creating DEVS workers.
    
    Supports any combination of message standard and broker without
    hard-coding specific types.
    """
    
    @staticmethod
    def create_worker(
        model_name: str,
        model: Any,
        config: SimulationConfig,
    ) -> Any:
        """
        Create a DEVS worker for the given model and configuration.
        
        Args:
            model_name: Unique identifier for the model
            model: DEVS model instance
            config: SimulationConfig with broker and standard selection
            
        Returns:
            Configured worker instance for the (standard, broker) pair
            
        Raises:
            ValueError: If standard or broker is not supported
            RuntimeError: If worker creation fails
            
        Example:
            config = SimulationConfig(
                broker_type='mqtt',
                broker_host='localhost',
                broker_port=1883,
                message_standard='ms4me',
            )
            worker = WorkerFactory.create_worker('Model_0', my_model, config)
        """
        logger.debug(
            "Creating worker: model=%s, standard=%s, broker=%s",
            model_name,
            config.message_standard,
            config.broker_type,
        )
        
        # Convert string values to enums
        try:
            standard = MessageStandard(config.message_standard)
            broker = BrokerType(config.broker_type)
        except ValueError as e:
            raise ValueError(
                f"Invalid standard or broker: standard={config.message_standard}, "
                f"broker={config.broker_type}"
            ) from e
        
        # Get worker class from registry
        try:
            worker_class = StandardRegistry.get_worker_class(standard, broker)
            if worker_class is None:
                raise KeyError(f"No worker for {standard}/{broker}")
        except (KeyError, ValueError) as e:
            raise ValueError(
                f"Unsupported combination: standard={config.message_standard}, "
                f"broker={config.broker_type}"
            ) from e
        
        # Create worker instance
        try:
            worker = worker_class(
                model_name=model_name,
                model=model,
                broker_type=config.broker_type,
                broker_host=config.broker_host,
                broker_port=config.broker_port,
                username=config.username,
                password=config.password,
                extra_config=config.extra_config,
            )
            
            logger.info(
                "Created worker %s for model %s: %s",
                worker.__class__.__name__,
                model_name,
                config,
            )
            return worker
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to create worker for model {model_name}: {e}"
            ) from e
    
    @staticmethod
    def create_worker_from_env(
        model_name: str,
        model: Any,
        standard: str = "ms4me",
        auto_detect: bool = True,
    ) -> Any:
        """
        Create a worker with auto-configured settings.
        
        Args:
            model_name: Unique identifier for the model
            model: DEVS model instance
            standard: Message standard to use
            auto_detect: Enable broker auto-detection
            
        Returns:
            Configured worker
            
        Example:
            worker = WorkerFactory.create_worker_from_env(
                'Model_0', 
                my_model,
                standard='ms4me',
            )
        """
        from .simulation_config import AutoSimulationConfig
        
        auto_config = AutoSimulationConfig(standard, auto_detect=auto_detect)
        config = auto_config.configure()
        
        return WorkerFactory.create_worker(model_name, model, config)
    
    @staticmethod
    def get_supported_standards() -> list:
        """Get list of supported message standards."""
        return StandardRegistry.list_registered_standards()
    
    @staticmethod
    def get_supported_brokers(standard: str) -> list:
        """
        Get list of supported brokers for a given standard.
        
        Args:
            standard: Message standard
            
        Returns:
            List of supported broker types
        """
        return StandardRegistry.list_supported_brokers(standard)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# HELPER FUNCTION FOR BACKWARD COMPATIBILITY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def create_worker(
    model_name: str,
    model: Any,
    broker_type: str,
    broker_host: str,
    broker_port: int,
    standard: str = "ms4me",
    **extra_kwargs,
) -> Any:
    """
    Create a worker (backward-compatible function).
    
    Args:
        model_name: Unique identifier
        model: DEVS model instance
        broker_type: Type of message broker
        broker_host: Broker hostname
        broker_port: Broker port
        standard: Message standard (default: ms4me)
        **extra_kwargs: Extra configuration options
        
    Returns:
        Configured worker
        
    Note:
        This is a convenience function. Prefer using WorkerFactory
        directly for more control.
    """
    config = SimulationConfig(
        broker_type=broker_type,
        broker_host=broker_host,
        broker_port=broker_port,
        message_standard=standard,
        extra_config=extra_kwargs,
    )
    
    return WorkerFactory.create_worker(model_name, model, config)
