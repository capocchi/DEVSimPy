### Fichier de configuration du logging pour KafkaDEVS
import logging

### Niveau de logging:
###  - logging.DEBUG pour le dev
###  - logging.INFO pour des traces plus légères
###  - logging.WARNING pour la prod

LOGGING_LEVEL = logging.DEBUG

def configure_logging():
    logging.basicConfig(
        level=logging.DEBUG,  # DEBUG pour le dev et WARNING pour la prod
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),                    # console
            logging.FileHandler("kafka_devssim.log")    # fichier
        ]
    )

# logger dédié pour les traces Kafka
kafka_logger = logging.getLogger("kafka.trace")
kafka_logger.setLevel(LOGGING_LEVEL)
