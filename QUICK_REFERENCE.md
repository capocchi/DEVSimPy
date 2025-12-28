# Quick Reference: Unified Worker Factory

## Installation / Setup

The new system is already integrated into the DEVSimPy codebase:

```python
# All imports from the same module
from devsimpy.DEVSKernel.BrokerDEVS import (
    SimulationConfig,
    AutoSimulationConfig,
    auto_configure_simulation,
    WorkerFactory,
    create_worker,  # backward compatible
    StandardRegistry,
    StandardWorkerBase,
    MessageStandard,
    BrokerType,
)
```

## 5-Minute Quick Start

### Scenario 1: MQTT with MS4Me
```python
from devsimpy.DEVSKernel.BrokerDEVS import SimulationConfig, WorkerFactory

config = SimulationConfig(
    broker_type='mqtt',
    broker_host='localhost',
    broker_port=1883,
    message_standard='ms4me',
)

worker = WorkerFactory.create_worker('MyModel', my_model, config)
worker.connect()
```

### Scenario 2: Kafka with Auto-Detection
```python
from devsimpy.DEVSKernel.BrokerDEVS import WorkerFactory

# Auto-detects Kafka, uses MS4Me standard
worker = WorkerFactory.create_worker_from_env('MyModel', my_model)
worker.connect()
```

### Scenario 3: Environment-Based Configuration
```bash
export DEVS_BROKER_TYPE=kafka
export DEVS_BROKER_HOST=kafka.example.com
export DEVS_BROKER_PORT=9092
export DEVS_MESSAGE_STANDARD=ms4me
```

```python
from devsimpy.DEVSKernel.BrokerDEVS import WorkerFactory

worker = WorkerFactory.create_worker_from_env('MyModel', my_model)
```

### Scenario 4: Backward Compatible
```python
from devsimpy.DEVSKernel.BrokerDEVS import create_worker

# Old API still works!
worker = create_worker(
    'MyModel', my_model,
    broker_type='mqtt',
    broker_host='localhost',
    broker_port=1883,
    standard='ms4me',
)
```

## Common Tasks

### Task 1: Create Worker with Credentials
```python
config = SimulationConfig(
    broker_type='mqtt',
    broker_host='secure.broker.com',
    broker_port=8883,
    message_standard='ms4me',
    username='user',
    password='secret',
)

worker = WorkerFactory.create_worker('Model', model, config)
```

### Task 2: Check Supported Combinations
```python
# What standards are available?
standards = WorkerFactory.get_supported_standards()
print(standards)  # ['ms4me', 'generic']

# What brokers does MS4Me support?
brokers = WorkerFactory.get_supported_brokers('ms4me')
print(brokers)  # ['kafka', 'mqtt', 'rabbitmq']
```

### Task 3: Handle Missing Configuration
```python
try:
    config = SimulationConfig(
        broker_type='nonexistent_broker',
        broker_host='localhost',
        broker_port=9999,
        message_standard='ms4me',
    )
    worker = WorkerFactory.create_worker('Model', model, config)
except ValueError as e:
    print(f"Configuration error: {e}")
    # Output: Unsupported combination: standard=ms4me, broker=nonexistent_broker
```

### Task 4: Use Auto-Configuration Directly
```python
from devsimpy.DEVSKernel.BrokerDEVS import auto_configure_simulation

# Auto-detect broker, use specified standard
config = auto_configure_simulation(standard='ms4me')

# Or with some overrides
config = auto_configure_simulation(
    standard='ms4me',
    broker='mqtt',  # Force MQTT instead of auto-detecting
    host='broker.example.com',
)

worker = WorkerFactory.create_worker('Model', model, config)
```

## Adding New Standards

### Step 1: Create Worker Classes
```python
# File: my_standard_workers.py

from devsimpy.DEVSKernel.BrokerDEVS import StandardWorkerBase

class MyStandardMqttWorker(StandardWorkerBase):
    def __init__(self, model_name, model, **kwargs):
        super().__init__(model_name, model, **kwargs)
        # MQTT-specific initialization
    
    def connect(self):
        # Connect to MQTT
        pass
    
    def disconnect(self):
        # Disconnect from MQTT
        pass
    
    def send_message(self, topic, message):
        # Send message
        return True
    
    def receive_message(self, topic, timeout=1.0):
        # Receive message
        return None

# Similar for KafkaWorker, RabbitMqWorker, etc.
```

### Step 2: Register
```python
from devsimpy.DEVSKernel.BrokerDEVS import StandardRegistry, MessageStandard, BrokerType
from my_standard_workers import MyStandardMqttWorker, MyStandardKafkaWorker

StandardRegistry.register_standard(
    MessageStandard.MY_STANDARD,
    {
        BrokerType.MQTT: MyStandardMqttWorker,
        BrokerType.KAFKA: MyStandardKafkaWorker,
    }
)
```

### Step 3: Use
```python
from devsimpy.DEVSKernel.BrokerDEVS import SimulationConfig, WorkerFactory

config = SimulationConfig(
    broker_type='kafka',
    broker_host='localhost',
    broker_port=9092,
    message_standard='mystandard',  # ← Your new standard!
)

worker = WorkerFactory.create_worker('Model', model, config)
```

## Adding New Brokers

