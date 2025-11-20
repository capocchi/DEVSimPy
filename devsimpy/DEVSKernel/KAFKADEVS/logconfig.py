### Fichier de configuration du logging pour KafkaDEVS
import logging
from pathlib import Path

### Niveau de logging:
###  - logging.DEBUG pour le dev
###  - logging.INFO pour des traces plus légères
###  - logging.WARNING pour la prod

LOGGING_LEVEL = logging.DEBUG
LOGFILE = "kafkadevs_local.log"

def configure_logging():
    # Racine DEVSimPy = dossier contenant devsimpy-nogui.py / devsimpy.py
    filename = Path(__file__).resolve()
    # filename_without_ext = filename.stem 
    base_dir = filename.parents[2]   # DEVSimPy/
    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"{LOGFILE}"

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
