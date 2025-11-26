#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test pour envoyer des messages DEVS à des workers Kafka.
Example : python test_run_worker.py --scenario full --models MessagesCollector --bootstrap localhost:9092
"""

import sys
import argparse
import json
import time
import logging
from pathlib import Path

import builtins
import os

# Ajouter le répertoire racine du projet au PYTHONPATH
script_dir = Path(__file__).parent.resolve()
devskernel_path = script_dir.parents[1]
project_root = script_dir.parents[2]

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"Added to PYTHONPATH: {project_root}")

setattr(builtins, 'DEFAULT_SIM_STRATEGY', 'ms4Me')
setattr(builtins, 'DEFAULT_DEVS_DIRNAME', 'KafkaDEVS')
setattr(builtins, 'DEVS_SIM_KERNEL_PATH', devskernel_path)
setattr(builtins, 'DEVS_DIR_PATH_DICT', {'KafkaDEVS': os.path.join(devskernel_path, 'KafkaDEVS')})

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("WorkerTester")

try:
    from confluent_kafka import Producer, Consumer
except ImportError:
    logger.error("confluent-kafka not installed. Run: pip install confluent-kafka")
    sys.exit(1)

from DEVSKernel.KafkaDEVS.MS4Me.ms4me_kafka_messages import (
    InitSim,
    SendOutput,
    ExecuteTransition,
    SimulationDone,
    SimTime,
    PortValue,
)
from DEVSKernel.KafkaDEVS.MS4Me.ms4me_kafka_wire_adapters import StandardWireAdapter
from DEVSKernel.KafkaDEVS.MS4Me.MS4MeKafkaWorker import MS4MeKafkaWorker
from DEVSKernel.KafkaDEVS.kafkaconfig import KAFKA_BOOTSTRAP, KAFKA_CONATINER_NAME, KAFKA_IMAGE
from DEVSKernel.KafkaDEVS.auto_kafka import ensure_kafka_broker

class WorkerCoordinatorTester:
    """
    Testeur compatible avec le format MS4MeKafkaWorker
    Version corrigée avec meilleure gestion du consumer
    """
    
    def __init__(self, bootstrap_server, model_labels):
        self.bootstrap = ensure_kafka_broker(
        KAFKA_CONATINER_NAME,
        KAFKA_IMAGE,
        bootstrap_server
    )
        self.model_labels = model_labels if isinstance(model_labels, list) else [model_labels]
        
        self.wire = StandardWireAdapter
        
        group_id = f"coordinator-{int(time.time() * 1000)}"
        
        self.producer = Producer({
            "bootstrap.servers": self.bootstrap,
            "enable.idempotence": True,
            "acks": "all",
        })
        
        # Configuration améliorée du consumer
        self.consumer = Consumer({
            "bootstrap.servers": self.bootstrap,
            "group.id": group_id,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
            "session.timeout.ms": 30000,
            "max.poll.interval.ms": 300000,  # 5 minutes
        })
        
        # Subscribe et attendre l'assignation des partitions
        self.consumer.subscribe([MS4MeKafkaWorker.OUT_TOPIC])
        
        logger.info(f"Coordinator Tester initialized")
        logger.info(f"  Models: {self.model_labels}")
        logger.info(f"  Out topic: {MS4MeKafkaWorker.OUT_TOPIC}")
        logger.info(f"  Bootstrap: {self.bootstrap}")
        logger.info(f"  Consumer group: {group_id}")
        
        self._wait_for_consumer_ready()
    
    def _wait_for_consumer_ready(self, max_seconds=10.0):
        """Attend que le consumer soit prêt et assigné à des partitions"""
        logger.info("Waiting for consumer to be ready...")
        
        start = time.time()
        while time.time() - start < max_seconds:
            # Poll pour déclencher le rebalancing
            msg = self.consumer.poll(timeout=0.5)
            
            # Vérifier si des partitions sont assignées
            assignment = self.consumer.assignment()
            if assignment:
                logger.info(f"  Consumer assigned to {len(assignment)} partition(s)")
                # Purger les anciens messages
                flushed = 0
                while True:
                    msg = self.consumer.poll(timeout=0.1)
                    if msg is None:
                        break
                    flushed += 1
                if flushed > 0:
                    logger.info(f"  Flushed {flushed} old messages")
                logger.info("Consumer ready!")
                return True
        
        logger.warning("Consumer may not be fully ready yet")
        return False
    
    def _send_msg_to_kafka(self, topic, devs_msg):
        """Envoie un message DEVS directement (sans enveloppe)"""
        msg_dict = devs_msg.to_dict()
        payload = json.dumps(msg_dict).encode("utf-8")
        
        self.producer.produce(topic, value=payload)
        self.producer.flush()
        
        logger.debug(f"COORD-OUT topic={topic} value={msg_dict}")
    
    def _await_msgs_from_kafka(self, expected_count, timeout=10.0):
        """
        Attend les réponses des workers
        Timeout augmenté pour laisser le temps au rebalancing
        """
        received = []
        deadline = time.time() + timeout
        consecutive_none = 0
        max_consecutive_none = 20  # Arrêter après 20 polls vides consécutifs
        
        logger.info(f"Waiting for {expected_count} message(s)...")
        
        while len(received) < expected_count and time.time() < deadline:
            msg = self.consumer.poll(timeout=0.5)
            
            if msg is None:
                consecutive_none += 1
                if consecutive_none >= max_consecutive_none:
                    logger.warning(f"No messages after {max_consecutive_none} consecutive polls")
                    break
                continue
            
            consecutive_none = 0  # Reset counter
            
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue
            
            try:
                if msg.value() is None:
                    logger.warning("Received message with None value, skipping")
                    continue
                
                data = json.loads(msg.value().decode("utf-8"))
                logger.debug(f"COORD-IN topic={msg.topic()} value={data}")
                
                # Parser le message directement (sans enveloppe)
                devs_msg = self.wire.from_wire(data)
                sender = data.get('sender', 'unknown')
                received.append((sender, devs_msg))
                
                logger.info(f"  Received {len(received)}/{expected_count} from {sender}")
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                continue
            except Exception as e:
                logger.error(f"Error parsing message: {e}")
                continue
        
        if len(received) < expected_count:
            logger.warning(f"Timeout: expected {expected_count}, got {len(received)}")
        
        return received
    
    def test_init(self):
        """Test InitSim"""
        logger.info("\n" + "="*60)
        logger.info("TEST: InitSim (STEP 0)")
        logger.info("="*60)
        
        st = SimTime(t=0.0)
        
        for label in self.model_labels:
            topic = f"ms4me{label}In"
            logger.info(f"→ Sending InitSim to {label} (topic={topic})")
            self._send_msg_to_kafka(topic, InitSim(st))
        
        # Attendre un peu que le worker traite
        logger.info("Waiting for workers to process...")
        time.sleep(1.0)
        
        responses = self._await_msgs_from_kafka(len(self.model_labels))
        
        logger.info(f"\n← Received {len(responses)} responses:")
        for sender, devs_msg in responses:
            msg_type = type(devs_msg).__name__
            if hasattr(devs_msg, 'time'):
                logger.info(f"  {sender}: {msg_type}(t={devs_msg.time.t})")
            else:
                logger.info(f"  {sender}: {msg_type}")
        
        return responses
    
    def test_send_output(self, current_time=0.0, imminent_labels=None):
        """Test SendOutput"""
        logger.info("\n" + "="*60)
        logger.info("TEST: SendOutput (STEP 1)")
        logger.info("="*60)
        
        if imminent_labels is None:
            imminent_labels = self.model_labels
        
        st = SimTime(t=current_time)
        
        for label in imminent_labels:
            topic = f"ms4me{label}In"
            logger.info(f"→ Sending SendOutput to {label} at t={current_time}")
            self._send_msg_to_kafka(topic, SendOutput(st))
        
        time.sleep(1.0)
        responses = self._await_msgs_from_kafka(len(imminent_labels))
        
        logger.info(f"\n← Received {len(responses)} outputs:")
        for sender, devs_msg in responses:
            msg_type = type(devs_msg).__name__
            if hasattr(devs_msg, 'modelOutput'):
                logger.info(f"  {sender}: {msg_type} outputs={devs_msg.modelOutput}")
            else:
                logger.info(f"  {sender}: {msg_type}")
        
        return responses
    
    def test_execute_transition_internal(self, current_time=0.0, imminent_labels=None):
        """Test ExecuteTransition interne"""
        logger.info("\n" + "="*60)
        logger.info("TEST: ExecuteTransition Internal (STEP 3)")
        logger.info("="*60)
        
        if imminent_labels is None:
            imminent_labels = self.model_labels
        
        st = SimTime(t=current_time)
        
        for label in imminent_labels:
            topic = f"ms4me{label}In"
            logger.info(f"→ Sending ExecuteTransition (internal) to {label}")
            self._send_msg_to_kafka(topic, ExecuteTransition(st, None))
        
        time.sleep(1.0)
        responses = self._await_msgs_from_kafka(len(imminent_labels))
        
        logger.info(f"\n← Received {len(responses)} TransitionDone:")
        for sender, devs_msg in responses:
            msg_type = type(devs_msg).__name__
            if hasattr(devs_msg, 'nextTime'):
                logger.info(f"  {sender}: {msg_type}(nextTime={devs_msg.nextTime.t})")
            else:
                logger.info(f"  {sender}: {msg_type}")
        
        return responses
    
    def test_execute_transition_external(self, label, current_time=0.0, port="IN0", value=None):
        """Test ExecuteTransition externe"""
        logger.info("\n" + "="*60)
        logger.info("TEST: ExecuteTransition External (STEP 2b)")
        logger.info("="*60)
        
        if value is None:
            value = [42, 0.0, 0.0]
        
        st = SimTime(t=current_time)
        pv = PortValue(value=value, portIdentifier=port, portType="list")
        
        topic = f"ms4me{label}In"
        logger.info(f"→ Sending ExecuteTransition (external) to {label}")
        logger.info(f"  Input: {port}={value}")
        self._send_msg_to_kafka(topic, ExecuteTransition(st, [pv]))
        
        time.sleep(1.0)
        responses = self._await_msgs_from_kafka(1)
        
        if responses:
            sender, devs_msg = responses[0]
            msg_type = type(devs_msg).__name__
            if hasattr(devs_msg, 'nextTime'):
                logger.info(f"\n← {sender}: {msg_type}(nextTime={devs_msg.nextTime.t})")
            else:
                logger.info(f"\n← {sender}: {msg_type}")
        
        return responses
    
    def test_simulation_done(self, current_time=0.0):
        """Test SimulationDone"""
        logger.info("\n" + "="*60)
        logger.info("TEST: SimulationDone")
        logger.info("="*60)
        
        st = SimTime(t=current_time)
        
        for label in self.model_labels:
            topic = f"ms4me{label}In"
            logger.info(f"→ Broadcasting SimulationDone to {label}")
            self._send_msg_to_kafka(topic, SimulationDone(time=st))
        
        time.sleep(1.0)
        responses = self._await_msgs_from_kafka(len(self.model_labels), timeout=5.0)
        
        logger.info(f"\n← Received {len(responses)} ModelDone:")
        for sender, devs_msg in responses:
            logger.info(f"  {sender}: {type(devs_msg).__name__}")
        
        return responses
    
    def test_full_scenario(self):
        """Scénario complet DEVS"""
        logger.info("\n" + "="*60)
        logger.info("SCENARIO: Full DEVS Simulation Cycle")
        logger.info("="*60)
        
        # STEP 0: InitSim
        init_responses = self.test_init()
        if not init_responses:
            logger.error("Init failed, stopping")
            return
        
        time.sleep(1.0)
        
        # STEP 1: SendOutput
        output_responses = self.test_send_output(current_time=0.0)
        
        time.sleep(1.0)
        
        # STEP 3: Transition interne
        trans_responses = self.test_execute_transition_internal(current_time=0.0)
        
        time.sleep(1.0)
        
        # Fin: SimulationDone
        self.test_simulation_done(current_time=0.0)
        
        logger.info("\n" + "="*60)
        logger.info("SCENARIO completed")
        logger.info("="*60)
    
    def close(self):
        """Ferme les connexions Kafka"""
        if hasattr(self, 'consumer'):
            self.consumer.close()
        logger.info("Coordinator Tester closed")


def main():
    parser = argparse.ArgumentParser(
        description="Test DEVS messages vers workers Kafka"
    )
    parser.add_argument(
        "--scenario",
        choices=["init", "output", "transition-int", "transition-ext", "done", "full"],
        default="init",
        help="Scénario de test"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["MessagesCollector"],
        help="Labels des modèles cibles"
    )
    parser.add_argument(
        "--bootstrap",
        default=KAFKA_BOOTSTRAP,
        help="Adresse Kafka"
    )
    parser.add_argument(
        "--time",
        type=float,
        default=0.0,
        help="Temps de simulation"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Active DEBUG logs"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = WorkerCoordinatorTester(
        bootstrap_server=args.bootstrap,
        model_labels=args.models
    )
    
    try:
        if args.scenario == "init":
            tester.test_init()
        elif args.scenario == "output":
            tester.test_send_output(args.time)
        elif args.scenario == "transition-int":
            tester.test_execute_transition_internal(args.time)
        elif args.scenario == "transition-ext":
            if len(args.models) == 0:
                logger.error("Specify at least one model for external transition")
                sys.exit(1)
            tester.test_execute_transition_external(args.models[0], args.time)
        elif args.scenario == "done":
            tester.test_simulation_done(args.time)
        elif args.scenario == "full":
            tester.test_full_scenario()
    
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.exception(f"Test failed: {e}")
    finally:
        tester.close()


if __name__ == "__main__":
    main()