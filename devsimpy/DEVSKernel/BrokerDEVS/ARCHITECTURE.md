# Unified Architecture for DEVS Workers

## Problem Statement

The original architecture separated concerns horizontally but lacked integration:

```
Message Standards    Broker Types
    |                   |
  DEVSStreaming ───────────── Kafka
                   ✗ No unified API
  Generic ───────── MQTT
```

Issues:
- Adding a new standard required creating N worker classes (one per broker)
- Adding a new broker required creating N worker classes (one per standard)
- Hard-coded broker types in factory methods
- Inconsistent worker creation patterns
- Difficult to discover supported combinations

## Solution: Unified Registry Pattern

```
                    StandardRegistry
                    ╱    │    ╲
                  /      │      \
                v        v        v
        MessageStandard  BrokerType  WorkerClass
              │            │            │
        ┌─────┼────────┬───┼────────┬──┴──────┐
        │     │        │   │        │         │
      DEVSStreaming Generic  MQTT KAFKA RABBITMQ    Worker
        │             │    │       │        Classes
        └─────────────┴────┴───────┴────────┘
                        │
                   WorkerFactory
                        │
              Any (Standard+Broker)
              combination supported
```

Key insight: **Message Standards and Brokers are Orthogonal Concerns**

## Architecture Components

### 1. MessageStandard Enum
Defines available message protocols:
- `DEVS_STREAMING` - DEVS-Streaming standard (MS4Me compatible)
- `GENERIC` - Minimal generic protocol
- Extensible for new standards

```python
class MessageStandard(Enum):
    DEVS_STREAMING = "devs-streaming"
    GENERIC = "generic"
```

### 2. BrokerType Enum
Defines supported message brokers:
- `KAFKA` - Distributed streaming
- `MQTT` - IoT messaging
- `RABBITMQ` - Enterprise messaging
- `REDIS` - In-memory data store

```python
class BrokerType(Enum):
    KAFKA = "kafka"
    MQTT = "mqtt"
    RABBITMQ = "rabbitmq"
    REDIS = "redis"
```

### 3. StandardWorkerBase
Abstract base class for all workers providing unified interface:

```
StandardWorkerBase
├── connect()
├── disconnect()
├── send_message(topic, message) → bool
└── receive_message(topic, timeout) → Message
```

All worker implementations extend this, ensuring consistent behavior across standards and brokers.

### 4. StandardRegistry
Central registration point mapping (Standard + Broker) → WorkerClass:

```
Registry Contents:
─────────────────────────────────────────────────────────
Standard         │ Broker      │ Worker Class
─────────────────┼─────────────┼──────────────────────────────
DEVS_STREAMING   │ MQTT        │ MS4MeMqttWorker
                 │ KAFKA       │ MS4MeKafkaWorker
                 │ RABBITMQ    │ MS4MeRabbitMqWorker
─────────────────┼─────────────┼──────────────────────────────
GENERIC          │ MQTT        │ GenericMqttWorker
                 │ KAFKA       │ GenericKafkaWorker
                 │ RABBITMQ    │ GenericRabbitMqWorker
─────────────────────────────────────────────────────────
```

### 5. SimulationConfig
Unified configuration dataclass:

```python
@dataclass
class SimulationConfig:
    broker_type: str              # kafka, mqtt, etc.
    broker_host: str              # localhost, broker.example.com
    broker_port: int              # 9092, 1883, etc.
    message_standard: str         # ms4me, generic, etc.
    username: Optional[str]       # auth
    password: Optional[str]       # auth
    extra_config: Optional[dict]  # custom options
```

### 6. AutoSimulationConfig
Auto-configuration combining broker detection + standard selection:

```
Priority Order:
1. Environment variables
   (DEVS_BROKER_TYPE, DEVS_MESSAGE_STANDARD, etc.)
   
2. Auto-detected brokers
   (BrokerDetector finds available brokers)
   
3. Defaults
   (Kafka on localhost:9092, DEVSStreaming standard)
```

### 7. WorkerFactory
Universal factory creating workers for any (Standard + Broker):

