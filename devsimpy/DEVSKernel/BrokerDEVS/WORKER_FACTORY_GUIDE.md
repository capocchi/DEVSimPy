# Unified Worker Factory System - Documentation

## Overview

The unified worker factory system eliminates the need for hard-coded broker and message standard types. Instead, it provides:

1. **StandardRegistry** - Central registry for message standards and their worker implementations
2. **SimulationConfig** - Unified configuration combining broker settings + message standard
3. **WorkerFactory** - Universal factory for creating workers with any (Standard + Broker) combination
4. **AutoSimulationConfig** - Auto-configures simulation with broker detection + standard selection

## Key Benefits

- **No Hard-Coding**: Adding new standards or brokers doesn't require modifying core factory code
- **Orthogonal Concerns**: Message standards and brokers are independent - any combination is supported
- **Environment-Based**: Configuration via environment variables for containerization
- **Backward Compatible**: Existing code continues to work through compatibility functions

## Architecture

```
User Code
    ↓
WorkerFactory.create_worker(model_name, model, config)
    ↓
StandardRegistry.get_worker_class(standard, broker)
    ↓
Worker Class (factory returns appropriate worker)
    ↓
Worker Instance (configured for broker + standard)
```

## Usage Examples

### Example 1: Basic Usage with Full Configuration

```python
from devsimpy.DEVSKernel.BrokerDEVS import (
    SimulationConfig,
    WorkerFactory,
)

# Create configuration
config = SimulationConfig(
    broker_type='mqtt',
    broker_host='localhost',
    broker_port=1883,
    message_standard='devs-streaming',
    username='user',
    password='pass',
)

# Create worker
worker = WorkerFactory.create_worker(
    model_name='MyModel',
    model=my_devs_model,
    config=config
)

# Use worker
worker.connect()
# ... send/receive messages ...
worker.disconnect()
```

### Example 2: Auto-Configured (Broker Detection)

```python
from devsimpy.DEVSKernel.BrokerDEVS import (
    WorkerFactory,
)

# Worker with auto-detected broker settings
worker = WorkerFactory.create_worker_from_env(
    model_name='MyModel',
    model=my_devs_model,
    standard='devs-streaming',  # Can override standard
)
```

### Example 3: Auto-Configure Convenience Function

```python
from devsimpy.DEVSKernel.BrokerDEVS import (
    auto_configure_simulation,
    WorkerFactory,
)

# Auto-configure everything
config = auto_configure_simulation(
    standard='devs-streaming',
    broker='mqtt',  # Can specify, or auto-detect
    host='broker.example.com',
    port=1883,
)

# Create worker
worker = WorkerFactory.create_worker(
    'MyModel', my_devs_model, config
)
```

### Example 4: Using Backward-Compatible Function

```python
from devsimpy.DEVSKernel.BrokerDEVS import create_worker

# Old-style API (still works)
worker = create_worker(
    model_name='MyModel',
    model=my_devs_model,
    broker_type='mqtt',
    broker_host='localhost',
    broker_port=1883,
    standard='ms4me',
)
```

## Environment Variables

The `AutoSimulationConfig` respects the following environment variables:

```bash
# Message standard selection
DEVS_MESSAGE_STANDARD=devs-streaming

# Broker configuration
DEVS_BROKER_TYPE=mqtt
DEVS_BROKER_HOST=localhost
DEVS_BROKER_PORT=1883
DEVS_BROKER_USERNAME=user
DEVS_BROKER_PASSWORD=pass
```

Example:
```bash
export DEVS_MESSAGE_STANDARD=devs-streaming
export DEVS_BROKER_TYPE=kafka
export DEVS_BROKER_HOST=kafka.example.com
export DEVS_BROKER_PORT=9092

python my_simulation.py
```

## Registering a New Message Standard

### Step 1: Create Standard Worker Classes

```python
# mystandard_mqtt.py
from devsimpy.DEVSKernel.BrokerDEVS.standard_registry import StandardWorkerBase

class MyStandardMqttWorker(StandardWorkerBase):
    def __init__(self, model_name, model, **kwargs):
        super().__init__(model_name, model, **kwargs)
        # Initialize MQTT-specific stuff
        
    def connect(self):
        # Connect to MQTT broker
        pass
    
    def disconnect(self):
        # Disconnect from MQTT broker
        pass
    
    def send_message(self, topic, message):
        # Send message via MQTT
        return True
    
    def receive_message(self, topic, timeout=1.0):
        # Receive message via MQTT
        return None
```

### Step 2: Register the Standard

```python
from devsimpy.DEVSKernel.BrokerDEVS import (
    StandardRegistry,
    MessageStandard,
    BrokerType,
)
from mystandard_mqtt import MyStandardMqttWorker
from mystandard_kafka import MyStandardKafkaWorker

# Create enum value (if needed)
# Add to MessageStandard enum:
#   MY_STANDARD = "mystandard"

# Register the standard
StandardRegistry.register_standard(
    MessageStandard.MY_STANDARD,  # Or create dynamic enum
    {
        BrokerType.MQTT: MyStandardMqttWorker,
        BrokerType.KAFKA: MyStandardKafkaWorker,
    }
)

# Now workers for this standard are available!
config = SimulationConfig(
    broker_type='kafka',
    broker_host='localhost',
    broker_port=9092,
    message_standard='mystandard',
)

worker = WorkerFactory.create_worker('Model_0', model, config)
```

## Registering a New Broker Type

To add a new broker type (e.g., RabbitMQ, Redis):

### Step 1: Create Workers for Each Standard

