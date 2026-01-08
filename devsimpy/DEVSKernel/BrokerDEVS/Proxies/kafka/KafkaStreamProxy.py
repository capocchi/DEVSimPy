# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# KafkaStreamProxy.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/28/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
from typing import Dict, Any, Optional

from DEVSKernel.BrokerDEVS.Proxies.BrokerStreamProxy import BrokerStreamProxy
from DEVSKernel.BrokerDEVS.Core.BrokerWireAdapter import BrokerWireAdapter

logger = logging.getLogger(__name__)


class KafkaStreamProxy(BrokerStreamProxy):
    """
    Kafka-specific stream proxy.
    
    Convenience wrapper for sending messages to Kafka with sensible defaults.
    
    Example:
        >>> proxy = KafkaStreamProxy(bootstrap_servers="kafka:9092")
        >>> proxy.send_message("my-topic", {"key": "value"})
        >>> proxy.flush()
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        producer_config: Optional[Dict[str, Any]] = None,
        wire_adapter: Optional[BrokerWireAdapter] = None,
    ):
        """
        Initialize Kafka stream proxy.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers (default: "localhost:9092")
            producer_config: Custom producer configuration dictionary (optional)
            wire_adapter: Message serialization adapter (default: JSON)
                Use BrokerWireAdapterFactory.create() for other formats
                
        Raises:
            ImportError: If confluent-kafka is not installed
            ConnectionError: If unable to connect to Kafka brokers
        """
        from DEVSKernel.BrokerDEVS.Brokers.kafka.KafkaAdapter import KafkaAdapter

        kafka_adapter = KafkaAdapter(bootstrap_servers)
        super().__init__(kafka_adapter, producer_config, wire_adapter)
        
        logger.info(
            "Initialized KafkaStreamProxy (bootstrap_servers=%s)",
            bootstrap_servers,
        )
