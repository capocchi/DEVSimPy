from confluent_kafka import Producer, Consumer, KafkaError
import threading
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('KafkaCoordinator')

class KafkaCoordinator:
    """Coordinator for DEVS models using Kafka messaging"""

    def __init__(self, model, clock=None, broker="localhost:9092"):
        self.model = model
        self.clock = clock
        self._stop = False
        
        # Test Kafka connection first
        try:
            # Basic producer config for testing
            test_producer = Producer({'bootstrap.servers': broker})
            test_producer.flush(timeout=5)
            logger.info("Successfully connected to Kafka broker at %s", broker)
        except Exception as e:
            logger.error("Failed to connect to Kafka broker: %s", e)
            raise RuntimeError(f"Kafka broker not available at {broker}")

        # Configure producer with valid callbacks
        producer_config = {
            'bootstrap.servers': broker,
            'client.id': f'coordinator_{model.name}',
            'error_cb': self._kafka_error_callback,
            'statistics.interval.ms': 5000  # Correct parameter name
        }
        
        self.producer = Producer(producer_config)
        logger.info("Producer initialized for coordinator %s", model.name)
        
        # Configure consumer
        consumer_config = {
            'bootstrap.servers': broker,
            'group.id': f'coordinator_{model.name}',
            'auto.offset.reset': 'earliest',
            'error_cb': self._kafka_error_callback
        }
        
        self.consumer = Consumer(consumer_config)
        logger.info("Consumer initialized for coordinator %s", model.name)
        
        # Initialize models and topics
        self.child_models = {}
        self._collect_child_models(model)
        self._ensure_topics_exist()
    
    def _ensure_topics_exist(self):
        """Create required topics if they don't exist"""
        if not self.child_models:
            logger.warning("No child models found - cannot create topics")
            return
            
        logger.info("Creating topics for %d models", len(self.child_models))
        
        # Create topics for each model
        for model_name in self.child_models:
            input_topic = f'devs.{model_name}.in'
            output_topic = f'devs.{model_name}.out'
            
            # Send initial message to create input/output topics
            init_message = json.dumps({
                'type': 'init',
                'time': 0.0,
                'data': None
            }).encode('utf-8')
            
            logger.debug("Creating topics for model %s", model_name)
            self.producer.produce(input_topic, init_message)
            self.producer.produce(output_topic, init_message)
            
        self.producer.flush()
        logger.info("Topics created successfully")
    
    # Wait for topics to be created
    time.sleep(1.0)

    def _collect_child_models(self, model):
        """Recursively collect all child models"""
        logger.info("Collecting child models for %s", model.name)
        
        # Handle atomic models
        if not hasattr(model, 'componentSet'):
            self.child_models[model.name] = model
            logger.debug("Added atomic model: %s", model.name)
            return
            
        # Handle coupled models
        for component in model.componentSet:
            self.child_models[component.name] = component
            logger.debug("Added component: %s", component.name)
            
            # Recursively process coupled components
            if hasattr(component, 'componentSet'):
                self._collect_child_models(component)
        
        # Log collected models
        logger.info("Found %d child models", len(self.child_models))
    
    def _kafka_error_callback(self, err):
        """Callback for Kafka errors"""
        logger.error("Kafka error: %s", err)

    def _kafka_stats_callback(self, stats):
        """Callback for Kafka stats"""
        logger.debug("Kafka stats: %s", stats)

    def start(self):
        """Start coordinator main loop"""
        topics = [f'devs.{name}.out' for name in self.child_models.keys()]
        
        if not topics:
            logger.warning("No topics to subscribe to - coordinator will not start")
            return
            
        try:
            self.consumer.subscribe(topics)
            logger.info("Subscribed to topics: %s", topics)
            
            while not self._stop:
                try:
                    msg = self.consumer.poll(1.0)
                    
                    if msg is None:
                        continue
                        
                    if msg.error():
                        if msg.error().code() != KafkaError._PARTITION_EOF:
                            logger.error("Consumer error: %s", msg.error())
                        continue
                    
                    logger.info("Raw message received on topic: %s", msg.topic())
                    logger.info("Message value: %s", msg.value().decode('utf-8'))
                    
                    self._handle_message(msg)
                    
                except Exception as e:
                    logger.exception("Error processing message in coordinator loop: %s", e)
                
        except Exception as e:
            logger.exception("Fatal error in coordinator loop: %s", e)
            self.stop()
    
    def _route_message(self, source_name, data):
        """Route message to connected models"""
        try:
            source_model = self.child_models.get(source_name)
            if not source_model:
                logger.warning("Source model %s not found", source_name)
                return
                
            message_routed = False
            for port in source_model.OPorts:
                for connection in port.connections:
                    target = connection.host_target.model
                    
                    logger.info("Routing message from %s to %s", source_name, target.name)
                    logger.debug("Message data: %s", data)
                    
                    self.producer.produce(
                        f'devs.{target.name}.in',
                        json.dumps({
                            'type': 'external',
                            'time': self.clock().Get() if self.clock else data.get('time', 0),
                            'port': connection.host_target.name,
                            'data': data.get('data', {})
                        }).encode('utf-8')
                    )
                    message_routed = True
                    
            self.producer.flush()
            
            if message_routed:
                logger.info("Message successfully routed from %s", source_name)
            else:
                logger.warning("No connections found for model %s", source_name)
                
        except Exception as e:
            logger.exception("Error routing message from %s: %s", source_name, e)

    def _handle_message(self, msg):
        try:
            data = json.loads(msg.value().decode('utf-8'))
            source_model = msg.topic().split('.')[1]
            
            logger.info("Processing message from %s", source_model)
            logger.info("Message data: %s", data)
            
            if data.get('type') == 'init':
                logger.debug("Skipping init message")
                return
                
            if self.clock and 'time' in data:
                old_time = self.clock().Get()
                self.clock().Set(data['time'])
                logger.info("Updated simulation time from %f to %f", old_time, data['time'])
            
            self._route_message(source_model, data)
            
        except Exception as e:
            logger.exception("Error handling message: %s", e)

    def stop(self):
        """Stop the coordinator"""
        self._stop = True
        try:
            self.consumer.close()
            self.producer.flush()
        except Exception as e:
            print(f"Error during shutdown: {e}")
            
    def get_time(self):
        """Get current simulation time"""
        return self.clock().Get() if self.clock else 0