from confluent_kafka.admin import AdminClient
import logging

from logconfig import configure_logging, LOGGING_LEVEL, kafka_logger
configure_logging()
logger = logging.getLogger("DEVSKernel.Strategies")
logger.setLevel(LOGGING_LEVEL)

def delete_all_topics(bootstrap_server):
    admin = AdminClient({"bootstrap.servers": bootstrap_server})

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