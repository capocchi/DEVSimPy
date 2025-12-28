# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# MqttReceiverProxy.py ---
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
# MQTT-specific receiver proxy for distributed DEVS simulation.
# Convenience class wrapping BrokerReceiverProxy for MQTT usage.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
from typing import Dict, Any, Optional

from DEVSKernel.BrokerDEVS.Proxies.BrokerReceiverProxy import BrokerReceiverProxy
from DEVSKernel.BrokerDEVS.Core.BrokerWireAdapter import BrokerWireAdapter

logger = logging.getLogger(__name__)


class MqttReceiverProxy(BrokerReceiverProxy):
    """
    MQTT-specific receiver proxy.
    
    Convenience class that simplifies MQTT usage by pre-configuring
    the generic BrokerReceiverProxy with MQTT-specific defaults.
    
    Example:
        receiver = MqttReceiverProxy(
            broker_host="localhost",
            broker_port=1883,
            client_id="my-receiver"
        )
        receiver.subscribe(["output/#"])
        messages = receiver.receive_messages(pending_models, timeout=30.0)
    """

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "devsimpy-receiver",
        consumer_config: Optional[Dict[str, Any]] = None,
        wire_adapter: Optional[BrokerWireAdapter] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize MQTT receiver proxy.
        
        Args:
            broker_host: MQTT broker hostname (default: "localhost")
            broker_port: MQTT broker port (default: 1883)
            client_id: MQTT client ID (default: "devsimpy-receiver")
            consumer_config: Custom MQTT consumer configuration (optional)
            wire_adapter: Message deserialization adapter (default: JSON)
            username: MQTT username for authentication (optional)
            password: MQTT password for authentication (optional)
            
        Raises:
            ImportError: If paho-mqtt is not installed
        """
        from DEVSKernel.BrokerDEVS.Brokers.mqtt.MqttAdapter import MqttAdapter
        from DEVSKernel.BrokerDEVS.DEVSStreaming.ms4me_mqtt_wire_adapters import StandardWireAdapter as MS4MeStandardWireAdapter

        mqtt_config = consumer_config or {}
        
        # Add MQTT-specific config (but NOT broker/port - those are adapter params)
        mqtt_config.update({
            "client_id": client_id,
        })
        
        # Add authentication if provided
        if username is not None:
            mqtt_config["username"] = username
        if password is not None:
            mqtt_config["password"] = password
        
        # Use ms4me StandardWireAdapter (pickle-based) for compatibility with workers
        if wire_adapter is None:
            # Create an adapter that wraps ms4me StandardWireAdapter to match BrokerWireAdapter interface
            class MS4MeWireAdapterBridge:
                """Bridge between ms4me serialize/deserialize and BrokerWireAdapter to_wire/from_wire"""
                def __init__(self):
                    self.adapter = MS4MeStandardWireAdapter()
                    self.format_name = "pickle"
                
                def to_wire(self, msg):
                    return self.adapter.serialize(msg)
                
                def from_wire(self, data):
                    return self.adapter.deserialize(data)
            
            wire_adapter = MS4MeWireAdapterBridge()
        
        mqtt_adapter = MqttAdapter(broker_host)
        super().__init__(mqtt_adapter, mqtt_config, wire_adapter)
        
        logger.info(
            "Initialized MqttReceiverProxy (host=%s, port=%d, client=%s, auth=%s)",
            broker_host,
            broker_port,
            client_id,
            username is not None,
        )
