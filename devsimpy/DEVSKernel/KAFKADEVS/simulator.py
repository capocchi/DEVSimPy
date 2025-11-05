#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simulator_kafka_full.py
----------------------
Simulateur DEVS distribué via Kafka, avec retour sur topic output.
Compatible Windows.
"""

import multiprocessing as mp
import time
import json
from kafka import KafkaProducer, KafkaConsumer

# ============================================================================
#  CLASSES DE BASE DEVS
# ============================================================================

from .DEVS import AtomicDEVS, CoupledDEVS
# ============================================================================
#  WORKERS KAFKA
# ============================================================================

class BaseSolverWorker:
    def __init__(self, model, bootstrap_servers="localhost:9092"):
        self.model = model
        self.bootstrap_servers = bootstrap_servers
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        self.consumer = KafkaConsumer(
            f"devs.{model.name}.input",
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            group_id=f"group_{model.name}",
            auto_offset_reset="latest"
        )
        self.running = True

    def send_output(self, data):
        topic = f"devs.{self.model.name}.output"
        self.producer.send(topic, data)
        self.producer.flush()

    def run(self):
        print(f"[{self.__class__.__name__}] Started for '{self.model.name}'")
        for msg in self.consumer:
            if not self.running:
                break
            self.process_message(msg.value)

    def stop(self):
        self.running = False
        self.consumer.close()
        self.producer.close()
        print(f"[{self.__class__.__name__}] Stopped '{self.model.name}'")

class AtomicSolverWorker(BaseSolverWorker):
    def process_message(self, msg):
        t = msg.get("time", 0)
        kind = msg.get("type")
        data = msg.get("data", {})

        if kind == "i":
            self.model.timeLast = 0
            self.model.myTimeAdvance = self.model.timeAdvance()
            self.model.timeNext = self.model.timeLast + self.model.myTimeAdvance
            self.send_output({"event": "init_done", "time": 0})

        elif kind == "*":
            if t != self.model.timeNext:
                print(f"[AtomicSolver] Warning: desync on {self.model.name}")
            self.model.outputFnc()
            self.send_output({"event": "output", "data": self.model.myOutput, "time": t})
            self.model.intTransition()
            self.model.timeLast = t
            self.model.myTimeAdvance = self.model.timeAdvance()
            self.model.timeNext = self.model.timeLast + self.model.myTimeAdvance

        elif kind == "x":
            self.model.myInput = data
            self.model.extTransition()
            self.model.timeLast = t
            self.model.myTimeAdvance = self.model.timeAdvance()
            self.model.timeNext = self.model.timeLast + self.model.myTimeAdvance

        elif kind == "stop":
            self.stop()

class CoupledSolverWorker(BaseSolverWorker):
    def process_message(self, msg):
        t = msg.get("time", 0)
        kind = msg.get("type")
        data = msg.get("data", {})

        if kind == "i":
            for comp in self.model.componentSet:
                topic = f"devs.{comp.name}.input"
                self.producer.send(topic, {"type": "i", "time": 0})
            self.producer.flush()
            self.send_output({"event": "init_done", "time": 0})

        elif kind == "*":
            imm_children = [c for c in self.model.componentSet if c.timeNext <= t]
            self.model.immChildren = imm_children
            dStar = self.model.select(imm_children)
            if dStar:
                topic = f"devs.{dStar.name}.input"
                self.producer.send(topic, {"type": "*", "time": t})
                self.producer.flush()
            self.send_output({"event": "internal_done", "time": t})

        elif kind == "x":
            for comp in self.model.componentSet:
                topic = f"devs.{comp.name}.input"
                self.producer.send(topic, {"type": "x", "time": t, "data": data})
            self.producer.flush()

        elif kind == "stop":
            for comp in self.model.componentSet:
                topic = f"devs.{comp.name}.input"
                self.producer.send(topic, {"type": "stop"})
            self.stop()

# ============================================================================
#  FONCTION GLOBALE POUR WINDOWS
# ============================================================================

def worker_process(model_type, model_name, model_obj, kafka_bootstrap):
    if model_type == "atomic":
        worker = AtomicSolverWorker(model_obj, bootstrap_servers=kafka_bootstrap)
    else:
        worker = CoupledSolverWorker(model_obj, bootstrap_servers=kafka_bootstrap)
    worker.run()

# ============================================================================
#  SIMULATOR
# ============================================================================

class Simulator:
    def __init__(self, model, kafka_bootstrap="localhost:9092", auto_distributed=True):
        self.model = model
        self.kafka_bootstrap = kafka_bootstrap
        self.auto_distributed = auto_distributed
        self.worker_processes = {}

        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )

        self.__augment(self.model)

        if self.auto_distributed:
            self.__init_kafka_workers(self.model)

    def __augment(self, devs):
        devs.timeLast = 0
        devs.timeNext = float('inf')
        devs.myTimeAdvance = 0
        if isinstance(devs, CoupledDEVS):
            for sub in devs.componentSet:
                self.__augment(sub)

    def __init_kafka_workers(self, devs):
        if isinstance(devs, CoupledDEVS):
            for subd in devs.componentSet:
                self.__init_kafka_workers(subd)
            self.__spawn_worker(devs, "coupled")
        else:
            self.__spawn_worker(devs, "atomic")

    def __spawn_worker(self, model, worker_type):
        p = mp.Process(
            target=worker_process,
            args=(worker_type, model.name, model, self.kafka_bootstrap),
            daemon=True
        )
        p.start()
        self.worker_processes[model.name] = p
        print(f"[Simulator] Spawned {worker_type} worker for '{model.name}'")

    def send(self, target_name, msg_type="x", data=None, t=0):
        payload = {"type": msg_type, "time": t, "data": data or {}}
        topic = f"devs.{target_name}.input"
        self.producer.send(topic, payload)
        self.producer.flush()
        print(f"[Simulator] → Sent {msg_type} to {target_name} at t={t}")

    def receive(self, target_name, timeout=5):
        """Attend un message sur le topic output du modèle cible"""
        consumer = KafkaConsumer(
            f"devs.{target_name}.output",
            bootstrap_servers=self.kafka_bootstrap,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            consumer_timeout_ms=int(timeout*1000)
        )
        try:
            for msg in consumer:
                return msg.value
        finally:
            consumer.close()

    def stop_all_workers(self):
        for name, proc in self.worker_processes.items():
            if proc.is_alive():
                proc.terminate()
                print(f"[Simulator] Worker '{name}' terminated.")
        self.worker_processes.clear()
        self.producer.close()

# ============================================================================
#  EXEMPLE D’UTILISATION
# ============================================================================

if __name__ == "__main__":
    atom1 = AtomicDEVS("A1")
    atom2 = AtomicDEVS("A2")
    coupled = CoupledDEVS("C1", [atom1, atom2])

    sim = Simulator(coupled, kafka_bootstrap="localhost:9092")

    # Init racine
    sim.send("C1", msg_type="i", t=0)
    print("Init sent. Waiting for outputs...")
    print(sim.receive("C1"))

    # Envoyer un message externe à A1
    sim.send("A1", msg_type="x", data={"ping": 1}, t=10)
    print(sim.receive("A1"))

    # Trigger transition interne C1
    sim.send("C1", msg_type="*", t=20)
    print(sim.receive("C1"))

    print("\n[Main] Simulation progressing… Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sim.stop_all_workers()
