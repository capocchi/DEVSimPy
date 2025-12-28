# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# MqttStreamProxy.py ---
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


class MqttStreamProxy(BrokerStreamProxy):
    """
    MQTT-specific stream proxy.
    
    Convenience wrapper for sending messages to MQTT with sensible defaults.
    
    Example:
        >>> proxy = MqttStreamProxy(
        ...     broker_host="mosquitto",
        ...     broker_port=1883,
        ...     client_id="my-producer",
        ...     username="user",
        ...     password="secret"
        ... )
        >>> proxy.send_message("sensors/temperature", {"value": 23.5})
        >>> proxy.flush()
    """

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "devsimpy-sender",
        producer_config: Optional[Dict[str, Any]] = None,
        wire_adapter: Optional[BrokerWireAdapter] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize MQTT stream proxy.
        
        Args:
            broker_host: MQTT broker hostname (default: "localhost")
            broker_port: MQTT broker port (default: 1883)
            client_id: MQTT client ID (default: "devsimpy-sender")
            producer_config: Custom producer configuration dictionary (optional)
            wire_adapter: Message serialization adapter (default: JSON)
                Use BrokerWireAdapterFactory.create() for other formats
            username: MQTT username for authentication (optional)
            password: MQTT password for authentication (optional)
                
        Raises:
            ImportError: If paho-mqtt is not installed
            ConnectionError: If unable to connect to MQTT broker
        """
        from DEVSKernel.BrokerDEVS.Brokers.mqtt.MqttAdapter import MqttAdapter
        from DEVSKernel.BrokerDEVS.MS4Me.ms4me_mqtt_wire_adapters import StandardWireAdapter as MS4MeStandardWireAdapter

        mqtt_config = producer_config or {}
        
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
            "Initialized MqttStreamProxy (broker=%s:%d, client_id=%s, auth=%s)",
            broker_host,
            broker_port,
            client_id,
            username is not None,
        )