```python
# For DEVSStreaming standard
class MS4MeRabbitMqWorker(StandardWorkerBase):
    # Implementation...
    pass

# For your custom standard
class MyStandardRabbitMqWorker(StandardWorkerBase):
    # Implementation...
    pass
```

### Step 2: Register Workers

```python
from devsimpy.DEVSKernel.BrokerDEVS import StandardRegistry, BrokerType, MessageStandard

# Add to existing standards
StandardRegistry.register_worker(
    MessageStandard.DEVS_STREAMING,
    BrokerType.RABBITMQ,
    MS4MeRabbitMqWorker,
)

StandardRegistry.register_worker(
    MessageStandard.MY_STANDARD,
    BrokerType.RABBITMQ,
    MyStandardRabbitMqWorker,
)

# Now RabbitMQ is available for all registered standards!
config = SimulationConfig(
    broker_type='rabbitmq',
    broker_host='localhost',
    broker_port=5672,
    message_standard='devs-streaming',
)

worker = WorkerFactory.create_worker('Model_0', model, config)
```

## Discovery API

```python
from devsimpy.DEVSKernel.BrokerDEVS import WorkerFactory

# Get all registered standards
standards = WorkerFactory.get_supported_standards()
# ['ms4me', 'generic', 'mystandard']

# Get brokers for a specific standard
brokers = WorkerFactory.get_supported_brokers('ms4me')
# ['kafka', 'mqtt', 'rabbitmq']
```

## Error Handling

The factory provides clear error messages:

```python
try:
    config = SimulationConfig(
        broker_type='nonexistent_broker',
        broker_host='localhost',
        broker_port=9999,
        message_standard='devs-streaming',
    )
    worker = WorkerFactory.create_worker('Model', model, config)
except ValueError as e:
    print(f"Configuration error: {e}")
    # Output: "Unsupported combination: standard=devs-streaming, broker=nonexistent_broker"
except RuntimeError as e:
    print(f"Worker creation error: {e}")
```

## Migration Guide

### For Existing Code Using auto_broker.py

**Before:**
```python
from devsimpy.DEVSKernel.BrokerDEVS.standard_registry import BrokerDetector
from devsimpy.DEVSKernel.BrokerDEVS.DEVSStreaming.MS4MeMqttWorker import MS4MeMqttWorker

detector = BrokerDetector()
info = detector.detect()

worker = MS4MeMqttWorker('Model_0', model, **info.to_dict())
```

**After:**
```python
from devsimpy.DEVSKernel.BrokerDEVS import WorkerFactory

# Direct replacement - auto-detects and creates appropriate worker
worker = WorkerFactory.create_worker_from_env(
    'Model_0', 
    model,
    standard='ms4me',
)
```

### For Code Creating Workers Manually

**Before:**
```python
if broker_type == 'mqtt':
    worker = MS4MeMqttWorker('Model', model, ...)
elif broker_type == 'kafka':
    worker = MS4MeKafkaWorker('Model', model, ...)
else:
    raise ValueError(f"Unknown broker: {broker_type}")
```

**After:**
```python
from devsimpy.DEVSKernel.BrokerDEVS import SimulationConfig, WorkerFactory

config = SimulationConfig(
    broker_type=broker_type,
    broker_host=host,
    broker_port=port,
    message_standard='devs-streaming',
)

worker = WorkerFactory.create_worker('Model', model, config)
```

## Implementation Details

### StandardRegistry

The registry is a class-level registry that maintains:
- `_standards`: Dict[MessageStandard, Dict[BrokerType, WorkerClass]]

This allows:
- Thread-safe registration of new standards
- Lazy loading of worker classes
- Clear error messages when combinations are unsupported

### SimulationConfig

Dataclass providing:
- Broker configuration (type, host, port)
- Message standard selection
- Optional authentication
- Extra configuration options
- Convenience properties and serialization methods

### WorkerFactory

Provides three creation methods:
1. `create_worker()` - From explicit config
2. `create_worker_from_env()` - With auto-detection
3. Legacy `create_worker()` function - For backward compatibility

### AutoSimulationConfig

Combines:
- Environment variable support
- Broker auto-detection via BrokerDetector
- Fallback to defaults
- Clear priority: env vars > auto-detected > defaults

## Testing

Example test for the new system:

```python
import pytest
from devsimpy.DEVSKernel.BrokerDEVS import (
    SimulationConfig,
    WorkerFactory,
    MessageStandard,
    BrokerType,
)

def test_worker_creation():
    """Test basic worker creation."""
    config = SimulationConfig(
        broker_type='mqtt',
        broker_host='localhost',
        broker_port=1883,
        message_standard='devs-streaming',
    )
    
    worker = WorkerFactory.create_worker(
        'TestModel',
        my_model,
        config
    )
    
    assert worker is not None
    assert worker.model_name == 'TestModel'
    assert worker.model == my_model

def test_unsupported_combination():
    """Test error handling for unsupported combinations."""
    config = SimulationConfig(
        broker_type='unsupported_broker',
        broker_host='localhost',
        broker_port=9999,
        message_standard='devs-streaming',
    )
    
    with pytest.raises(ValueError):
        WorkerFactory.create_worker('TestModel', my_model, config)

def test_standard_discovery():
    """Test standard discovery."""
    standards = WorkerFactory.get_supported_standards()
    assert 'devs-streaming' in standards
    
    brokers = WorkerFactory.get_supported_brokers('devs-streaming')
    assert 'mqtt' in brokers
    assert 'kafka' in brokers
```

## Next Steps

1. Refactor existing worker creation code to use WorkerFactory
2. Update SimulationStrategy classes to use new API
3. Add integration tests for all standard+broker combinations
4. Create migration guide for users
5. Document extension points for custom standards/brokers
