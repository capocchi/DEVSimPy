# devs_kafka_wire_adapters.py
from __future__ import annotations

from typing import Any, Dict

from .devs_kafka_messages import BaseMessage


# ---------------------------------------------------------------------
#  Adaptateur "standard" : enveloppe {corr_id, atomic_index, payload}
#  où payload est un message devs.msg.* (example-messages.json)
# ---------------------------------------------------------------------

class StandardWireAdapter:
    """
    Adaptateur pour le format "standard" :
      Kafka value = {
        "correlation_id": <float>,
        "atomic_index": <int>,
        "payload": { ... devs.msg.* ... }
      }
    """

    @staticmethod
    def to_wire(msg: BaseMessage, corr_id: float, index: int) -> Dict[str, Any]:
        """
        Transforme un BaseMessage (InitSim, NextTime, ...) en dict prêt à être
        sérialisé en JSON et envoyé sur Kafka.
        """
        return {
            "correlation_id": corr_id,
            "atomic_index": index,
            "payload": msg.to_dict(),
        }

    @staticmethod
    def from_wire(d: Dict[str, Any]) -> BaseMessage:
        """
        Transforme un dict (valeur Kafka) en BaseMessage.
        Suppose la forme :
          { correlation_id, atomic_index, payload={devsType: ...} }.
        """
        payload = d.get("payload", {}) or {}
        return BaseMessage.from_dict(payload)
