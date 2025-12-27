# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ms4me_mqtt_wire_adapters.py ---
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
# Wire adapters for MS4Me message serialization over MQTT.
# Handles encoding/decoding of DEVS messages for MQTT transport.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import pickle
import json

from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import (
    BaseMessage,
    SimTime,
    InitSim,
    NextTime,
    ExecuteTransition,
    SendOutput,
    ModelOutputMessage,
    ModelDone,
    TransitionDone,
    SimulationDone,
    PortValue,
)

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# ABSTRACT WIRE ADAPTER
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class WireAdapter:
    """Base class for message serialization adapters"""

    def serialize(self, msg: BaseMessage) -> bytes:
        """Serialize a message to bytes"""
        raise NotImplementedError

    def deserialize(self, data: bytes) -> BaseMessage:
        """Deserialize bytes to a message"""
        raise NotImplementedError


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# STANDARD WIRE ADAPTER (Pickle-based)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class StandardWireAdapter(WireAdapter):
    """
    Standard wire adapter using Python pickle serialization.
    
    Features:
    - Full Python object serialization
    - Fast and efficient
    - No schema needed
    - Works with any Python object
    """

    @staticmethod
    def serialize(msg: BaseMessage) -> bytes:
        """Serialize message using pickle"""
        return pickle.dumps(msg)

    @staticmethod
    def deserialize(data: bytes) -> BaseMessage:
        """Deserialize message using pickle"""
        return pickle.loads(data)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# JSON WIRE ADAPTER (for interoperability)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class JsonWireAdapter(WireAdapter):
    """
    JSON-based wire adapter for language/platform interoperability.
    
    Features:
    - Human-readable messages
    - Cross-platform compatibility
    - Language-independent
    - Larger message size
    """

    # Message type registry for deserialization
    MESSAGE_TYPES = {
        'SimTime': SimTime,
        'InitSim': InitSim,
        'NextTime': NextTime,
        'ExecuteTransition': ExecuteTransition,
        'SendOutput': SendOutput,
        'ModelOutputMessage': ModelOutputMessage,
        'ModelDone': ModelDone,
        'TransitionDone': TransitionDone,
        'SimulationDone': SimulationDone,
        'PortValue': PortValue,
    }

    @staticmethod
    def serialize(msg: BaseMessage) -> bytes:
        """Serialize message to JSON"""
        msg_dict = {
            '__type__': type(msg).__name__,
            '__data__': msg.__dict__,
        }
        return json.dumps(msg_dict).encode('utf-8')

    @staticmethod
    def deserialize(data: bytes) -> BaseMessage:
        """Deserialize message from JSON"""
        msg_dict = json.loads(data.decode('utf-8'))
        msg_type_name = msg_dict.get('__type__')
        msg_data = msg_dict.get('__data__', {})

        if msg_type_name not in JsonWireAdapter.MESSAGE_TYPES:
            raise ValueError(f"Unknown message type: {msg_type_name}")

        msg_class = JsonWireAdapter.MESSAGE_TYPES[msg_type_name]
        msg = msg_class.__new__(msg_class)
        msg.__dict__.update(msg_data)

        return msg


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# COMPRESSION ADAPTER (wrapper for any adapter)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class CompressionWireAdapter(WireAdapter):
    """
    Wrapper adapter that compresses messages using gzip.
    
    Can wrap any other adapter for compression benefits:
    - Reduced bandwidth
    - Slower serialization/deserialization
    """

    def __init__(self, inner_adapter: WireAdapter = None):
        """Initialize with optional inner adapter (default: StandardWireAdapter)"""
        self.inner_adapter = inner_adapter or StandardWireAdapter()

    def serialize(self, msg: BaseMessage) -> bytes:
        """Serialize and compress message"""
        import gzip
        serialized = self.inner_adapter.serialize(msg)
        return gzip.compress(serialized)

    def deserialize(self, data: bytes) -> BaseMessage:
        """Decompress and deserialize message"""
        import gzip
        decompressed = gzip.decompress(data)
        return self.inner_adapter.deserialize(decompressed)
