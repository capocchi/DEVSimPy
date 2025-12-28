# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# simulation_config.py ---
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
# Unified configuration for distributed DEVS simulations.
# Combines broker configuration with message standard selection.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import os
from typing import Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# SIMULATION CONFIGURATION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


@dataclass
class SimulationConfig:
    """
    Complete configuration for a distributed DEVS simulation.
    
    Combines broker settings with message standard selection.
    """
    
    # Broker configuration
    broker_type: str                    # 'kafka', 'mqtt', 'rabbitmq', etc.
    broker_host: str                    # Broker hostname
    broker_port: int                    # Broker port
    
    # Message standard
    message_standard: str               # 'ms4me', 'yourstandard', etc.
    
    # Optional authentication
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Optional extra options
    extra_config: Optional[dict] = None
    
    @property
    def broker_address(self) -> str:
        """Get broker address in host:port format."""
        return f"{self.broker_host}:{self.broker_port}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'broker_type': self.broker_type,
            'broker_host': self.broker_host,
            'broker_port': self.broker_port,
            'message_standard': self.message_standard,
            'broker_address': self.broker_address,
            'username': self.username,
            'password': self.password,
            'extra_config': self.extra_config or {},
        }
    
    def __str__(self):
        return (f"SimulationConfig("
                f"standard={self.message_standard}, "
                f"broker={self.broker_type}://{self.broker_address})")


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# AUTO-CONFIGURATION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class AutoSimulationConfig:
    """
    Auto-configure simulation with message standard + broker detection.
    
    Priority order:
    1. Explicit environment variables
    2. Detected available brokers
    3. Default fallback
    """
    
    ENV_STANDARD = "DEVS_MESSAGE_STANDARD"
    ENV_BROKER_TYPE = "DEVS_BROKER_TYPE"
    ENV_BROKER_HOST = "DEVS_BROKER_HOST"
    ENV_BROKER_PORT = "DEVS_BROKER_PORT"
    ENV_BROKER_USERNAME = "DEVS_BROKER_USERNAME"
    ENV_BROKER_PASSWORD = "DEVS_BROKER_PASSWORD"
    
    def __init__(self, message_standard: str = "ms4me", auto_detect: bool = True):
        """
        Initialize auto-configuration.
        
        Args:
            message_standard: Message standard to use (default: ms4me)
            auto_detect: Enable broker auto-detection
        """
        self.message_standard = message_standard
        self.auto_detect = auto_detect
    
    def configure(self) -> SimulationConfig:
        """
        Auto-configure simulation.
        
        Returns:
            SimulationConfig with complete settings
            
        Raises:
            RuntimeError: If no broker can be configured
        """
        # Get message standard from environment or use default
        standard = os.environ.get(self.ENV_STANDARD, self.message_standard)
        
        # Get broker configuration
        broker_type = os.environ.get(self.ENV_BROKER_TYPE)
        broker_host = os.environ.get(self.ENV_BROKER_HOST)
        broker_port = os.environ.get(self.ENV_BROKER_PORT)
        username = os.environ.get(self.ENV_BROKER_USERNAME)
        password = os.environ.get(self.ENV_BROKER_PASSWORD)
        
        # If not all broker settings provided, try auto-detection
        if not all([broker_type, broker_host, broker_port]) and self.auto_detect:
            from DEVSKernel.BrokerDEVS.standard_registry import (
                BrokerDetector,
                BrokerType,
            )
            
            detector = BrokerDetector()
            detected_brokers = detector.detect_all()
            
            if detected_brokers:
                best = self._select_best_broker(detected_brokers)
                broker_type = best.broker_type.value
                broker_host = best.host
                broker_port = best.port
                logger.info("Auto-detected broker: %s at %s:%d",
                           broker_type, broker_host, broker_port)
            else:
                logger.warning("No brokers detected, using defaults")
                broker_type, broker_host, broker_port = self._get_defaults()
        elif not all([broker_type, broker_host, broker_port]):
            # No env vars and auto-detect disabled
            broker_type, broker_host, broker_port = self._get_defaults()
        
        # Convert port to int
        try:
            broker_port = int(broker_port)
        except (ValueError, TypeError):
            broker_port = self._get_default_port(broker_type)
        
        config = SimulationConfig(
            broker_type=broker_type,
            broker_host=broker_host,
            broker_port=broker_port,
            message_standard=standard,
            username=username,
            password=password,
        )
        
        logger.info("Configured simulation: %s", config)
        return config
    
    @staticmethod
    def _select_best_broker(brokers) -> Any:
        """Select best available broker (prefer Kafka > MQTT > others)."""
        priority = {
            'kafka': 4,
            'mqtt': 3,
            'rabbitmq': 2,
            'redis': 1,
        }
        
        return max(
            brokers,
            key=lambda b: priority.get(b.broker_type.value, 0),
        )
    
    @staticmethod
    def _get_defaults() -> tuple:
        """Get default broker settings."""
        return ('kafka', 'localhost', 9092)
    
    @staticmethod
    def _get_default_port(broker_type: str) -> int:
        """Get default port for broker type."""
        defaults = {
            'kafka': 9092,
            'mqtt': 1883,
            'rabbitmq': 5672,
            'redis': 6379,
        }
        return defaults.get(broker_type, 9092)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CONVENIENCE FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def auto_configure_simulation(
    standard: str = "ms4me",
    broker: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    auto_detect: bool = True,
) -> SimulationConfig:
    """
    Auto-configure simulation with sensible defaults.
    
    Args:
        standard: Message standard to use (default: ms4me)
        broker: Broker type (kafka, mqtt, rabbitmq)
        host: Broker host
        port: Broker port
        auto_detect: Enable auto-detection if not all params provided
        
    Returns:
        SimulationConfig
        
    Example:
        # Auto-detect everything
        config = auto_configure_simulation()
        
        # Specify broker, auto-detect host
        config = auto_configure_simulation(broker='mqtt')
        
        # Fully manual
        config = auto_configure_simulation(
            standard='ms4me',
            broker='mqtt',
            host='broker.example.com',
            port=1883
        )
    """
    # Set environment variables if provided
    if broker:
        os.environ['DEVS_BROKER_TYPE'] = broker
    if host:
        os.environ['DEVS_BROKER_HOST'] = host
    if port:
        os.environ['DEVS_BROKER_PORT'] = str(port)
    
    auto_config = AutoSimulationConfig(standard, auto_detect=auto_detect)
    return auto_config.configure()
