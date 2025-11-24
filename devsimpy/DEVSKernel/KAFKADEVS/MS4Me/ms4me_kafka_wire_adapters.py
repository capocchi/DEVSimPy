# devs_kafka_wire_adapters.py
from __future__ import annotations
from typing import Any, Dict

from DEVSKernel.KafkaDEVS.MS4Me.ms4me_kafka_messages import BaseMessage

class StandardWireAdapter:
    """
    MS4me msg adaptator.
    """

    @staticmethod
    def to_wire(msg: BaseMessage) -> Dict[str, Any]:
        """
        Transform BaseMessage (InitSim, NextTime, ...) to dict in order to be sended on Kafka.
        """
        return msg.to_dict()

    @staticmethod
    def from_wire(d: Dict[str, Any]) -> BaseMessage:
        """
        Transform  a dict (Kafka value) in BaseMessage.
        """
        return BaseMessage.from_dict(d)
