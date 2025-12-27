# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# BrokerMessageTypes.py ---
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
# This module provides generic message types for broker-based DEVS simulations.
# Messages are designed to be agnostic to the underlying broker (Kafka, MQTT, RabbitMQ, etc.)
# and support serialization/deserialization across multiple formats.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol
import numpy as np
import json


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# BASE MESSAGE TYPES
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


@dataclass
class SimTime:
    """
    Represents simulation time in a broker-agnostic format.
    Handles serialization of infinite time values across different formats.
    """
    timeType: str = "devs.msg.time.DoubleSimTime"
    t: float = 0.0

    def __init__(self, t: float = 0.0, timeType: str = "devs.msg.time.DoubleSimTime"):
        """Initialize SimTime with time value."""
        self.t = t
        self.timeType = timeType

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, replacing inf with max float."""
        t_value = self.t
        if t_value == float("inf"):
            t_value = np.finfo(np.float64).max
        return {
            "timeType": self.timeType,
            "t": t_value,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SimTime":
        """Create from dictionary, restoring inf from max float."""
        t_value = float(d.get("t", 0.0))
        if t_value == np.finfo(np.float64).max:
            t_value = float("inf")
        return SimTime(
            timeType=d.get("timeType", "devs.msg.time.DoubleSimTime"),
            t=t_value,
        )

    def __eq__(self, other):
        if not isinstance(other, SimTime):
            return False
        return self.t == other.t

    def __lt__(self, other):
        if not isinstance(other, SimTime):
            return NotImplemented
        return self.t < other.t

    def __le__(self, other):
        if not isinstance(other, SimTime):
            return NotImplemented
        return self.t <= other.t

    def __gt__(self, other):
        if not isinstance(other, SimTime):
            return NotImplemented
        return self.t > other.t

    def __ge__(self, other):
        if not isinstance(other, SimTime):
            return NotImplemented
        return self.t >= other.t


@dataclass
class PortValue:
    """
    Represents a value on a DEVS port.
    Contains the actual value, port identifier, and port type.
    """
    value: Any
    portIdentifier: str
    portType: str = "java.lang.Object"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "value": self.value,
            "portIdentifier": self.portIdentifier,
            "portType": self.portType,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PortValue":
        """Create from dictionary."""
        return PortValue(
            value=d.get("value"),
            portIdentifier=d.get("portIdentifier", ""),
            portType=d.get("portType", "java.lang.Object"),
        )

    def __repr__(self) -> str:
        return f"PortValue(port={self.portIdentifier}, value={self.value})"


class BaseMessageProtocol(Protocol):
    """Protocol defining the interface for broker messages."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize message to dictionary."""
        ...

    def to_json(self) -> str:
        """Serialize message to JSON string."""
        ...

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "BaseMessageProtocol":
        """Deserialize message from dictionary."""
        ...

    @staticmethod
    def from_json(json_str: str) -> "BaseMessageProtocol":
        """Deserialize message from JSON string."""
        ...


class BaseMessage:
    """
    Abstract base class for all broker messages.
    Supports polymorphic deserialization based on devsType field.
    """
    devsType: str

    def __init__(self, devsType: str):
        """Initialize base message with devsType."""
        self.devsType = devsType

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary - must be implemented by subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__}.to_dict() not implemented")

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    def to_bytes(self) -> bytes:
        """Serialize to UTF-8 bytes."""
        return self.to_json().encode("utf-8")

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "BaseMessage":
        """
        Factory method for polymorphic deserialization.
        Routes to appropriate subclass based on devsType.
        """
        devs_type = d.get("devsType")

        # Dispatch to appropriate message type
        message_types = {
            "devs.msg.InitSim": InitSim.from_dict,
            "devs.msg.ExecuteTransition": ExecuteTransition.from_dict,
            "devs.msg.ModelDone": ModelDone.from_dict,
            "devs.msg.ModelOutputMessage": ModelOutputMessage.from_dict,
            "devs.msg.NextTime": NextTime.from_dict,
            "devs.msg.SendOutput": SendOutput.from_dict,
            "devs.msg.SimulationDone": SimulationDone.from_dict,
            "devs.msg.TransitionDone": TransitionDone.from_dict,
        }

        factory = message_types.get(devs_type)
        if factory is None:
            raise ValueError(f"Unknown devsType: {devs_type}")

        return factory(d)

    @staticmethod
    def from_json(json_str: str) -> "BaseMessage":
        """Deserialize from JSON string."""
        d = json.loads(json_str)
        return BaseMessage.from_dict(d)

    @staticmethod
    def from_bytes(data: bytes) -> "BaseMessage":
        """Deserialize from UTF-8 bytes."""
        return BaseMessage.from_json(data.decode("utf-8"))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.devsType})"


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# SPECIFIC MESSAGE TYPES
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


@dataclass
class InitSim(BaseMessage):
    """Initialize simulation message."""
    time: SimTime

    def __init__(self, time: SimTime):
        super().__init__("devs.msg.InitSim")
        self.time = time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "devsType": self.devsType,
            "time": self.time.to_dict(),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "InitSim":
        return InitSim(
            time=SimTime.from_dict(d.get("time", {}))
        )


