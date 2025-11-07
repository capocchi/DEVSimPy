# atomic_worker.py
import os, json, argparse, sys
from confluent_kafka import Consumer, Producer
from DEVSKernel.KafkaDEVS.simulator import AtomicSolver

def build_atomic_instance(atomic_id: str):
    # TODO: adapter à votre modèle: soit via une fabrique, soit via un registre picklable.
    # Exemples:
    # if atomic_id == "1": return MyGenerator("G1")
    # if atomic_id == "2": return MyProcessor("P1")
    # Ici, on suppose un point d’extension externalisé.
    raise NotImplementedError("Provide a factory to create the atomic model for id=" + atomic_id)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--single", action="store_true")
    parser.add_argument("--atomic-id", type=str, default=os.getenv("ATOMIC_ID"))
    args = parser.parse_args()

    BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    CMD_TOPIC = os.getenv("CMD_TOPIC", "strategy.commands")
    EVT_TOPIC = os.getenv("EVT_TOPIC", "strategy.events")
    GROUP_ID = os.getenv("WORKER_GROUP_ID", "atomic-workers")

    prod = Producer({"bootstrap.servers": BOOTSTRAP, "enable.idempotence": True, "acks": "all"})
    cons = Consumer({
        "bootstrap.servers": BOOTSTRAP,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest"
    })
    cons.subscribe([CMD_TOPIC])

    # Mono-atomic
    if args.single:
        if not args.atomic_id:
            print("Missing --atomic-id", file=sys.stderr); sys.exit(2)
        aid = str(args.atomic_id)
        a = build_atomic_instance(aid)

        def send_evt(payload):
            prod.produce(EVT_TOPIC, json.dumps(payload), key=aid)
            prod.poll(0)

        def loop_single():
            while True:
                msg = cons.poll(0.2)
                if msg is None or msg.error():
                    continue
                data = json.loads(msg.value().decode())
                if data.get("atomic_id") != aid:
                    continue
                op = data.get("op"); t = data.get("t"); corr_id = data.get("corr_id")
                if op == "init":
                    AtomicSolver.receive(a, [0, None, t])
                    send_evt({"op": "ack", "t": t, "corr_id": corr_id, "myTimeAdvance": a.myTimeAdvance})
                elif op == "step-int":
                    y = AtomicSolver.receive(a, [1, None, t])
                    y_named = {}
                    if isinstance(y, dict):
                        for p, v in y.items():
                            y_named[getattr(p, "name", "OUT")] = v
                    send_evt({"op": "y", "t": t, "corr_id": corr_id, "y": y_named, "myTimeAdvance": a.myTimeAdvance})
                elif op == "step-ext":
                    xin = {}
                    n2p = {p.name: p for p in a.IPorts}
                    for name, val in (data.get("inputs") or {}).items():
                        if name in n2p:
                            xin[n2p[name]] = val
                    AtomicSolver.receive(a, [xin, None, t])
                    send_evt({"op": "ack", "t": t, "corr_id": corr_id, "myTimeAdvance": a.myTimeAdvance})
                elif op == "state-ack":
                    send_evt({"op": "ack-state", "t": t, "corr_id": corr_id, "myTimeAdvance": a.myTimeAdvance})
                elif op == "shutdown":
                    send_evt({"op": "ack", "t": t, "corr_id": corr_id})
                    break

        try:
            loop_single()
        finally:
            cons.close()
        return

    # Mode multi-atomics (REGISTRY) si vous le conservez
    # ...

if __name__ == "__main__":
    main()
