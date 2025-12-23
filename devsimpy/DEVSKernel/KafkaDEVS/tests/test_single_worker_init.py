# tests/test_single_worker_init.py
import sys
import time
import builtins
import json
import argparse
import logging
from pathlib import Path
import zipfile
import importlib.util
import tempfile
import shutil

from confluent_kafka import Producer, Consumer

# --------------------------------------------------------------------
# Bootstrap environnement DEVSimPy
# --------------------------------------------------------------------
here = Path(__file__).resolve().parent
project_root = here.parents[2]  # .../devsimpy
sys.path.insert(0, str(project_root))

from config import GLOBAL_SETTINGS, USER_SETTINGS

GLOBAL_SETTINGS["GUI_FLAG"] = False
GLOBAL_SETTINGS["INFINITY"] = float("inf")

builtins.__dict__.update(GLOBAL_SETTINGS)
builtins.__dict__.update(USER_SETTINGS)

from DEVSKernel.KafkaDEVS.MS4Me.auto_kafka import ensure_kafka_broker
from DEVSKernel.KafkaDEVS.MS4Me.kafkaconfig import KAFKA_BOOTSTRAP
from DEVSKernel.KafkaDEVS.InMemoryKafkaWorker import InMemoryKafkaWorker
from DEVSKernel.KafkaDEVS.devs_kafka_messages import (
	SimTime,
	InitSim,
	SimulationDone,
	NextTime,
	ModelDone,
	SendOutput, 
	ModelOutputMessage,
	ExecuteTransition, 
	TransitionDone,
	PortValue,
)
from DEVSKernel.KafkaDEVS.devs_kafka_wire_adapters import StandardWireAdapter
from DEVSKernel.KafkaDEVS.logconfig import configure_logging 

from Domain.Generator.RandomGenerator import RandomGenerator
from Domain.Collector.MessagesCollector import MessagesCollector

def load_atomic_from_amd(amd_path: str, class_name: str = None):
	"""
	Charge dynamiquement un modèle atomique DEVSimPy depuis un .amd (zip).
	- amd_path : chemin du .amd
	- class_name : nom explicite de la classe à instancier (sinon, auto-détection naïve)
	Retourne : instance du modèle atomique.
	"""
	amd_path = Path(amd_path).resolve()


	lib_dir = amd_path.parent 
	sys.path.insert(0, str(lib_dir))

	# 1) dossier temporaire pour extraire le contenu
	tmp_dir = Path(tempfile.mkdtemp(prefix="devsimpy_amd_"))

	try:
		# 2) extraire le zip
		with zipfile.ZipFile(amd_path, "r") as zf:
			zf.extractall(tmp_dir)

		# 3) trouver le .py principal (ici on prend le premier .py trouvé)
		py_files = list(tmp_dir.rglob("*.py"))
		if not py_files:
			raise RuntimeError(f"Aucun fichier .py trouvé dans {amd_path}")

		main_py = py_files[0]

		# 4) import dynamique du module
		spec = importlib.util.spec_from_file_location(main_py.stem, main_py)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)  # type: ignore

		# 5) trouver la classe du modèle
		if class_name is not None:
			model_cls = getattr(module, class_name)
		else:
			# heuristique simple : première classe définie dans le module
			candidates = [
				obj for obj in module.__dict__.values()
				if isinstance(obj, type)
			]
			if not candidates:
				raise RuntimeError(f"Aucune classe trouvée dans {main_py}")
			model_cls = candidates[0]

		# 6) instancier le modèle
		model = model_cls()
		return model

	finally:
		# tu peux choisir de garder le dossier pour debug,
		# sinon on le supprime
		shutil.rmtree(tmp_dir, ignore_errors=True)

# --------------------------------------------------------------------
# CLI + logging
# --------------------------------------------------------------------
def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--mode",
		choices=["summary", "details", "both"],
		default="both",
		help="summary = seulement les résumés, details = seulement les échanges, both = les deux",
	)
	return parser.parse_args()


def configure_log_level(mode: str):
	level = logging.INFO if mode == "summary" else logging.DEBUG
	logging.getLogger().setLevel(level)


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
class _MockBlockModel:
	def __init__(self, label: str):
		self.label = label