### Step 1: Create Worker Classes
```python
# File: rabbitmq_workers.py

from devsimpy.DEVSKernel.BrokerDEVS import StandardWorkerBase

class MS4MeRabbitMqWorker(StandardWorkerBase):
    def __init__(self, model_name, model, **kwargs):
        super().__init__(model_name, model, **kwargs)
        # RabbitMQ-specific initialization
    
    def connect(self):
        # Connect to RabbitMQ
        pass
    
    # ... implement other methods ...

class GenericRabbitMqWorker(StandardWorkerBase):
    # Similar implementation
    pass
```

### Step 2: Register
```python
from devsimpy.DEVSKernel.BrokerDEVS import StandardRegistry, MessageStandard, BrokerType
from rabbitmq_workers import MS4MeRabbitMqWorker, GenericRabbitMqWorker

StandardRegistry.register_worker(
    MessageStandard.MS4ME,
    BrokerType.RABBITMQ,  # ← New broker!
    MS4MeRabbitMqWorker,
)

StandardRegistry.register_worker(
    MessageStandard.GENERIC,
    BrokerType.RABBITMQ,  # ← New broker!
    GenericRabbitMqWorker,
)
```

### Step 3: Use
```python
from devsimpy.DEVSKernel.BrokerDEVS import SimulationConfig, WorkerFactory

# RabbitMQ now works with all registered standards!
config = SimulationConfig(
    broker_type='rabbitmq',
    broker_host='rabbitmq.example.com',
    broker_port=5672,
    message_standard='ms4me',
)

worker = WorkerFactory.create_worker('Model', model, config)
```

## Configuration Reference

### SimulationConfig Properties
```python
config = SimulationConfig(
    broker_type='mqtt',              # Required
    broker_host='localhost',         # Required
    broker_port=1883,                # Required
    message_standard='ms4me',        # Required
    username='user',                 # Optional
    password='pass',                 # Optional
    extra_config={'key': 'value'},  # Optional
)

# Properties
config.broker_address              # 'localhost:1883'
config.to_dict()                   # Dictionary representation
str(config)                        # String representation
```

### Environment Variables
```bash
# Message standard
DEVS_MESSAGE_STANDARD=ms4me

# Broker configuration
DEVS_BROKER_TYPE=mqtt
DEVS_BROKER_HOST=localhost
DEVS_BROKER_PORT=1883

# Authentication
DEVS_BROKER_USERNAME=user
DEVS_BROKER_PASSWORD=pass
```

## Error Messages and Solutions

### Error: "Unsupported combination"
```
ValueError: Unsupported combination: standard=mystandard, broker=rabbitmq
```
**Solution**: Register the worker for this combination:
```python
StandardRegistry.register_worker(
    MessageStandard.MY_STANDARD,
    BrokerType.RABBITMQ,
    MyStandardRabbitMqWorker,
)
```

### Error: "Invalid standard or broker"
```
ValueError: Invalid standard or broker: standard=nonexistent, broker=mqtt
```
**Solution**: Check available standards:
```python
standards = WorkerFactory.get_supported_standards()
print(standards)
```

### Error: "Failed to create worker"
```
RuntimeError: Failed to create worker for model MyModel: [specific error]
```
**Solution**: Check worker class initialization requirements and config values.

## Testing Examples

### Unit Test
```python
import pytest
from devsimpy.DEVSKernel.BrokerDEVS import SimulationConfig, WorkerFactory

def test_worker_creation():
    config = SimulationConfig(
        broker_type='mqtt',
        broker_host='localhost',
        broker_port=1883,
        message_standard='ms4me',
    )
    
    worker = WorkerFactory.create_worker('TestModel', mock_model, config)
    assert worker is not None
    assert worker.model_name == 'TestModel'
```

### Integration Test
```python
def test_mqtt_message_flow():
    config = SimulationConfig(
        broker_type='mqtt',
        broker_host='localhost',
        broker_port=1883,
        message_standard='ms4me',
    )
    
    worker = WorkerFactory.create_worker('Model', model, config)
    worker.connect()
    
    # Test message sending/receiving
    assert worker.send_message('test/topic', b'hello')
    
    worker.disconnect()
```

## Migration Checklist

- [ ] Review WORKER_FACTORY_GUIDE.md
- [ ] Update imports to use WorkerFactory
- [ ] Replace hard-coded worker creation with factory
- [ ] Replace auto_broker.py usage with auto_configure_simulation()
- [ ] Test with each broker type
- [ ] Update documentation
- [ ] Get code review

## Performance Tips

1. **Cache WorkerFactory results** if creating many workers
2. **Register standards once at startup**, not in loops
3. **Use auto-detection sparingly** (runs broker detection)
4. **Connection pooling** for message brokers (handle in worker class)
5. **Async message handling** for high-throughput (worker class implementation)

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see:
# DEBUG - Creating worker: model=MyModel, standard=ms4me, broker=mqtt
# INFO - Created worker MS4MeMqttWorker for model MyModel
```

### Check Registry Contents
```python
from devsimpy.DEVSKernel.BrokerDEVS import StandardRegistry

standards = StandardRegistry.list_standards()
print(f"Registered standards: {standards}")

for std in standards:
    brokers = StandardRegistry.list_brokers_for_standard(std)
    print(f"{std.value}: {[b.value for b in brokers]}")
```

## Related Documentation

- **WORKER_FACTORY_GUIDE.md**: Complete usage guide
- **ARCHITECTURE.md**: Design principles and diagrams
- **STAGE2_IMPLEMENTATION_SUMMARY.md**: What was implemented
- **test_unified_factory.py**: Test examples
