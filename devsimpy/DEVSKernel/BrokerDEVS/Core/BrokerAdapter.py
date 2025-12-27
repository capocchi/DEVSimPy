# BrokerDEVS/Core/BrokerAdapter.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Protocol

class BrokerConsumer(Protocol):
    """Protocol for broker consumer"""
    def subscribe(self, topics: list) -> None: ...
    def poll(self, timeout: float) -> Any: ...
    def close(self) -> None: ...

class BrokerProducer(Protocol):
    """Protocol for broker producer"""
    def produce(self, topic: str, value: bytes, key: str = None) -> None: ...
    def flush(self, timeout: float = None) -> None: ...
    def close(self) -> None: ...

class BrokerAdapter(ABC):
    """Abstract adapter for different message brokers"""
    
    @abstractmethod
    def create_consumer(self, config: Dict[str, Any]) -> BrokerConsumer:
        """Create a consumer instance"""
        ...
    
    @abstractmethod
    def create_producer(self, config: Dict[str, Any]) -> BrokerProducer:
        """Create a producer instance"""
        ...
    
    @abstractmethod
    def extract_message_value(self, message: Any) -> bytes:
        """Extract message value from broker's message format"""
        ...
    
    @abstractmethod
    def get_topic(self, message: Any) -> str:
        """Get topic/channel from message"""
        ...
    
    @abstractmethod
    def has_error(self, message: Any) -> bool:
        """Check if message has error"""
        ...
    
    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Return broker name (kafka, mqtt, rabbitmq)"""
        ...