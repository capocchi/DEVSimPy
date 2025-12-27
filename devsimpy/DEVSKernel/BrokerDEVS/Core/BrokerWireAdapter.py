# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# BrokerWireAdapter.py ---
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
# This module provides abstract wire adapters for serializing/deserializing
# broker messages. Wire adapters handle the conversion between:
#   - Internal Python message objects
#   - Wire format (JSON, MessagePack, Protocol Buffers, etc.)
#   - Broker-specific formats (Kafka bytes, MQTT payload, RabbitMQ frames, etc.)
#
# Supports multiple serialization formats for different use cases:
#   - JSON: Human-readable, widely compatible
#   - MessagePack: Compact binary format
#   - CloudEvents: Standard event format
#   - Custom: User-defined serialization
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol, Optional, Type
import json
import logging

from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import (
    BaseMessage,
    SimTime,
    PortValue,
)

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# ABSTRACT WIRE ADAPTER BASE CLASS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerWireAdapter(ABC):
    """
    Abstract base class for message serialization adapters.
    
    Handles conversion between internal message objects and wire formats
    suitable for transmission over different brokers.
    """

    @abstractmethod
    def to_wire(self, msg: BaseMessage) -> bytes:
        """
        Serialize a message object to wire format (bytes).
        
        Args:
            msg: The BaseMessage object to serialize
            
        Returns:
            Serialized message as bytes
        """
        ...

    @abstractmethod
    def from_wire(self, data: bytes) -> BaseMessage:
        """
        Deserialize wire format (bytes) to message object.
        
        Args:
            data: Serialized message bytes
            
        Returns:
            Deserialized BaseMessage object
        """
        ...

    @abstractmethod
    def to_dict(self, msg: BaseMessage) -> Dict[str, Any]:
        """
        Serialize message to dictionary (intermediate format).
        
        Args:
            msg: The BaseMessage object to serialize
            
        Returns:
            Message as dictionary
        """
        ...

    @abstractmethod
    def from_dict(self, d: Dict[str, Any]) -> BaseMessage:
        """
        Deserialize dictionary to message object.
        
        Args:
            d: Dictionary representation of message
            
        Returns:
            Deserialized BaseMessage object
        """
        ...

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the name of this wire format (e.g., 'json', 'msgpack')."""
        ...


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# JSON WIRE ADAPTER (DEFAULT)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class JsonWireAdapter(BrokerWireAdapter):
    """
    Wire adapter using JSON serialization.
    
    Advantages:
    - Human-readable
    - Language-independent
    - Built-in Python support
    
    Disadvantages:
    - Larger payload size
    - Slower serialization than binary formats
    """

    def __init__(self, indent: Optional[int] = None, sort_keys: bool = False):
        """
        Initialize JSON adapter.
        
        Args:
            indent: JSON indentation level (None for compact, 2/4 for pretty)
            sort_keys: Whether to sort dictionary keys
        """
        self.indent = indent
        self.sort_keys = sort_keys

    def to_wire(self, msg: BaseMessage) -> bytes:
        """Serialize message to JSON bytes."""
        msg_dict = self.to_dict(msg)
        json_str = json.dumps(msg_dict, indent=self.indent, sort_keys=self.sort_keys)
        return json_str.encode("utf-8")

    def from_wire(self, data: bytes) -> BaseMessage:
        """Deserialize JSON bytes to message."""
        json_str = data.decode("utf-8")
        msg_dict = json.loads(json_str)
        return self.from_dict(msg_dict)

    def to_dict(self, msg: BaseMessage) -> Dict[str, Any]:
        """Serialize message to dictionary."""
        return msg.to_dict()

    def from_dict(self, d: Dict[str, Any]) -> BaseMessage:
        """Deserialize dictionary to message."""
        return BaseMessage.from_dict(d)

    @property
    def format_name(self) -> str:
        return "json"


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MESSAGEPACK WIRE ADAPTER (COMPACT BINARY)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class MessagePackWireAdapter(BrokerWireAdapter):
    """
    Wire adapter using MessagePack serialization.
    
    Advantages:
    - Compact binary format
    - Fast serialization/deserialization
    - ~30% smaller than JSON
    
    Disadvantages:
    - Requires msgpack library
    - Not human-readable
    
    Requires: pip install msgpack
    """

    def __init__(self, use_bin_type: bool = True):
        """
        Initialize MessagePack adapter.
        
        Args:
            use_bin_type: Whether to use bin type for bytes (Python 3 compatibility)
        """
        try:
            import msgpack
            self.msgpack = msgpack
        except ImportError:
            raise ImportError(
                "MessagePack adapter requires 'msgpack' library. "
                "Install with: pip install msgpack"
            )
        self.use_bin_type = use_bin_type

    def to_wire(self, msg: BaseMessage) -> bytes:
        """Serialize message to MessagePack bytes."""
        msg_dict = self.to_dict(msg)
        return self.msgpack.packb(msg_dict, use_bin_type=self.use_bin_type)

    def from_wire(self, data: bytes) -> BaseMessage:
        """Deserialize MessagePack bytes to message."""
        msg_dict = self.msgpack.unpackb(data, raw=False)
        return self.from_dict(msg_dict)

    def to_dict(self, msg: BaseMessage) -> Dict[str, Any]:
        """Serialize message to dictionary."""
        return msg.to_dict()

    def from_dict(self, d: Dict[str, Any]) -> BaseMessage:
        """Deserialize dictionary to message."""
        return BaseMessage.from_dict(d)

    @property
    def format_name(self) -> str:
        return "msgpack"


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLOUDEVENTS WIRE ADAPTER (STANDARD FORMAT)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class CloudEventsWireAdapter(BrokerWireAdapter):
    """
    Wire adapter using CloudEvents standard format.
    
    CloudEvents is a CNCF standard for describing events in a common way.
    Useful when integrating with event-driven systems.
    
    Reference: https://cloudevents.io/
    
    Advantages:
    - Industry standard format
    - Better integration with cloud platforms
    - Rich metadata support
    
    Disadvantages:
    - Additional overhead
    - Slightly larger payload
    
    Requires: pip install cloudevents
    """

    def __init__(
        self,
        source: str = "devsimpy/broker",
        subject_prefix: str = "simulation",
    ):
        """
        Initialize CloudEvents adapter.
        
        Args:
            source: CloudEvents source identifier
            subject_prefix: Prefix for CloudEvents subject
        """
        try:
            from cloudevents.http import CloudEvent
            self.CloudEvent = CloudEvent
        except ImportError:
            raise ImportError(
                "CloudEvents adapter requires 'cloudevents' library. "
                "Install with: pip install cloudevents"
            )
        self.source = source
        self.subject_prefix = subject_prefix

    def to_wire(self, msg: BaseMessage) -> bytes:
        """Serialize message as CloudEvent JSON."""
        event = self._create_cloud_event(msg)
        return json.dumps(event).encode("utf-8")

    def from_wire(self, data: bytes) -> BaseMessage:
        """Deserialize CloudEvent JSON to message."""
        event_dict = json.loads(data.decode("utf-8"))
        return self._extract_message_from_event(event_dict)

    def to_dict(self, msg: BaseMessage) -> Dict[str, Any]:
        """Serialize message to CloudEvent dictionary."""
        return self._create_cloud_event(msg)

    def from_dict(self, d: Dict[str, Any]) -> BaseMessage:
        """Deserialize CloudEvent dictionary to message."""
        return self._extract_message_from_event(d)

    def _create_cloud_event(self, msg: BaseMessage) -> Dict[str, Any]:
        """Create CloudEvent wrapper for message."""
        msg_dict = msg.to_dict()
        devs_type = msg_dict.get("devsType", "unknown")

        # Extract simplified type for CloudEvents type field
        event_type = f"com.devsimpy.{devs_type.split('.')[-1].lower()}"

        return {
            "specversion": "1.0",
            "type": event_type,
            "source": self.source,
            "subject": f"{self.subject_prefix}/{devs_type}",
            "datacontenttype": "application/json",
            "data": msg_dict,
        }

    def _extract_message_from_event(self, event_dict: Dict[str, Any]) -> BaseMessage:
        """Extract message from CloudEvent wrapper."""
        if "data" not in event_dict:
            raise ValueError("CloudEvent missing 'data' field")
        return BaseMessage.from_dict(event_dict["data"])

    @property
    def format_name(self) -> str:
        return "cloudevents"


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# PROTOBUF WIRE ADAPTER (FOR FUTURE USE)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class ProtobufWireAdapter(BrokerWireAdapter):
    """
    Wire adapter using Protocol Buffers serialization.
    
    Advantages:
    - Very compact binary format
    - Strong schema definition
    - Excellent performance
    
    Disadvantages:
    - Requires .proto schema definition
    - More setup complexity
    - Not human-readable
    
    Requires: pip install protobuf
    
    Note: Implementation requires pre-generated protobuf message classes.
    """

    def __init__(self):
        """Initialize Protobuf adapter."""
        try:
            from google.protobuf import json_format
            self.json_format = json_format
        except ImportError:
            raise ImportError(
                "Protobuf adapter requires 'protobuf' library. "
                "Install with: pip install protobuf"
            )
        self._message_classes = {}

    def register_message_class(self, devs_type: str, proto_class):
        """Register a protobuf message class for a devsType."""
        self._message_classes[devs_type] = proto_class

    def to_wire(self, msg: BaseMessage) -> bytes:
        """Serialize message to protobuf bytes."""
        devs_type = msg.devsType
        proto_class = self._message_classes.get(devs_type)

        if proto_class is None:
            raise ValueError(
                f"No protobuf class registered for {devs_type}. "
                f"Available: {list(self._message_classes.keys())}"
            )

        msg_dict = msg.to_dict()
        proto_msg = proto_class()
        self.json_format.ParseDict(msg_dict, proto_msg)
        return proto_msg.SerializeToString()

    def from_wire(self, data: bytes) -> BaseMessage:
        """Deserialize protobuf bytes to message."""
        # This would require knowing the message type from the data
        # Implementation depends on your protobuf schema
        raise NotImplementedError(
            "Protobuf deserialization requires message type metadata. "
            "Consider using a wrapper format."
        )

    def to_dict(self, msg: BaseMessage) -> Dict[str, Any]:
        """Serialize message to dictionary."""
        return msg.to_dict()

    def from_dict(self, d: Dict[str, Any]) -> BaseMessage:
        """Deserialize dictionary to message."""
        return BaseMessage.from_dict(d)

    @property
    def format_name(self) -> str:
        return "protobuf"


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# WIRE ADAPTER FACTORY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class WireAdapterFactory:
    """Factory for creating wire adapters."""

    _ADAPTERS: Dict[str, Type[BrokerWireAdapter]] = {
        "json": JsonWireAdapter,
        "msgpack": MessagePackWireAdapter,
        "cloudevents": CloudEventsWireAdapter,
        "protobuf": ProtobufWireAdapter,
    }

    @classmethod
    def create(cls, format_name: str, **kwargs) -> BrokerWireAdapter:
        """
        Create a wire adapter by format name.
        
        Args:
            format_name: One of 'json', 'msgpack', 'cloudevents', 'protobuf'
            **kwargs: Arguments passed to adapter constructor
            
        Returns:
            Configured BrokerWireAdapter instance
        """
        adapter_class = cls._ADAPTERS.get(format_name.lower())
        if adapter_class is None:
            available = ", ".join(cls._ADAPTERS.keys())
            raise ValueError(
                f"Unknown wire format: {format_name}. "
                f"Available: {available}"
            )
        return adapter_class(**kwargs)

    @classmethod
    def register(cls, format_name: str, adapter_class: Type[BrokerWireAdapter]):
        """Register a custom wire adapter."""
        cls._ADAPTERS[format_name.lower()] = adapter_class

    @classmethod
    def get_available_formats(cls) -> list:
        """Get list of available wire adapter formats."""
        return list(cls._ADAPTERS.keys())

    @classmethod
    def get_default(cls) -> BrokerWireAdapter:
        """Get the default wire adapter (JSON)."""
        return cls.create("json")


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CONVENIENCE FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def serialize_message(msg: BaseMessage, format_name: str = "json") -> bytes:
    """
    Serialize a message to bytes using specified format.
    
    Args:
        msg: Message to serialize
        format_name: Serialization format
        
    Returns:
        Serialized message bytes
    """
    adapter = WireAdapterFactory.create(format_name)
    return adapter.to_wire(msg)


def deserialize_message(data: bytes, format_name: str = "json") -> BaseMessage:
    """
    Deserialize bytes to a message using specified format.
    
    Args:
        data: Serialized message bytes
        format_name: Serialization format
        
    Returns:
        Deserialized message
    """
    adapter = WireAdapterFactory.create(format_name)
    return adapter.from_wire(data)