```python
# No hard-coded types!
worker = WorkerFactory.create_worker(
    model_name='MyModel',
    model=my_devs_model,
    config=SimulationConfig(
        broker_type='mqtt',
        broker_host='localhost',
        broker_port=1883,
        message_standard='ms4me',
    )
)

# Or with auto-detection
worker = WorkerFactory.create_worker_from_env(
    'MyModel',
    my_devs_model,
    standard='ms4me',
)
```

## Data Flow

```
User Code
   │
   └─→ WorkerFactory.create_worker(model, config)
       │
       ├─→ Convert config to enums
       │   ├─ config.message_standard → MessageStandard
       │   └─ config.broker_type → BrokerType
       │
       └─→ StandardRegistry.get_worker_class(standard, broker)
           │
           ├─ Look up in registry
           │ `_standards[MessageStandard.DEVS_STREAMING][BrokerType.MQTT]`
           │
           └─ Return WorkerClass
               │
               └─→ Worker Constructor
                   │
                   └─ Worker Instance
                       (configured, ready to use)
```

## Extension Points

### Adding a New Message Standard

1. Create worker classes for existing brokers:
   ```python
   class MyStandardMqttWorker(StandardWorkerBase):
       def connect(self): ...
       def send_message(self, topic, msg): ...
       # etc.
   
   class MyStandardKafkaWorker(StandardWorkerBase):
       # ... similar implementation
   ```

2. Register the standard:
   ```python
   StandardRegistry.register_standard(
       MessageStandard.MY_STANDARD,  # Add to enum
       {
           BrokerType.MQTT: MyStandardMqttWorker,
           BrokerType.KAFKA: MyStandardKafkaWorker,
           # ...
       }
   )
   ```

3. **Done!** All brokers now support the new standard with zero changes to core code.

### Adding a New Broker Type

1. Create worker classes for each standard:
   ```python
   class MS4MeRabbitMqWorker(StandardWorkerBase):
       # Implementation for DEVSStreaming + RabbitMQ
   
   class GenericRabbitMqWorker(StandardWorkerBase):
       # Implementation for Generic + RabbitMQ
   ```

2. Register workers:
   ```python
   StandardRegistry.register_worker(
       MessageStandard.DEVS_STREAMING,
       BrokerType.RABBITMQ,
       MS4MeRabbitMqWorker,
   )
   
   StandardRegistry.register_worker(
       MessageStandard.GENERIC,
       BrokerType.RABBITMQ,
       GenericRabbitMqWorker,
   )
   ```

3. **Done!** New broker works with all standards with zero changes to core code.

## Design Principles

### 1. Open/Closed Principle
- **Open for Extension**: New standards/brokers via StandardRegistry
- **Closed for Modification**: Core factory code unchanged

### 2. Single Responsibility
- `MessageStandard`: Define available protocols
- `BrokerType`: Define available transports
- `StandardRegistry`: Map combinations → implementations
- `WorkerFactory`: Create workers from config
- `SimulationConfig`: Hold configuration data

### 3. Dependency Injection
- Configuration injected into factory
- Factory creates appropriate worker
- No hard-coded broker/standard types in factory

### 4. Factory Pattern
- StandardRegistry maps combinations to classes
- WorkerFactory creates instances
- Clean separation of class selection from instantiation

## Comparison: Before and After

### Before: Hard-Coded Factory
```python
# Hard-coded in AutoBrokerAdapterFactory
class AutoBrokerAdapterFactory:
    @staticmethod
    def create_from_info(info: BrokerInfo, model_name, model):
        if info.broker_type == BrokerType.KAFKA:
            return MS4MeKafkaWorker(model_name, model, ...)
        elif info.broker_type == BrokerType.MQTT:
            return MS4MeMqttWorker(model_name, model, ...)
        else:
            raise ValueError(f"Unknown broker: {info.broker_type}")

# Problem: Adding RABBITMQ requires modifying this method!
```