@dataclass
class ExecuteTransition(BaseMessage):
    """Execute state transition message."""
    time: SimTime
    portValueList: List[PortValue]

    def __init__(self, time: SimTime, portValueList: Optional[List[PortValue]] = None):
        super().__init__("devs.msg.ExecuteTransition")
        self.time = time
        self.portValueList = portValueList or []

    def is_internal(self) -> bool:
        """Check if this is an internal transition (no inputs)."""
        return len(self.portValueList) == 0

    def is_external(self) -> bool:
        """Check if this is an external transition (has inputs)."""
        return len(self.portValueList) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "devsType": self.devsType,
            "time": self.time.to_dict(),
            "modelInputsOption": {
                "portValueList": [pv.to_dict() for pv in self.portValueList]
            } if self.portValueList else {},
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ExecuteTransition":
        time = SimTime.from_dict(d.get("time", {}))
        mio = d.get("modelInputsOption", {}) or {}
        pv_list = [
            PortValue.from_dict(pv)
            for pv in mio.get("portValueList", []) or []
        ]
        return ExecuteTransition(time=time, portValueList=pv_list)


@dataclass
class ModelDone(BaseMessage):
    """Model transition execution complete message."""
    time: SimTime
    sender: str

    def __init__(self, time: SimTime, sender: str):
        super().__init__("devs.msg.ModelDone")
        self.time = time
        self.sender = sender

    def to_dict(self) -> Dict[str, Any]:
        return {
            "devsType": self.devsType,
            "time": self.time.to_dict(),
            "sender": self.sender,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ModelDone":
        return ModelDone(
            time=SimTime.from_dict(d.get("time", {})),
            sender=d.get("sender", ""),
        )


@dataclass
class ModelOutputMessage(BaseMessage):
    """Model output message."""
    modelOutput: List[PortValue]
    nextTime: SimTime
    sender: str

    def __init__(
        self,
        modelOutput: Optional[List[PortValue]],
        nextTime: SimTime,
        sender: str,
    ):
        super().__init__("devs.msg.ModelOutputMessage")
        self.modelOutput = modelOutput or []
        self.nextTime = nextTime
        self.sender = sender

    def to_dict(self) -> Dict[str, Any]:
        return {
            "devsType": self.devsType,
            "modelOutput": {
                "portValueList": [pv.to_dict() for pv in self.modelOutput]
            } if self.modelOutput else {},
            "nextTime": self.nextTime.to_dict(),
            "sender": self.sender,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ModelOutputMessage":
        mo = d.get("modelOutput", {}) or {}
        pv_list = [
            PortValue.from_dict(pv)
            for pv in mo.get("portValueList", []) or []
        ]
        return ModelOutputMessage(
            modelOutput=pv_list,
            nextTime=SimTime.from_dict(d.get("nextTime", {})),
            sender=d.get("sender", ""),
        )


@dataclass
class NextTime(BaseMessage):
    """Next event time message."""
    time: SimTime
    sender: str

    def __init__(self, time: SimTime, sender: str):
        super().__init__("devs.msg.NextTime")
        self.time = time
        self.sender = sender

    def to_dict(self) -> Dict[str, Any]:
        return {
            "devsType": self.devsType,
            "time": self.time.to_dict(),
            "sender": self.sender,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "NextTime":
        return NextTime(
            time=SimTime.from_dict(d.get("time", {})),
            sender=d.get("sender", ""),
        )


@dataclass
class SendOutput(BaseMessage):
    """Send output phase message."""
    time: SimTime

    def __init__(self, time: SimTime):
        super().__init__("devs.msg.SendOutput")
        self.time = time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "devsType": self.devsType,
            "time": self.time.to_dict(),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SendOutput":
        return SendOutput(
            time=SimTime.from_dict(d.get("time", {}))
        )


@dataclass
class SimulationDone(BaseMessage):
    """Simulation termination message."""
    time: SimTime

    def __init__(self, time: SimTime):
        super().__init__("devs.msg.SimulationDone")
        self.time = time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "devsType": self.devsType,
            "time": self.time.to_dict(),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SimulationDone":
        return SimulationDone(
            time=SimTime.from_dict(d.get("time", {}))
        )


@dataclass
class TransitionDone(BaseMessage):
    """Transition operation complete message."""
    time: SimTime
    sender: str
    nextTime: Optional['SimTime'] = None

    def __init__(self, time: SimTime, sender: str, nextTime: Optional['SimTime'] = None):
        super().__init__("devs.msg.TransitionDone")
        self.time = time
        self.sender = sender
        self.nextTime = nextTime

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "devsType": self.devsType,
            "time": self.time.to_dict(),
            "sender": self.sender,
        }
        if self.nextTime is not None:
            result["nextTime"] = self.nextTime.to_dict()
        return result

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TransitionDone":
        next_time = None
        if "nextTime" in d:
            next_time = SimTime.from_dict(d.get("nextTime", {}))
        return TransitionDone(
            time=SimTime.from_dict(d.get("time", {})),
            sender=d.get("sender", ""),
            nextTime=next_time,
        )


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MESSAGE TYPE REGISTRY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


# Registry mapping devsType strings to message classes
MESSAGE_REGISTRY = {
    "devs.msg.InitSim": InitSim,
    "devs.msg.ExecuteTransition": ExecuteTransition,
    "devs.msg.ModelDone": ModelDone,
    "devs.msg.ModelOutputMessage": ModelOutputMessage,
    "devs.msg.NextTime": NextTime,
    "devs.msg.SendOutput": SendOutput,
    "devs.msg.SimulationDone": SimulationDone,
    "devs.msg.TransitionDone": TransitionDone,
}


def get_message_class(devs_type: str):
    """Get message class by devsType string."""
    return MESSAGE_REGISTRY.get(devs_type)


def register_message_type(devs_type: str, message_class):
    """Register a new custom message type."""
    MESSAGE_REGISTRY[devs_type] = message_class
