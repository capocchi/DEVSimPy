import subprocess
import shutil
import time
from confluent_kafka.admin import AdminClient
from .kafkaconfig import KAFKA_BOOTSTRAP, KAFKA_CONATINER_NAME, KAFKA_IMAGE
from confluent_kafka import KafkaException, KafkaError

def wait_for_kafka(bootstrap: str, timeout: float = 30.0, interval: float = 1.0):
    """Wait for the Kafka broker to respond on bootstrap, or raise after timeout."""
    admin = AdminClient({"bootstrap.servers": bootstrap})
    start = time.time()
    while True:
        try:
            admin.list_topics(timeout=5)
            return  # Kafka responds, we can continue
        except KafkaException as e:
            err = e.args[0]
            if err.code() == KafkaError._TRANSPORT:
                if time.time() - start > timeout:
                    raise RuntimeError(
                        f"Kafka not responding on {bootstrap} after {timeout} seconds.\n"
                        f"Check that container '{KAFKA_CONATINER_NAME}' is started and healthy."
                    ) from e
                time.sleep(interval)
            else:
                # other Kafka error: re-raise
                raise

def ensure_kafka_broker(
    container_name: str = KAFKA_CONATINER_NAME,
    image: str = KAFKA_IMAGE,
    bootstrap: str = KAFKA_BOOTSTRAP,
):
    """
    Check if a Kafka container is already running, otherwise start or create it.
    Then wait for the Kafka broker to be actually UP before returning.
    Returns the bootstrap address to use in KafkaDEVS.
    """
    # Check that 'docker' is available
    if shutil.which("docker") is None:
        raise RuntimeError(
            "Docker is not available on this machine.\n"
            "Install and start Docker Desktop before running a KafkaDEVS simulation."
        )
    
    # 1) Check if the container already exists
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        existing = result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Unable to call docker: {e}") from e
    
    
    # 2) If it already exists
    if container_name in existing:
        # Check if it is running
        state_res = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True,
        )
        is_running = state_res.stdout.strip().lower() == "true"
        if not is_running:
            # Existing container but stopped: start it
            subprocess.run(["docker", "start", container_name], check=True)
    else:
        kafka_port = bootstrap.split(':')[-1] or "9092"
        # 3) Otherwise, create it with docker run
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{kafka_port}:{kafka_port}",
            "-e", "KAFKA_NODE_ID=1",
            "-e", "KAFKA_PROCESS_ROLES=broker,controller",
            "-e", f"KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:{kafka_port},CONTROLLER://0.0.0.0:9093",
            "-e", f"KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://{KAFKA_BOOTSTRAP}",
            "-e", "KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER",
            "-e", "KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093",
            "-e", "KAFKA_LOG_DIRS=/var/lib/kafka/data",
            "-e", "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1",
            "-e", "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1",
            "-e", "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1",
            "-e", "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0",
            "-e", "KAFKA_AUTO_CREATE_TOPICS_ENABLE=true",
            "-e", "KAFKA_DELETE_TOPIC_ENABLE=true",
            # CLUSTER_ID: valid base64 UUID, fixed for this broker
            "-e", "CLUSTER_ID=VkFMSTEwMDAtMDAwMC00MDAwLTAwMDAtMDAwMDAwMDAwMDAw",
            image,
        ]
        subprocess.run(cmd, check=True)
    
    # 4) Wait for Kafka in the container to be actually UP
    wait_for_kafka(bootstrap)
    return bootstrap