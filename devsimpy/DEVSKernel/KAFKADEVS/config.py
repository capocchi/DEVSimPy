from typing import Dict, Any
import os

# Kafka broker configuration
KAFKA_CONFIG: Dict[str, Any] = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'devsimpy',
    'group.id': 'devsimpy.simulation',
    'auto.offset.reset': 'earliest'
}

# Topic naming patterns
TOPIC_PATTERNS = {
    'model_input': 'devs.{model_name}.in',
    'model_output': 'devs.{model_name}.out',
    'control': 'devs.control'
}

# Simulation settings
SIM_SETTINGS = {
    'poll_timeout': 1.0,  # Timeout for Kafka consumer poll in seconds
    'flush_timeout': 10.0,  # Timeout for producer flush in seconds
    'reconnect_backoff_ms': 1000,
    'reconnect_backoff_max_ms': 10000
}

# Debug and logging settings
DEBUG_SETTINGS = {
    'verbose': False,
    'log_dir': os.path.join('logs', 'kafka'),
    'log_level': 'INFO'
}

def get_topic_name(pattern: str, **kwargs) -> str:
    """Helper function to generate topic names"""
    return TOPIC_PATTERNS[pattern].format(**kwargs)

def get_broker_config(**overrides) -> Dict[str, Any]:
    """Get broker configuration with optional overrides"""
    config = KAFKA_CONFIG.copy()
    config.update(overrides)
    return config