def build_workers(bootstrap):
	"""Crée les modèles DEVS, les workers Kafka in-memory, et retourne la liste (worker, in_topic, out_topic)."""

	amd_path = project_root / "Domain" / "FSM" / "QFSM.amd"
	qfsm_model = load_atomic_from_amd(str(amd_path), class_name="QFSM")
	print(f"Modèle chargé depuis AMD : {qfsm_model}")

	randomGen = RandomGenerator()
	randomGen.addOutPort("out")
	randomGen.timeNext = 0.0

	messagesCol = MessagesCollector()
	messagesCol.addInPort("in")
	messagesCol.timeNext = float('inf')

	models = [randomGen, messagesCol]

	workers = []
	for model in models:
		label = model.__class__.__name__

		in_topic = f"test_{label}_0In"
		out_topic = f"test_{label}_out"

		worker = InMemoryKafkaWorker(
			aDEVS=model,
			aDEVS_index=0,
			bootstrap_server=bootstrap,
			in_topic=in_topic,
			out_topic=out_topic,
		)
		worker.start()
		workers.append((worker, in_topic, out_topic))

	return workers


def build_consumer(bootstrap, out_topics, group_id: str):
	consumer = Consumer(
		{
			"bootstrap.servers": bootstrap,
			"group.id": group_id,
			"auto.offset.reset": "earliest",
			"enable.auto.commit": True,
		}
	)
	consumer.subscribe(out_topics)
	return consumer


def send_and_wait_reply(
	producer,
	consumer,
	in_topic,
	out_topics,
	devs_msg,
	corr_id,
	index=0,
	timeout=5.0,
	tag="",
	expected_type=None,  # ex: NextTime ou ModelDone
	mode="both",  # "summary", "details", "both"
):
	wire_payload = StandardWireAdapter.to_wire(devs_msg, corr_id, index=index)
	payload_bytes = json.dumps(wire_payload).encode("utf-8")

	sent_desc = (
		f"{devs_msg.__class__.__name__}"
		f"(t={getattr(getattr(devs_msg, 'time', None), 't', 'NA')}, corr_id={corr_id}) "
		f"sur {in_topic}"
	)

	if mode in ("details", "both"):
		if tag:
			print(f"--- [{tag}] Envoi vers {in_topic} (topics out={out_topics}) ---")
		else:
			print(f"--- Envoi vers {in_topic} (topics out={out_topics}) ---")

	producer.produce(in_topic, value=payload_bytes)
	producer.flush()

	reply = None
	deadline = time.time() + timeout

	while time.time() < deadline:
		msg = consumer.poll(timeout=0.5)
		if msg is None or msg.error():
			continue

		raw = msg.value().decode("utf-8")
		data = json.loads(raw)

		if data.get("correlation_id") != corr_id:
			continue  # autre test

		candidate = StandardWireAdapter.from_wire(data)

		# Si on a un type attendu, on ignore les autres (ex: ignorer ModelDone ici)
		if expected_type is not None and not isinstance(candidate, expected_type):
			continue

		reply = candidate
		if mode in ("details", "both"):
			print(f"    Réponse reçue : {reply}")
		break

	if reply is None:
		summary = f"{in_topic} -> aucune réponse (timeout) pour {sent_desc}"
	else:
		summary = (
			f"{in_topic} -> a répondu {reply.__class__.__name__}"
			f"(corr_id={corr_id}) sur l'un des {out_topics} pour {sent_desc}"
		)

	return reply, summary


# --------------------------------------------------------------------
# Scénarios de test
# --------------------------------------------------------------------
def run_test_init_sim(workers, producer, bootstrap, mode="both"):
	summaries = []
	out_topics = [ot for _, _, ot in workers]

	consumer = build_consumer(bootstrap, out_topics, group_id="test-coord-init")

	corr_id_base = 1.0
	init_msg = InitSim(SimTime(t=0.0))

	for idx, (_, in_topic, _) in enumerate(workers):
		corr_id = corr_id_base + (idx + 1)  # 2.0, 3.0, ...
		reply, summary = send_and_wait_reply(
			producer,
			consumer,
			in_topic=in_topic,
			out_topics=out_topics,
			devs_msg=init_msg,
			corr_id=corr_id,
			index=0,
			timeout=5.0,
			tag=f"InitSim worker {idx}",
			expected_type=NextTime,
			mode=mode,
		)
		summaries.append(summary)

	consumer.close()

	if mode in ("summary", "both"):
		print("\n=== RÉSUMÉ DES TESTS InitSim ===")
		for line in summaries:
			print(" -", line)


