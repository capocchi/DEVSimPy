# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# auto_mqtt.py ---
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
# Utilities for automatically ensuring MQTT broker availability.
# Attempts to connect to local MQTT broker (Mosquitto).
# If unavailable, returns configuration for external broker.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time

logger = logging.getLogger(__name__)


def check_mqtt_broker_available(address: str = "localhost", port: int = 1883, timeout: float = 5.0) -> bool:
    """
    Check if an MQTT broker is available at the given address and port.
    
    Args:
        address: Broker address
        port: Broker port
        timeout: Connection timeout in seconds
        
    Returns:
        True if broker is available, False otherwise
    """
    try:
        import paho.mqtt.client as mqtt
        
        # Create client compatible with paho-mqtt 2.x and 1.x
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"checker-{int(time.time() * 1000)}")
        except (TypeError, AttributeError):
            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=f"checker-{int(time.time() * 1000)}")
            except (TypeError, AttributeError):
                client = mqtt.Client(client_id=f"checker-{int(time.time() * 1000)}")
        
        client.connect(address, port, keepalive=5)
        time.sleep(0.5)  # Wait for connection to establish
        client.disconnect()
        
        logger.info("MQTT broker is available at %s:%d", address, port)
        return True
    except Exception as e:
        logger.debug("MQTT broker not available at %s:%d: %s", address, port, e)
        return False


def ensure_mqtt_broker(
    address: str = "localhost",
    port: int = 1883,
    attempts: int = 5,
    retry_delay: float = 2.0,
) -> tuple[str, int]:
    """
    Ensure MQTT broker is available, with retries.
    
    Args:
        address: Broker address to check
        port: Broker port to check
        attempts: Number of connection attempts
        retry_delay: Delay between attempts in seconds
        
    Returns:
        Tuple of (address, port) if broker is available
        
    Raises:
        RuntimeError: If broker is not available after all attempts
    """
    logger.info("Checking MQTT broker availability at %s:%d", address, port)
    
    for attempt in range(1, attempts + 1):
        if check_mqtt_broker_available(address, port):
            return address, port
        
        if attempt < attempts:
            logger.info(
                "MQTT broker not available (attempt %d/%d), retrying in %.1f seconds...",
                attempt, attempts, retry_delay
            )
            time.sleep(retry_delay)
    
    raise RuntimeError(
        f"MQTT broker not available at {address}:{port} after {attempts} attempts. "
        f"Please ensure the MQTT broker is running and reachable."
    )
