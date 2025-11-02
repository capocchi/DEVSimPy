# -*- coding: utf-8 -*-

"""
Kafka-based DEVS simulator implementation
"""

from confluent_kafka import Producer, Consumer, KafkaError
import threading
import json
import time
import logging
from collections import defaultdict
from .DEVS import AtomicDEVS, CoupledDEVS
from PluginManager import PluginManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('KafkaCoordinator')

class Sender:
    """Base class for simulator components that can send messages via Kafka"""
    
    def __init__(self, broker="localhost:9092"):
        self.producer = Producer({
            'bootstrap.servers': broker
        })
        
    def send_message(self, topic, message):
        """Send message to Kafka topic"""
        self.producer.produce(
            topic,
            json.dumps(message).encode('utf-8')
        )
        self.producer.flush()

class AtomicSimulator(Sender):
    """Simulator for atomic-DEVS that communicates via Kafka"""

    def __init__(self, model, broker="localhost:9092"):
        super().__init__(broker)
        self.model = model
        self.time_last = 0.0
        self.time_next = 0.0
        
        # Setup Kafka consumer
        self.consumer = Consumer({
            'bootstrap.servers': broker,
            'group.id': f'atomic_{model.name}',
            'auto.offset.reset': 'earliest' 
        })
        
        # Subscribe to model's input topic
        self.consumer_topic = f'devs.{model.name}.in'
        self.producer_topic = f'devs.{model.name}.out'
        self.consumer.subscribe([self.consumer_topic])
        
    def process_internal_transition(self):
        """Process internal transition"""
        try:
            # Get output
            output = self.model.outputFnc()
            logger.info("Model %s output: %s", self.model.name, output)
            
            if output:
                message = {
                    'type': 'output',
                    'time': self.time_next,
                    'data': output
                }
                logger.info("Sending message from %s: %s", self.model.name, message)
                
                self.producer.produce(
                    self.producer_topic,
                    json.dumps(message).encode('utf-8')
                )
                self.producer.flush()
                logger.info("Message sent successfully")
                
            # Internal transition
            self.model.intTransition()
            self.time_last = self.time_next
            ta = self.model.timeAdvance()
            self.time_next = self.time_last + ta
            logger.info("Model %s advanced to time %f", self.model.name, self.time_next)
            
        except Exception as e:
            logger.exception("Error in internal transition for %s: %s", self.model.name, e)

    def process_external_transition(self, message):
        """Process external transition"""
        # Update elapsed time
        self.model.elapsed = message['time'] - self.time_last
        
        # External transition
        self.model.myInput = message['data'] 
        self.model.extTransition()
        
        # Update time variables
        self.time_last = message['time']
        ta = self.model.timeAdvance()
        self.time_next = self.time_last + ta
        
    def simulate(self):
        """Main simulation loop"""
        while True:
            msg = self.consumer.poll(1.0)
            
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break
                    
            # Process message
            data = json.loads(msg.value().decode('utf-8'))
            
            if data['type'] == 'internal':
                self.process_internal_transition()
            elif data['type'] == 'external':
                self.process_external_transition(data)

class CoupledSimulator(Sender):
    """Coordinator for coupled DEVS models"""
    
    def __init__(self, model, broker="localhost:9092"):
        super().__init__(broker)
        self.model = model
        self.simulators = {}
        
        # Setup Kafka consumer
        self.consumer = Consumer({
            'bootstrap.servers': broker,
            'group.id': f'coupled_{model.name}',
            'auto.offset.reset': 'earliest'
        })
        
        # Create simulators for components
        for component in model.componentSet:
            if isinstance(component, AtomicDEVS):
                self.simulators[component.name] = AtomicSimulator(component, broker)
            elif isinstance(component, CoupledDEVS):
                self.simulators[component.name] = CoupledSimulator(component, broker)
                
        # Subscribe to output topics of all components
        topics = [f'devs.{name}.out' for name in self.simulators.keys()]
        self.consumer.subscribe(topics)
        
    def route_message(self, source, message):
        """Route output message to connected components"""
        for coupling in self.model.IC + self.model.EIC + self.model.EOC:
            if coupling[0] == source:
                target = coupling[1].hostDEVS
                self.send_message(f'devs.{target.name}.in', {
                    'type': 'external',
                    'time': message['time'], 
                    'data': message['data']
                })
                
    def simulate(self):
        """Main simulation loop"""
        # Start component simulators
        for simulator in self.simulators.values():
            simulator_thread = threading.Thread(target=simulator.simulate)
            simulator_thread.daemon = True
            simulator_thread.start()
            
        # Route messages between components
        while True:
            msg = self.consumer.poll(1.0)
            
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break
                    
            # Route message
            source_model = msg.topic().split('.')[1]
            message = json.loads(msg.value().decode('utf-8'))
            self.route_message(source_model, message)

class Simulator:
    """Main simulation coordinator"""
    
    def __init__(self, model):
        """Initialize simulation"""
        self.model = model
        self.coordinator = CoupledSimulator(model)
        
    def simulate(self, time_limit=float('inf')):
        """Run simulation"""
        # Start coordinator
        coordinator_thread = threading.Thread(target=self.coordinator.simulate)
        coordinator_thread.daemon = True
        coordinator_thread.start()
        
        # Wait for simulation to complete or time limit
        start_time = time.time()
        while time.time() - start_time < time_limit:
            time.sleep(0.1)