def run_test_simulation_done(workers, producer, bootstrap, mode="both"):
	summaries = []
	out_topics = [ot for _, _, ot in workers]

	consumer = build_consumer(bootstrap, out_topics, group_id="test-coord-done")

	sim_done_time = SimTime(t=0.0)

	for idx, (_, in_topic, _) in enumerate(workers):
		corr_id = 1000.0 + idx  # plage différente
		sim_done_msg = SimulationDone(time=sim_done_time)

		reply, summary = send_and_wait_reply(
			producer,
			consumer,
			in_topic=in_topic,
			out_topics=out_topics,
			devs_msg=sim_done_msg,
			corr_id=corr_id,
			index=0,
			timeout=5.0,
			tag=f"SimulationDone worker {idx}",
			expected_type=ModelDone,
			mode=mode,
		)
		summaries.append(summary)

	consumer.close()

	if mode in ("summary", "both"):
		print("\n=== RÉSUMÉ DES SimulationDone ===")
		for line in summaries:
			print(" -", line)


def run_test_send_output(workers, producer, bootstrap, mode="both"):
	"""
	Envoie un SendOutput(t=1.0) à chaque worker et collecte les réponses ModelOutputMessage.
	Hypothèse : les modèles acceptent un SendOutput à t=1.0 après l'InitSim.
	"""
	summaries = []
	out_topics = [ot for _, _, ot in workers]

	# consumer dédié à ce scénario
	consumer = build_consumer(bootstrap, out_topics, group_id="test-coord-sendoutput")

	# temps de sortie à tester
	send_time = SimTime(t=1.0)

	for idx, (_, in_topic, _) in enumerate(workers):
		corr_id = 2000.0 + idx
		send_msg = SendOutput(time=send_time)

		reply, summary = send_and_wait_reply(
			producer,
			consumer,
			in_topic=in_topic,
			out_topics=out_topics,
			devs_msg=send_msg,
			corr_id=corr_id,
			index=0,
			timeout=5.0,
			tag=f"SendOutput worker {idx}",
			expected_type=ModelOutputMessage,  # on attend un ModelOutputMessage
			mode=mode,
		)
		summaries.append(summary)

	consumer.close()

	if mode in ("summary", "both"):
		print("\n=== RÉSUMÉ DES SendOutput ===")
		for line in summaries:
			print(" -", line)
				
def run_test_execute_transition_internal(workers, producer, bootstrap, mode="both"):
	"""
	Teste une transition interne :
	  - on suppose que RandomGenerator a timeAdvance() = 0.0 après InitSim
	  - on envoie ExecuteTransition(time=0.0, modelInputsOption={})
	  - on attend un TransitionDone correspondant
	"""
	summaries = []
	out_topics = [ot for _, _, ot in workers]

	consumer = build_consumer(bootstrap, out_topics, group_id="test-coord-exectrans")

	# temps de transition interne (t = 0.0 pour la première transition)
	trans_time = SimTime(t=0.0)

	for idx, (_, in_topic, _) in enumerate(workers):
		corr_id = 3000.0 + idx
		exec_msg = ExecuteTransition(time=trans_time)

		reply, summary = send_and_wait_reply(
			producer,
			consumer,
			in_topic=in_topic,
			out_topics=out_topics,
			devs_msg=exec_msg,
			corr_id=corr_id,
			index=0,
			timeout=5.0,
			tag=f"ExecuteTransition worker {idx}",
			expected_type=TransitionDone,
			mode=mode,
		)
		summaries.append(summary)

	consumer.close()

	if mode in ("summary", "both"):
		print("\n=== RÉSUMÉ DES ExecuteTransition (interne) ===")
		for line in summaries:
			print(" -", line)

