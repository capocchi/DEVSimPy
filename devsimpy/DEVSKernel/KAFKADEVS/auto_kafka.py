import subprocess
import shutil
import time

from confluent_kafka.admin import AdminClient
from .kafkaconfig import KAFKA_BOOTSTRAP, KAFKA_CONATINER_NAME, KAFKA_IMAGE
from confluent_kafka import KafkaException, KafkaError

def wait_for_kafka(bootstrap: str, timeout: float = 30.0, interval: float = 1.0):
	"""Attend que le broker Kafka réponde sur bootstrap, ou lève après timeout."""
	admin = AdminClient({"bootstrap.servers": bootstrap})
	start = time.time()

	while True:
		try:
			admin.list_topics(timeout=5)
			return  # Kafka répond, on peut continuer
		except KafkaException as e:
			err = e.args[0]
			if err.code() == KafkaError._TRANSPORT:
				if time.time() - start > timeout:
					raise RuntimeError(
						f"Kafka ne répond pas sur {bootstrap} après {timeout} secondes.\n"
						f"Vérifier que le conteneur '{KAFKA_CONATINER_NAME}' est démarré et en bonne santé."
					) from e
				time.sleep(interval)
			else:
				# autre erreur Kafka : on remonte
				raise

def ensure_kafka_broker(
	container_name: str = KAFKA_CONATINER_NAME,
	image: str = KAFKA_IMAGE,
	bootstrap: str = KAFKA_BOOTSTRAP,
):
	"""
	Vérifie si un conteneur Kafka tourne déjà, sinon le démarre ou le crée.
	Puis attend que le broker Kafka soit réellement UP avant de rendre la main.
	Retourne l'adresse bootstrap à utiliser dans KafkaDEVS.
	"""

	# Vérifier que 'docker' est disponible
	if shutil.which("docker") is None:
		raise RuntimeError(
			"Docker n'est pas disponible sur cette machine.\n"
			"Installe et lance Docker Desktop avant une simulation KafkaDEVS."
		)

	# 1) Vérifier si le conteneur existe déjà
	try:
		result = subprocess.run(
			["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
			capture_output=True,
			text=True,
			check=True,
		)
		existing = result.stdout.strip().splitlines()
	except subprocess.CalledProcessError as e:
		raise RuntimeError(f"Impossible d'appeler docker: {e}") from e


	# 2) S'il existe déjà
	if container_name in existing:
		# Vérifier s'il est en cours d'exécution
		state_res = subprocess.run(
			["docker", "inspect", "-f", "{{.State.Running}}", container_name],
			capture_output=True,
			text=True,
		)
		is_running = state_res.stdout.strip().lower() == "true"

		if not is_running:
			# Conteneur existant mais arrêté : on le démarre
			subprocess.run(["docker", "start", container_name], check=True)
	else:
		# 3) Sinon, on le crée avec docker run
		cmd = [
			"docker", "run", "-d",
			"--name", container_name,
			"-p", "9092:9092",
			"-e", "KAFKA_NODE_ID=1",
			"-e", "KAFKA_PROCESS_ROLES=broker,controller",
			"-e", "KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093",
			"-e", f"KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://{bootstrap}",
			"-e", "KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER",
			"-e", "KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093",
			"-e", "KAFKA_LOG_DIRS=/var/lib/kafka/data",
			"-e", "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1",
			"-e", "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1",
			"-e", "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1",
			"-e", "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0",
			"-e", "KAFKA_AUTO_CREATE_TOPICS_ENABLE=true",
			"-e", "KAFKA_DELETE_TOPIC_ENABLE=true",
			# CLUSTER_ID : UUID base64 valide, fixe pour ce broker
			"-e", "CLUSTER_ID=VkFMSTEwMDAtMDAwMC00MDAwLTAwMDAtMDAwMDAwMDAwMDAw",
			image,
		]
		subprocess.run(cmd, check=True)

	# 4) Attendre que Kafka dans le conteneur soit vraiment UP
	wait_for_kafka(bootstrap)

	return bootstrap