from confluent_kafka.admin import AdminClient
import logging

logging.basicConfig(
    level=logging.DEBUG,  # tu verras aussi les DEBUG
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),                    # console
        logging.FileHandler("kafka_devssim.log")    # fichier
    ]
)

logger = logging.getLogger(__name__)

def delete_all_topics(bootstrap_servers="localhost:9092"):
    admin = AdminClient({"bootstrap.servers": bootstrap_servers})

    # Récupérer la métadonnée du cluster
    md = admin.list_topics(timeout=10)
    topics = list(md.topics.keys())

    # Optionnel : filtrer les topics internes si tu veux les garder
    # topics = [t for t in topics if not t.startswith("__")]

    logger.info(f"Found {len(topics)} topics:")
    for t in topics:
        print(f"  - {t}")

    if not topics:
        logger.info("No topics to delete.")
        return

    # Lancer la suppression
    fs = admin.delete_topics(topics, operation_timeout=30)

    for topic, f in fs.items():
        try:
            f.result()  # None si succès
            logger.info(f"Topic '{topic}' deleted")
        except Exception as e:
            logger.info(f"Failed to delete topic '{topic}': {e}")

if __name__ == "__main__":
    delete_all_topics()