# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# KafkaReceiverProxy.py ---
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
# Kafka-specific receiver proxy for distributed DEVS simulation.
# Convenience class wrapping BrokerReceiverProxy for Kafka usage.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
from typing import Dict, Any, Optional

from DEVSKernel.BrokerDEVS.Proxies.BrokerReceiverProxy import BrokerReceiverProxy
from DEVSKernel.BrokerDEVS.Core.BrokerWireAdapter import BrokerWireAdapter

logger = logging.getLogger(__name__)


class KafkaReceiverProxy(BrokerReceiverProxy):
    """
    Kafka-specific receiver proxy.
    
    Convenience class that simplifies Kafka usage by pre-configuring
    the generic BrokerReceiverProxy with Kafka-specific defaults.
    
    Example:
        receiver = KafkaReceiverProxy(
            bootstrap_servers="localhost:9092",
            group_id="my-group"
        )
        receiver.subscribe(["output-topic"])
        messages = receiver.receive_messages(pending_models, timeout=30.0)
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "devsimpy-receiver",
        consumer_config: Optional[Dict[str, Any]] = None,
        wire_adapter: Optional[BrokerWireAdapter] = None,
    ):
        """
        Initialize Kafka receiver proxy.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers (e.g., "localhost:9092")
            group_id: Consumer group ID (default: "devsimpy-receiver")
            consumer_config: Custom Kafka consumer configuration (optional)
            wire_adapter: Message deserialization adapter (default: JSON)
            
        Raises:
            ImportError: If confluent-kafka is not installed
        """
        from DEVSKernel.BrokerDEVS.Brokers.kafka.KafkaAdapter import KafkaAdapter

        kafka_config = consumer_config or {}
        kafka_config["group.id"] = group_id

        kafka_adapter = KafkaAdapter(bootstrap_servers)
        super().__init__(kafka_adapter, kafka_config, wire_adapter)
        
        logger.info(
            "Initialized KafkaReceiverProxy (bootstrap=%s, group=%s)",
            bootstrap_servers,
            group_id,
        )
