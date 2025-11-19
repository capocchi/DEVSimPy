### KAFKA_MODE OPTIONS: "local" or "standard"
###  - local: topics work_i and atomic_results
###  - standard: topics ms4meXXXIn and ms4meOut
### Default:
KAFKA_MODE = "standard"

### Whether to auto-start a Kafka broker if not already running
AUTO_START_KAFKA_BROKER=True

### Kafka broker configuration
KAFKA_BOOTSTRAP="localhost:9092"
KAFKA_CONATINER_NAME="kafkabroker"
KAFKA_IMAGE="apache/kafka:latest"