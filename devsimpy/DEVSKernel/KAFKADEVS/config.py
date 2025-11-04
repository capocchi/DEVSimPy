#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration pour le broker Kafka
"""

KAFKA_CONFIG = {
    'bootstrap_servers': 'localhost:9092',
    'base_topic': 'devs_simulation',
    'producer': {
        'acks': 'all',
        'retries': 3,
        'max_in_flight_requests_per_connection': 1
    },
    'consumer': {
        'auto_offset_reset': 'latest',
        'enable_auto_commit': True,
        'session_timeout_ms': 30000
    }
}
