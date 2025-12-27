#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick MQTT connection test to diagnose issues
"""

import time
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mqtt():
    try:
        import paho.mqtt.client as mqtt
        try:
            version = mqtt.__version__
        except AttributeError:
            try:
                import paho.mqtt
                version = paho.mqtt.__version__
            except:
                version = "2.x (unknown exact version)"
        logger.info(f"paho-mqtt version: {version}")
    except ImportError as e:
        logger.error(f"paho-mqtt not installed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error importing paho-mqtt: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    connected = False
    
    def on_connect(client, userdata, connect_flags, reason_code, properties):
        nonlocal connected
        if reason_code == 0:
            logger.info("✓ Connected to MQTT broker!")
            connected = True
        else:
            logger.error(f"✗ Connection failed with code {reason_code}")
    
    def on_disconnect(client, disconnect_flags, auth_data, reason_code, properties):
        if reason_code != 0:
            logger.error(f"Unexpected disconnection (code {reason_code})")
    
    logger.info("=" * 60)
    logger.info("Testing MQTT connection to localhost:1883")
    logger.info("=" * 60)
    
    # Try paho-mqtt 2.x API
    try:
        logger.info("Trying paho-mqtt 2.x API...")
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="test-client")
    except (TypeError, AttributeError):
        logger.info("Falling back to paho-mqtt VERSION1 API...")
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="test-client")
        except (TypeError, AttributeError):
            logger.info("Falling back to paho-mqtt 1.x API...")
            client = mqtt.Client(client_id="test-client")
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    try:
        logger.info("Connecting to localhost:1883...")
        client.connect("localhost", 1883, keepalive=60)
        # logger.info("Connecting to broker.hivemq.com:1883...")
        # client.connect("broker.hivemq.com", 1883, keepalive=60)
        client.loop_start()
        
        # Wait for connection
        for i in range(20):
            if connected:
                logger.info("✓ Connection successful!")
                client.disconnect()
                client.loop_stop()
                return True
            time.sleep(0.5)
        
        logger.error("✗ Connection timeout (waited 10 seconds)")
        client.loop_stop()
        return False
        
    except Exception as e:
        logger.error(f"✗ Exception during connection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mqtt()
    exit(0 if success else 1)
