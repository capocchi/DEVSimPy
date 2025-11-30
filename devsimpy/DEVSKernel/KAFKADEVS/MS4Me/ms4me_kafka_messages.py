# ms4me_kafka_messages.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import sys
import numpy as np
# ---------- Types de base ----------

@dataclass
class SimTime:
    timeType: str = "devs.msg.time.DoubleSimTime"
    t: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        if self.t == float("inf"): 
            self.t = np.finfo(np.float64).max
        return {
            "timeType": self.timeType,
            "t": self.t,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SimTime":
        time =float(d.get("t", 0.0))
        if time == np.finfo(np.float64).max:
            time = float("inf")
        return SimTime(
            timeType=d.get("timeType", "devs.msg.time.DoubleSimTime"),
            t=time,
        )


@dataclass
class PortValue:
    value: Any
    portIdentifier: str
    portType: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "portIdentifier": self.portIdentifier,
            "portType": self.portType,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PortValue":
        return PortValue(
            value=d.get("value"),
            portIdentifier=d.get("portIdentifier", ""),
            portType=d.get("portType", "java.lang.Object"),
        )


# ---------- Classe racine des messages ----------

@dataclass
class BaseMessage:
    devsType: str

    def to_dict(self) -> Dict[str, Any]:
        """Doit être redéfini par les sous-classes."""
        raise NotImplementedError

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "BaseMessage":
        devs_type = d.get("devsType")
        if devs_type == "devs.msg.InitSim":
            return InitSim.from_dict(d)
        if devs_type == "devs.msg.ExecuteTransition":
            return ExecuteTransition.from_dict(d)
        if devs_type == "devs.msg.ModelDone":
            return ModelDone.from_dict(d)
        if devs_type == "devs.msg.ModelOutputMessage":
            return ModelOutputMessage.from_dict(d)
        if devs_type == "devs.msg.NextTime":
            return NextTime.from_dict(d)
        if devs_type == "devs.msg.SendOutput":
            return SendOutput.from_dict(d)
        if devs_type == "devs.msg.SimulationDone":
            return SimulationDone.from_dict(d)
        if devs_type == "devs.msg.TransitionDone":
            return TransitionDone.from_dict(d)
        raise ValueError(f"Unknown devsType: {devs_type}")


# ---------- Messages spécifiques (d’après example-messages.json) ----------

@dataclass
class InitSim(BaseMessage):
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
    time: SimTime
    portValueList: List[PortValue]

    def __init__(self, time: SimTime, portValueList: Optional[List[PortValue]] = None):
        super().__init__("devs.msg.ExecuteTransition")
        self.time = time
        self.portValueList = portValueList or []

    def is_internal(self) -> bool:
        return len(self.portValueList) == 0
    
    def is_external(self) -> bool:
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
    time: SimTime
    nextTime: SimTime
    sender: str

    def __init__(self, time: SimTime, nextTime: SimTime, sender: str):
        super().__init__("devs.msg.TransitionDone")
        self.time = time
        self.nextTime = nextTime
        self.sender = sender

    def to_dict(self) -> Dict[str, Any]:
        return {
            "devsType": self.devsType,
            "time": self.time.to_dict(),
            "nextTime": self.nextTime.to_dict(),
            "sender": self.sender,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TransitionDone":
        return TransitionDone(
            time=SimTime.from_dict(d.get("time", {})),
            nextTime=SimTime.from_dict(d.get("nextTime", {})),
            sender=d.get("sender", ""),
        )
