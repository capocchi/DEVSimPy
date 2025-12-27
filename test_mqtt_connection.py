#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test MQTT connection with paho-mqtt 2.1.0 compatibility
Supports testing local Docker MQTT and public HiveMQ broker
"""
import time
import logging
import sys
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mqtt(broker_address='localhost', port=1883, username=None, password=None):
    """Test MQTT connection"""
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
    
    def on_connect(client, userdata, flags=None, rc=None, properties=None):
        """Handle connection - compatible with both VERSION1 and VERSION2"""
        nonlocal connected
        
        # Handle both VERSION2 (5 params) and VERSION1 (3-4 params)
        reason_code = rc if rc is not None else flags
        
        if reason_code == 0:
            logger.info(f"✓ Successfully connected to {broker_address}:{port}")
            connected = True
        else:
            error_msg = {
                0: "Connection successful",
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized",
            }.get(reason_code, f"Unknown error code {reason_code}")
            logger.error(f"✗ Connection failed with code {reason_code}: {error_msg}")
    
    def on_disconnect(client, userdata, flags=None, rc=None, properties=None):
        """Handle disconnection"""
        reason_code = rc if rc is not None else flags
        
        if reason_code != 0:
            error_msg = {
                0: "Normal disconnection",
                1: "Incorrect protocol version",
                4: "Bad username or password",
                5: "Not authorized",
            }.get(reason_code, f"Unspecified error")
            logger.error(f"Unexpected disconnection (code {reason_code}: {error_msg})")
    
    logger.info("=" * 60)
    logger.info(f"Testing MQTT connection to {broker_address}:{port}")
    if username:
        logger.info(f"Credentials: {username}:{'*' * len(password or '')}")
    else:
        logger.info("Using anonymous connection")
    logger.info("=" * 60)
    
    # Try paho-mqtt 2.x API first
    try:
        logger.info("Trying paho-mqtt 2.x API (VERSION2)...")
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
    
    # Set credentials if provided
    if username:
        client.username_pw_set(username, password or "")
    
    try:
        logger.info(f"Connecting to {broker_address}:{port}...")
        client.connect(broker_address, port, keepalive=60)
        client.loop_start()
        
        # Wait for connection
        for i in range(20):
            if connected:
                logger.info("✓ Connection test PASSED")
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
    parser = argparse.ArgumentParser(description='Test MQTT broker connection')
    parser.add_argument('--broker', default='localhost', help='Broker address (default: localhost)')
    parser.add_argument('--port', type=int, default=1883, help='Broker port (default: 1883)')
    parser.add_argument('--username', help='Username for authentication')
    parser.add_argument('--password', help='Password for authentication')
    parser.add_argument('--public', action='store_true', help='Test with public HiveMQ broker instead')
    
    args = parser.parse_args()
    
    # Use public broker if requested
    if args.public:
        broker = 'broker.hivemq.com'
        port = 1883
        username = None
        password = None
        logger.info("Using public HiveMQ broker (broker.hivemq.com:1883)")
    else:
        broker = args.broker
        port = args.port
        username = args.username
        password = args.password
    
    success = test_mqtt(broker, port, username, password)
    sys.exit(0 if success else 1)
