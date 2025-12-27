# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# run_worker.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/26/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# Standalone worker process for broker-based DEVS simulation.
#
# Starts a distributed DEVS model worker that connects to a message broker
# (Kafka, MQTT, RabbitMQ, etc.) and processes simulation commands from a
# coordinator. Can auto-detect broker or use explicit configuration.
#
# Usage:
#   python run_worker.py <model_file> <model_class> [options]
#
# Examples:
#   # Auto-detect broker
#   python run_worker.py models/system.py SimpleModel
#
#   # Explicit Kafka configuration
#   python run_worker.py models/system.py Model1 --broker kafka --host localhost --port 9092
#
#   # Use MQTT with MS4Me worker
#   python run_worker.py models/system.py Model1 --broker mqtt --ms4me
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import sys
import os
import argparse
import logging
import signal
import importlib.util
from pathlib import Path
from typing import Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# UTILITY FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def load_model_class(file_path: str, class_name: str) -> Any:
    """
    Dynamically load a model class from a Python file.

    Args:
        file_path: Path to Python file containing model
        class_name: Name of model class to load

    Returns:
        Model class

    Raises:
        FileNotFoundError: If file doesn't exist
        AttributeError: If class not found
        SyntaxError: If file has syntax errors
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Model file not found: {file_path}")

    logger.info("Loading model class %s from %s", class_name, file_path)

    # Load module from file
    spec = importlib.util.spec_from_file_location(
        file_path.stem,
        file_path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    # Get class from module
    if not hasattr(module, class_name):
        available = [
            name
            for name in dir(module)
            if not name.startswith("_") and isinstance(getattr(module, name), type)
        ]
        raise AttributeError(
            f"Class {class_name} not found in {file_path}. "
            f"Available classes: {', '.join(available)}"
        )

    model_class = getattr(module, class_name)
    logger.info("Successfully loaded model class: %s", class_name)

    return model_class


def create_broker_adapter(
    broker_type: Optional[str],
    host: Optional[str],
    port: Optional[int],
):
    """
    Create broker adapter from explicit config or auto-detect.

    Args:
        broker_type: Broker type (kafka, mqtt, rabbitmq) or None for auto-detect
        host: Broker host or None for auto-detect
        port: Broker port or None for auto-detect

    Returns:
        BrokerAdapter instance

    Raises:
        ValueError: If broker configuration invalid
    """
    from devsimpy.DEVSKernel.BrokerDEVS.MS4Me.auto_broker import (
        AutoBrokerConfig,
        AutoBrokerAdapterFactory,
        BrokerType,
    )

    if broker_type:
        # Explicit configuration
        try:
            btype = BrokerType(broker_type.lower())
        except ValueError:
            raise ValueError(
                f"Unknown broker type: {broker_type}. "
                f"Supported: kafka, mqtt, rabbitmq"
            )

        config = AutoBrokerConfig(auto_detect=False)

        if host:
            config.selected_broker = config._from_environment()
            if not config.selected_broker:
                from devsimpy.DEVSKernel.BrokerDEVS.MS4Me.auto_broker import BrokerInfo, BrokerStatus

                config.selected_broker = BrokerInfo(
                    broker_type=btype,
                    host=host,
                    port=port or 9092,
                    status=BrokerStatus.UNTESTED,
                )
        else:
            # Use defaults for this broker type
            config.selected_broker = config._from_environment()
            if not config.selected_broker:
                from devsimpy.DEVSKernel.BrokerDEVS.MS4Me.auto_broker import (
                    BrokerDetector,
                    BrokerInfo,
                    BrokerStatus,
                )

                defaults = BrokerDetector.DEFAULT_ADDRESSES.get(btype, [])
                if defaults:
                    host, port = defaults[0]
                else:
                    host, port = "localhost", 9092

                config.selected_broker = BrokerInfo(
                    broker_type=btype,
                    host=host,
                    port=port,
                    status=BrokerStatus.UNTESTED,
                )

        logger.info(
            "Using explicit broker configuration: %s at %s:%d",
            broker_type,
            config.selected_broker.host,
            config.selected_broker.port,
        )
    else:
        # Auto-detect
        config = AutoBrokerConfig(auto_detect=True)
        config.configure()

        if not config.selected_broker:
            raise ValueError("No broker configured or detected")

        logger.info(
            "Auto-detected broker: %s at %s:%d",
            config.selected_broker.broker_type.value,
            config.selected_broker.host,
            config.selected_broker.port,
        )

    # Create adapter
    adapter = AutoBrokerAdapterFactory.create_from_info(config.selected_broker)
    return adapter


def create_worker(
    model_instance: Any,
    adapter,
    use_ms4me: bool = True,
    **worker_kwargs,
):
    """
    Create appropriate worker for model.

    Args:
        model_instance: DEVS model instance
        adapter: BrokerAdapter instance
        use_ms4me: Use MS4Me worker if True, else generic worker
        **worker_kwargs: Additional arguments for worker

    Returns:
        Worker instance (BrokerMS4MeWorker or InMemoryBrokerWorker)
    """
    if use_ms4me:
        from DEVSKernel.BrokerDEVS.Workers.BrokerMS4MeWorker import (
            BrokerMS4MeWorker,
        )

        logger.info("Creating MS4Me worker")
        return BrokerMS4MeWorker(model_instance, adapter, **worker_kwargs)
    else:
        from DEVSKernel.BrokerDEVS.Workers.InMemoryBrokerWorker import (
            InMemoryBrokerWorker,
        )

        logger.info("Creating generic broker worker")
        return InMemoryBrokerWorker(model_instance, adapter, **worker_kwargs)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# SIGNAL HANDLING
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class WorkerProcessManager:
    """Manages worker process lifecycle and signals."""

    def __init__(self, worker):
        """
        Initialize manager.

        Args:
            worker: Worker instance to manage
        """
        self.worker = worker
        self.running = True

    def setup_signal_handlers(self):
        """Setup SIGINT and SIGTERM handlers."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle termination signals."""
        logger.info("Received signal %d, shutting down gracefully", signum)
        self.running = False
        self.worker.stop()

    def run(self):
        """Run worker until stopped."""
        try:
            logger.info("Starting worker, press Ctrl+C to stop")
            self.worker.start()

            # Keep main thread alive for signal handling
            while self.running and self.worker.is_running():
                import time

                time.sleep(0.1)

            logger.info("Worker stopped")

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            self.worker.stop()
        except Exception as e:
            logger.error("Worker error: %s", e, exc_info=True)
            self.worker.stop()
            raise


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# COMMAND-LINE INTERFACE
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a DEVS model as a distributed worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect broker and run with MS4Me worker
  python run_worker.py models/system.py SimpleModel

  # Use explicit Kafka configuration
  python run_worker.py models/system.py Model1 \\
    --broker kafka --host kafka-broker.local --port 9092

  # Use MQTT with standard worker (no MS4Me)
  python run_worker.py models/system.py Model1 \\
    --broker mqtt --host mqtt.local --no-ms4me

  # Enable verbose logging
  python run_worker.py models/system.py Model1 --debug

  # Custom checkpoint interval
  python run_worker.py models/system.py Model1 \\
    --checkpoint-interval 50
        """,
    )

    # Positional arguments
    parser.add_argument(
        "model_file",
        help="Path to Python file containing DEVS model",
    )
    parser.add_argument(
        "model_class",
        help="Name of model class to instantiate",
    )

    # Broker configuration
    broker_group = parser.add_argument_group("Broker Configuration")
    broker_group.add_argument(
        "--broker",
        choices=["kafka", "mqtt", "rabbitmq"],
        help="Broker type (auto-detected if not specified)",
    )
    broker_group.add_argument(
        "--host",
        help="Broker host/hostname",
    )
    broker_group.add_argument(
        "--port",
        type=int,
        help="Broker port",
    )

    # Worker configuration
    worker_group = parser.add_argument_group("Worker Configuration")
    worker_group.add_argument(
        "--ms4me / --no-ms4me",
        dest="use_ms4me",
        default=True,
        help="Use MS4Me worker (default: True)",
    )
    worker_group.add_argument(
        "--checkpoint-interval",
        type=int,
        default=100,
        help="Transitions between checkpoints (default: 100)",
    )
    worker_group.add_argument(
        "--request-timeout",
        type=float,
        default=30.0,
        help="Coordinator request timeout in seconds (default: 30.0)",
    )
    worker_group.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum message send retries (default: 3)",
    )

    # Logging
    logging_group = parser.add_argument_group("Logging")
    logging_group.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    logging_group.add_argument(
        "--log-file",
        help="Log file path (default: stdout)",
    )

    return parser.parse_args()


def setup_logging(debug: bool = False, log_file: Optional[str] = None):
    """
    Setup logging configuration.

    Args:
        debug: Enable debug logging
        log_file: Log file path or None for stdout
    """
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Update root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handler
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    logger.info("Logging configured (level=%s)", log_level)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MAIN
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def main():
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_arguments()

        # Setup logging
        setup_logging(debug=args.debug, log_file=args.log_file)

        logger.info("=" * 70)
        logger.info("DEVS Distributed Worker")
        logger.info("=" * 70)

        # Load model
        logger.info("Loading model...")
        model_class = load_model_class(args.model_file, args.model_class)
        model_instance = model_class()
        logger.info("Model loaded: %s", args.model_class)

        # Create broker adapter
        logger.info("Configuring broker...")
        adapter = create_broker_adapter(
            args.broker,
            args.host,
            args.port,
        )
        logger.info("Broker adapter created: %s", adapter.broker_name)

        # Create worker
        logger.info("Creating worker...")
        worker_kwargs = {
            "enable_checkpointing": args.use_ms4me,
            "checkpoint_interval": args.checkpoint_interval,
            "max_retries": args.max_retries,
        }

        worker = create_worker(
            model_instance,
            adapter,
            use_ms4me=args.use_ms4me,
            **worker_kwargs,
        )
        logger.info("Worker created and ready")

        # Run worker
        logger.info("=" * 70)
        manager = WorkerProcessManager(worker)
        manager.setup_signal_handlers()
        manager.run()

        logger.info("=" * 70)
        logger.info("Worker shutdown complete")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
