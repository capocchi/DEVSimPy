### KAFKA_MODE OPTIONS:
###  - fromMe4Me: topics ms4meXXXIn and ms4meOut
### Default:
KAFKA_MODE = "fromMe4Me"

### Whether to auto-start a Kafka broker if not already running
AUTO_START_KAFKA_BROKER=True

### Kafka broker configuration
KAFKA_BOOTSTRAP="localhost:9092"
KAFKA_CONATINER_NAME="kafkabroker"
KAFKA_IMAGE="apache/kafka:latest"