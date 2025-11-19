### Fichier de configuration du logging pour KafkaDEVS
import logging
import os, sys
from pathlib import Path

### Niveau de logging:
###  - logging.DEBUG pour le dev
###  - logging.INFO pour des traces plus légères
###  - logging.WARNING pour la prod

LOGGING_LEVEL = logging.DEBUG

def configure_logging():
    # Racine DEVSimPy = dossier contenant devsimpy-nogui.py / devsimpy.py
    base_dir = Path(__file__).resolve().parents[2]   # DEVSimPy/
    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "kafkadevs.log"

    logging.basicConfig(
        level=LOGGING_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),   # console (optionnel)
        ],
    )

# logger dédié pour les traces Kafka
kafka_logger = logging.getLogger("kafka.trace")
kafka_logger.setLevel(LOGGING_LEVEL)
