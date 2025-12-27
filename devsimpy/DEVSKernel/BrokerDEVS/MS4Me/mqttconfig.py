# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# mqttconfig.py ---
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
# MQTT configuration for MS4Me distributed DEVS simulation.
#
# To lunch a container: docker run -d --name mqtt -p 1883:1883 -p 9001:9001 eclipse-mosquitto
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

### Whether to auto-check MQTT broker availability
AUTO_START_MQTT_BROKER = True

### MQTT broker configuration
MQTT_BROKER_ADDRESS = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = None  # Set to username if broker requires authentication
MQTT_PASSWORD = None  # Set to password if broker requires authentication

### MQTT connection defaults
MQTT_QOS = 1  # Quality of Service (0=at most once, 1=at least once, 2=exactly once)
MQTT_KEEPALIVE = 60  # Seconds
MQTT_PROTOCOL_VERSION = 4  # MQTTv3.1.1
