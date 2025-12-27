### conf file for BrokerDEVS
import logging
from pathlib import Path

### logging level:
###  - logging.DEBUG for dev
###  - logging.INFO for light traces
###  - logging.WARNING for prod

LOGGING_LEVEL = logging.DEBUG
LOGFILE = "kafkadevs_local.log"

def configure_logging():
    # DEVSimPy root dir
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
            logging.StreamHandler(),   # console (opt.)
        ],
    )

# logger dedicated to Kafka
worker_kafka_logger = logging.getLogger("worker.kafka.trace")
worker_kafka_logger.setLevel(LOGGING_LEVEL)

coord_kafka_logger = logging.getLogger("coord.kafka.trace")
coord_kafka_logger.setLevel(LOGGING_LEVEL)