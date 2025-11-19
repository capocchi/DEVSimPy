import subprocess

def ensure_kafka_broker(
    container_name: str = "kafkabroker",
    image: str = "apache/kafka:latest",
    bootstrap: str = "localhost:9092",
):
    """
    Vérifie si un conteneur Kafka tourne déjà, sinon lance :
      docker run -d --name broker ... apache/kafka:latest
    Retourne l'adresse bootstrap à utiliser dans KafkaDEVS.
    """

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

    # 2) S'il existe mais est arrêté, on le démarre
    if container_name in existing:
        subprocess.run(["docker", "start", container_name], check=True)
        return bootstrap

    # 3) Sinon, on le crée avec docker run
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "-p", "9092:9092",
        "-e", "KAFKA_NODE_ID=1",
        "-e", "KAFKA_PROCESS_ROLES=broker,controller",
        "-e", "KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093",
        "-e", "KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092",
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
    return bootstrap