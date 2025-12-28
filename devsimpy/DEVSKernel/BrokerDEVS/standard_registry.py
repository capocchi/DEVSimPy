# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# standard_registry.py ---
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
# Registry system for message standards and their worker implementations.
# Provides extensible factory pattern for creating workers with any
# combination of message standard + message broker.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import socket
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional, Type, Any, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MESSAGE STANDARD DEFINITIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MessageStandard(Enum):
    """Available message standards for distributed DEVS simulation."""
    
    MS4ME = "ms4me"
    GENERIC = "generic"
    # Add more standards here
    # YOUR_STANDARD = "yourstandard"


class BrokerType(Enum):
    """Supported message broker types."""
    
    KAFKA = "kafka"
    MQTT = "mqtt"
    RABBITMQ = "rabbitmq"
    REDIS = "redis"


class BrokerStatus(Enum):
    """Broker connectivity status."""
    
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNTESTED = "untested"
    ERROR = "error"


@dataclass
class BrokerInfo:
    """Information about a detected broker."""
    
    broker_type: BrokerType
    host: str
    port: int
    status: BrokerStatus
    error: Optional[str] = None
    extras: Dict[str, str] = field(default_factory=dict)
    
    @property
    def address(self) -> str:
        """Get broker address."""
        return f"{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "type": self.broker_type.value,
            "host": self.host,
            "port": str(self.port),
            "status": self.status.value,
            "address": self.address,
            "error": self.error or "",
        }


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# BROKER AUTO-DETECTION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerDetector:
    """Auto-detect available message brokers."""
    
    # Default broker addresses
    DEFAULT_ADDRESSES = {
        BrokerType.KAFKA: [
            ("localhost", 9092),
            ("kafka", 9092),
            ("127.0.0.1", 9092),
        ],
        BrokerType.MQTT: [
            ("localhost", 1883),
            ("mqtt", 1883),
            ("127.0.0.1", 1883),
        ],
        BrokerType.RABBITMQ: [
            ("localhost", 5672),
            ("rabbitmq", 5672),
            ("127.0.0.1", 5672),
        ],
        BrokerType.REDIS: [
            ("localhost", 6379),
            ("redis", 6379),
            ("127.0.0.1", 6379),
        ],
    }
    
    def __init__(self, timeout: float = 2.0):
        """
        Initialize broker detector.
        
        Args:
            timeout: Connection timeout in seconds
        """
        self.timeout = timeout
        self.detected_brokers: List[BrokerInfo] = []
    
    def detect_all(self) -> List[BrokerInfo]:
        """
        Detect all available brokers.
        
        Returns:
            List of detected BrokerInfo objects
        """
        self.detected_brokers = []
        
        # Check each broker type
        for broker_type in BrokerType:
            brokers = self._detect_broker_type(broker_type)
            self.detected_brokers.extend(brokers)
        
        logger.info("Detected %d brokers", len(self.detected_brokers))
        return self.detected_brokers
    
    def _detect_broker_type(self, broker_type: BrokerType) -> List[BrokerInfo]:
        """
        Detect specific broker type.
        
        Args:
            broker_type: Type to detect
            
        Returns:
            List of detected brokers of this type
        """
        brokers = []
        addresses = self.DEFAULT_ADDRESSES.get(broker_type, [])
        
        for host, port in addresses:
            info = self._test_broker_connection(broker_type, host, port)
            if info:
                brokers.append(info)
                # Only return first available for each type
                return [info]
        
        return brokers
    
    def _test_broker_connection(
        self,
        broker_type: BrokerType,
        host: str,
        port: int,
    ) -> Optional[BrokerInfo]:
        """
        Test connection to a broker.
        
        Args:
            broker_type: Type of broker
            host: Broker hostname/IP
            port: Broker port
            
        Returns:
            BrokerInfo if available, None otherwise
        """
        try:
            # Quick socket test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                info = BrokerInfo(
                    broker_type=broker_type,
                    host=host,
                    port=port,
                    status=BrokerStatus.AVAILABLE,
                )
                logger.debug("Found %s broker at %s:%d", broker_type.value, host, port)
                return info
        
        except Exception as e:
            logger.debug("Error testing %s:%d: %s", host, port, e)
        
        return None
    
    def get_broker_by_type(self, broker_type: BrokerType) -> Optional[BrokerInfo]:
        """
        Get detected broker by type.
        
        Args:
            broker_type: Type to find
            
        Returns:
            BrokerInfo if found, None otherwise
        """
        for broker in self.detected_brokers:
            if broker.broker_type == broker_type:
                return broker
        return None
    
    def is_broker_available(self, broker_type: BrokerType) -> bool:
        """
        Check if specific broker type is available.
        
        Args:
            broker_type: Type to check
            
        Returns:
            True if available
        """
        broker = self.get_broker_by_type(broker_type)
        return broker is not None and broker.status == BrokerStatus.AVAILABLE


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# BASE WORKER CLASS FOR STANDARDS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class StandardWorkerBase(ABC):
    """
    Base class for all message standard workers.
    
    Provides common interface for all standard implementations across
    different brokers (Kafka, MQTT, RabbitMQ, etc.).
    """
    
    def __init__(self, model_name: str, model, **kwargs):
        """
        Initialize standard worker.
        
        Args:
            model_name: Name/identifier of the DEVS model
            model: The atomic DEVS model instance
            **kwargs: Broker-specific configuration
        """
        self.model_name = model_name
        self.model = model
        self.kwargs = kwargs
    
    @abstractmethod
    def connect(self):
        """Establish connection to message broker."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection to message broker."""
        pass
    
    @abstractmethod
    def send_message(self, topic: str, message: Any) -> bool:
        """
        Send a message on the specified topic.
        
        Args:
            topic: Destination topic
            message: Message to send
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def receive_message(self, topic: str, timeout: float = 1.0) -> Optional[Any]:
        """
        Receive a message from the specified topic.
        
        Args:
            topic: Source topic
            timeout: Timeout in seconds
            
        Returns:
            Message if received, None if timeout
        """
        pass


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# STANDARD REGISTRY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class StandardRegistry:
    """
    Registry for message standards and their broker-specific workers.
    
    Allows registration of new message standards and their worker
    implementations for different brokers without modifying core code.
    
    Example:
        # Register a new standard
        StandardRegistry.register_standard(
            MessageStandard.MY_STANDARD,
            {
                BrokerType.MQTT: MyStandardMqttWorker,
                BrokerType.KAFKA: MyStandardKafkaWorker,
            }
        )
        
        # Create worker
        worker = StandardRegistry.create_worker(
            MessageStandard.MY_STANDARD,
            BrokerType.MQTT,
            'ModelName', model_instance,
            broker_host='localhost'
        )
    """
    
    # Registry: standard -> {broker -> worker_class}
    _standards: Dict[MessageStandard, Dict[BrokerType, Type[StandardWorkerBase]]] = {}
    
    @classmethod
    def register_standard(
        cls,
        standard: MessageStandard,
        workers: Dict[BrokerType, Type[StandardWorkerBase]],
    ) -> None:
        """
        Register a message standard with its broker-specific workers.
        
        Args:
            standard: The message standard to register
            workers: Dictionary mapping BrokerType to worker class
            
        Example:
            StandardRegistry.register_standard(
                MessageStandard.MS4ME,
                {
                    BrokerType.KAFKA: MS4MeKafkaWorker,
                    BrokerType.MQTT: MS4MeMqttWorker,
                }
            )
        """
        cls._standards[standard] = workers
        logger.info("Registered message standard: %s with %d brokers",
                   standard.value, len(workers))
    
    @classmethod
    def register_worker(
        cls,
        standard: MessageStandard,
        broker: BrokerType,
        worker_class: Type[StandardWorkerBase],
    ) -> None:
        """
        Register a worker for a specific standard+broker combination.
        
        Args:
            standard: The message standard
            broker: The broker type
            worker_class: The worker class to register
        """
        if standard not in cls._standards:
            cls._standards[standard] = {}
        
        cls._standards[standard][broker] = worker_class
        logger.info("Registered worker for %s + %s: %s",
                   standard.value, broker.value, worker_class.__name__)
    
    @classmethod
    def get_worker_class(
        cls,
        standard: MessageStandard,
        broker: BrokerType,
    ) -> Optional[Type[StandardWorkerBase]]:
        """
        Get worker class for a standard+broker combination.
        
        Args:
            standard: The message standard
            broker: The broker type
            
        Returns:
            Worker class if registered, None otherwise
        """
        if standard not in cls._standards:
            logger.warning("Message standard not registered: %s", standard.value)
            return None
        
        worker = cls._standards[standard].get(broker)
        if worker is None:
            logger.warning("No worker registered for %s + %s",
                          standard.value, broker.value)
        return worker
    
    @classmethod
    def is_supported(cls, standard: MessageStandard, broker: BrokerType) -> bool:
        """
        Check if a standard+broker combination is supported.
        
        Args:
            standard: The message standard
            broker: The broker type
            
        Returns:
            True if supported
        """
        return cls.get_worker_class(standard, broker) is not None
    
    @classmethod
    def list_standards(cls) -> list:
        """Get list of registered standards."""
        return list(cls._standards.keys())
    
    @classmethod
    def list_brokers_for_standard(cls, standard: MessageStandard) -> list:
        """Get list of supported brokers for a standard."""
        if standard not in cls._standards:
            return []
        return list(cls._standards[standard].keys())
    
    @classmethod
    def list_registered_standards(cls) -> list:
        """Get list of registered standard names."""
        return [s.value for s in cls._standards.keys()]
    
    @classmethod
    def list_supported_brokers(cls, standard: str) -> list:
        """
        Get list of supported brokers for a given standard string.
        
        Args:
            standard: Standard name (e.g., 'ms4me', 'yourstandard')
            
        Returns:
            List of broker type strings supported by this standard
        """
        try:
            enum_standard = MessageStandard(standard)
            brokers = cls.list_brokers_for_standard(enum_standard)
            return [b.value for b in brokers]
        except ValueError:
            logger.warning("Unknown standard: %s", standard)
            return []
    
    @classmethod
    def create_worker(
        cls,
        standard: MessageStandard,
        broker: BrokerType,
        model_name: str,
        model: Any,
        **kwargs
    ) -> Optional[StandardWorkerBase]:
        """
        Create a worker instance for a standard+broker combination.
        
        Args:
            standard: The message standard
            broker: The broker type
            model_name: Name of the DEVS model
            model: The DEVS model instance
            **kwargs: Broker-specific configuration (host, port, username, password, etc.)
            
        Returns:
            Worker instance if successful, None if combination not supported
            
        Raises:
            ValueError: If standard or broker not registered
            
        Example:
            worker = StandardRegistry.create_worker(
                MessageStandard.MS4ME,
                BrokerType.MQTT,
                'MyModel', model_instance,
                broker_host='localhost',
                broker_port=1883,
                username='user',
                password='pass'
            )
        """
        worker_class = cls.get_worker_class(standard, broker)
        
        if worker_class is None:
            raise ValueError(
                f"Unsupported combination: {standard.value} + {broker.value}"
            )
        
        try:
            worker = worker_class(model_name, model, **kwargs)
            logger.info("Created worker: %s (%s + %s)",
                       model_name, standard.value, broker.value)
            return worker
        except Exception as e:
            logger.error("Failed to create worker: %s", e, exc_info=True)
            raise


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# REGISTRATION OF DEFAULT STANDARDS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def register_builtin_standards():
    """Register built-in message standards and their workers."""
    
    try:
        from DEVSKernel.BrokerDEVS.MS4Me.MS4MeKafkaWorker import MS4MeKafkaWorker
        from DEVSKernel.BrokerDEVS.MS4Me.MS4MeMqttWorker import MS4MeMqttWorker
        
        StandardRegistry.register_standard(
            MessageStandard.MS4ME,
            {
                BrokerType.KAFKA: MS4MeKafkaWorker,
                BrokerType.MQTT: MS4MeMqttWorker,
            }
        )
        logger.info("Registered built-in MS4Me standard")
    except ImportError as e:
        logger.warning("Failed to register MS4Me standard: %s", e)


# Auto-register built-in standards on module load
register_builtin_standards()
