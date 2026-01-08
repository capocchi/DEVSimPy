# -*- coding: utf-8 -*-

"""Kafka proxies - convenience wrappers for KafkaAdapter"""

from .KafkaReceiverProxy import KafkaReceiverProxy
from .KafkaStreamProxy import KafkaStreamProxy

__all__ = ["KafkaReceiverProxy", "KafkaStreamProxy"]