def run_test_execute_transition_external_for_collector(workers, producer, bootstrap, mode="both"):
	"""
	Teste une transition externe pour MessagesCollector :
	  - on suppose que les modèles ont reçu InitSim juste avant
	  - on envoie ExecuteTransition(time=t, inputs=[PortValue(...)] ) sur le worker MessagesCollector
	  - on attend un TransitionDone correspondant
	"""
	summaries = []
	out_topics = [ot for _, _, ot in workers]

	consumer = build_consumer(bootstrap, out_topics, group_id="test-coord-exectrans-collector")

	# temps de l'événement d'entrée (par ex. t = 1.0)
	trans_time = SimTime(t=1.0)

	for idx, (_, in_topic, _) in enumerate(workers):
		# On ne cible que MessagesCollector
		# (RandomGenerator n'a pas d'entrée IN0 dans ce scénario)
		worker_label = "RandomGenerator" if "RandomGenerator" in in_topic else "MessagesCollector"

		corr_id = 4000.0 + idx

		if worker_label == "MessagesCollector":
			# Construire un PortValue sur IN0 avec une valeur de test
			input_pv = PortValue(
				value=[42, 0.0, 0.0],       # ta payload de test
				portIdentifier="IN0",
				portType="list",
			)
			inputs = [input_pv]
		else:
			# Pas d'inputs pour RandomGenerator dans ce scénario
			inputs = None

		exec_msg = ExecuteTransition(trans_time, inputs)

		reply, summary = send_and_wait_reply(
			producer,
			consumer,
			in_topic=in_topic,
			out_topics=out_topics,
			devs_msg=exec_msg,
			corr_id=corr_id,
			index=0,
			timeout=5.0,
			tag=f"ExecuteTransition ext worker {idx} ({worker_label})",
			expected_type=TransitionDone,
			mode=mode,
		)
		summaries.append(summary)

	consumer.close()

	if mode in ("summary", "both"):
		print("\n=== RÉSUMÉ DES ExecuteTransition (externe MessagesCollector) ===")
		for line in summaries:
			print(" -", line)
			
def run_scenario_init(bootstrap, mode):
	workers = build_workers(bootstrap)
	producer = Producer({"bootstrap.servers": bootstrap})
	run_test_init_sim(workers, producer, bootstrap, mode=mode)
	for worker, _, _ in workers:
		worker.stop()
		worker.join()


def run_scenario_sendoutput(bootstrap, mode):
	workers = build_workers(bootstrap)
	producer = Producer({"bootstrap.servers": bootstrap})
	run_test_init_sim(workers, producer, bootstrap, mode=mode)      # pour initialiser
	run_test_send_output(workers, producer, bootstrap, mode=mode)
	for worker, _, _ in workers:
		worker.stop()
		worker.join()


def run_scenario_simdone(bootstrap, mode):
	workers = build_workers(bootstrap)
	producer = Producer({"bootstrap.servers": bootstrap})
	run_test_init_sim(workers, producer, bootstrap, mode=mode)      # pour initialiser
	run_test_simulation_done(workers, producer, bootstrap, mode=mode)
	for worker, _, _ in workers:
		worker.stop()
		worker.join()

def run_scenario_execute_transition_internal(bootstrap, mode):
	workers = build_workers(bootstrap)
	producer = Producer({"bootstrap.servers": bootstrap})

	# 1) InitSim pour initialiser le modèle et calculer le premier ta
	run_test_init_sim(workers, producer, bootstrap, mode=mode)

	# 2) ExecuteTransition interne à t=0.0
	run_test_execute_transition_internal(workers, producer, bootstrap, mode=mode)

	for worker, _, _ in workers:
		worker.stop()
		worker.join()

def run_scenario_execute_transition_external_collector(bootstrap, mode):
	workers = build_workers(bootstrap)
	producer = Producer({"bootstrap.servers": bootstrap})

	# 1) InitSim pour initialiser les modèles
	run_test_init_sim(workers, producer, bootstrap, mode=mode)

	# 2) ExecuteTransition externe avec un PortValue sur IN0 pour MessagesCollector
	run_test_execute_transition_external_for_collector(workers, producer, bootstrap, mode=mode)

	for worker, _, _ in workers:
		worker.stop()
		worker.join()

# --------------------------------------------------------------------
# main
# --------------------------------------------------------------------
def main():
	args = parse_args()
	configure_logging()
	configure_log_level(args.mode)

	bootstrap = ensure_kafka_broker(bootstrap=KAFKA_BOOTSTRAP)

	# run_scenario_init(bootstrap, args.mode)
	# run_scenario_sendoutput(bootstrap, args.mode)
	# run_scenario_execute_transition_internal(bootstrap, args.mode)
	run_scenario_execute_transition_external_collector(bootstrap, args.mode)
	# run_scenario_simdone(bootstrap, args.mode)

if __name__ == "__main__":
	main()