### After: Registry-Based Factory
```python
# No changes needed to add new brokers!
class WorkerFactory:
    @staticmethod
    def create_worker(model_name, model, config):
        # Get worker class from registry (same code works for all)
        worker_class = StandardRegistry.get_worker_class(
            config.message_standard,
            config.broker_type,
        )
        # Create instance
        return worker_class(model_name, model, **config_dict)

# To add RABBITMQ:
# 1. Create MS4MeRabbitMqWorker class
# 2. Call StandardRegistry.register_worker()
# 3. Done! WorkerFactory works with no changes!
```

## Configuration Examples

### Example 1: Explicit Configuration
```python
config = SimulationConfig(
    broker_type='mqtt',
    broker_host='broker.example.com',
    broker_port=1883,
    message_standard='devs-streaming',
    username='user',
    password='pass',
)
worker = WorkerFactory.create_worker('Model', model, config)
```

### Example 2: Environment Variables
```bash
export DEVS_MESSAGE_STANDARD=devs-streaming
export DEVS_BROKER_TYPE=kafka
export DEVS_BROKER_HOST=kafka.example.com
export DEVS_BROKER_PORT=9092
```
```python
worker = WorkerFactory.create_worker_from_env('Model', model)
```

### Example 3: Auto-Detection
```python
# Detects available brokers, uses sensible defaults
config = auto_configure_simulation(
    standard='devs-streaming',
    auto_detect=True,  # detect available brokers
)
worker = WorkerFactory.create_worker('Model', model, config)
```

## Testing Strategy

### Unit Tests
- StandardRegistry registration/retrieval
- SimulationConfig initialization
- AutoSimulationConfig priority order

### Integration Tests
- Each (Standard + Broker) combination creates valid worker
- Configuration propagates correctly to worker
- Error handling for unsupported combinations

### End-to-End Tests
- Full simulation with each supported combination
- Message flow through different standards/brokers
- Auto-detection with different available brokers

## Migration Path

1. **Phase 1** (Current): Create new registry system alongside existing code
2. **Phase 2**: Update high-level APIs to use WorkerFactory
3. **Phase 3**: Refactor existing worker classes to extend StandardWorkerBase
4. **Phase 4**: Update SimulationStrategy classes to use WorkerFactory
5. **Phase 5**: Deprecate old factory methods
6. **Phase 6**: Remove old factory code

This allows gradual migration without breaking existing code.

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Adding new standard** | Modify N files (one per broker) | Call `register_standard()` once |
| **Adding new broker** | Modify factory + create N classes | Call `register_worker()` once per standard |
| **Discovering combinations** | Hardcoded list | `WorkerFactory.get_supported_brokers()` |
| **Configuration** | Broker-specific params | Unified SimulationConfig |
| **Auto-detection** | Manual in each strategy | Centralized in AutoSimulationConfig |
| **Testing** | Hard-coded test cases | Generic tests + data-driven tests |
| **Error messages** | Generic "unsupported broker" | Specific "unsupported combination: ..." |

## Technical Debt Eliminated

1. ✅ Hard-coded broker types in factory
2. ✅ Inconsistent worker creation patterns  
3. ✅ Auto-detection separate from standard selection
4. ✅ No unified configuration dataclass
5. ✅ Difficulty adding new standards/brokers
6. ✅ No discovery API for supported combinations
7. ✅ Missing abstract base class for consistency

## Future Extensions

### Middleware Support
```python
class WorkerMiddleware(ABC):
    def send(self, topic, message): ...
    def receive(self, topic, timeout): ...

# Chain multiple middleware layers
worker = WorkerFactory.create_worker_with_middleware(
    'Model', model, config,
    middleware=[LoggingMiddleware, CachingMiddleware]
)
```

### Protocol Negotiation
```python
# Auto-select compatible standard for broker
config = auto_configure_simulation(
    auto_select_standard=True,  # Broker determines standard
)
```

### Metrics and Monitoring
```python
# Built-in observability
config = SimulationConfig(
    ...,
    extra_config={'enable_metrics': True}
)

metrics = worker.get_metrics()  # message count, latency, etc.
```
