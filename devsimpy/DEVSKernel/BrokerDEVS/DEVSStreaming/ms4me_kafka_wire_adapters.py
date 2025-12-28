# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ms4me_kafka_wire_adapters.py ---
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
# Wire adapters for DEVSStreaming message serialization over kafka.
# Handles encoding/decoding of DEVS messages for Kafka transport.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from __future__ import annotations
from typing import Any, Dict

from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import BaseMessage

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
