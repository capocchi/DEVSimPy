# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# RabbitmqReceiverProxy.py ---
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
# RabbitMQ-specific receiver proxy for distributed DEVS simulation.
# Convenience class wrapping BrokerReceiverProxy for RabbitMQ usage.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
from typing import Optional

from DEVSKernel.BrokerDEVS.Proxies.BrokerReceiverProxy import BrokerReceiverProxy
from DEVSKernel.BrokerDEVS.Core.BrokerWireAdapter import BrokerWireAdapter

logger = logging.getLogger(__name__)


class RabbitmqReceiverProxy(BrokerReceiverProxy):
    """
    RabbitMQ-specific receiver proxy.
    
    Convenience class that simplifies RabbitMQ usage by pre-configuring
    the generic BrokerReceiverProxy with RabbitMQ-specific defaults.
    
    Example:
        receiver = RabbitmqReceiverProxy(
            url="amqp://guest:guest@localhost:5672//"
        )
        receiver.subscribe(["output-queue"])
        messages = receiver.receive_messages(pending_models, timeout=30.0)
    """

    def __init__(
        self,
        url: str = "amqp://localhost",
        wire_adapter: Optional[BrokerWireAdapter] = None,
    ):
        """
        Initialize RabbitMQ receiver proxy.
        
        Args:
            url: RabbitMQ connection URL
                Format: amqp[s]://[username[:password]@]host[:port][/vhost]
                Default: "amqp://localhost"
            wire_adapter: Message deserialization adapter (default: JSON)
            
        Raises:
            ImportError: If pika is not installed
        """
        from DEVSKernel.BrokerDEVS.Brokers.rabbitmq.RabbitmqAdapter import (
            RabbitmqAdapter,
        )

        rabbitmq_adapter = RabbitmqAdapter(url)
        super().__init__(rabbitmq_adapter, wire_adapter=wire_adapter)
        
        logger.info(
            "Initialized RabbitmqReceiverProxy (url=%s)",
            url,
        )
