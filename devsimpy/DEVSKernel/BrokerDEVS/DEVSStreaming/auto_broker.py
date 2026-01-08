# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# auto_broker.py ---
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
# Auto-detection and configuration of message brokers for DEVS simulation.
#
# Automatically discovers available brokers, validates connectivity,
# and provides convenient factory methods for broker adapter creation.
# Supports environment variable configuration and intelligent fallbacks.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import os
import socket
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# BROKER TYPES AND STATUS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerType(Enum):
    """Supported message broker types."""

    KAFKA = "kafka"
    MQTT = "mqtt"
    RABBITMQ = "rabbitmq"
    REDIS = "redis"
    UNKNOWN = "unknown"


class BrokerStatus(Enum):
    """Broker connectivity status."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNTESTED = "untested"
    ERROR = "error"


@dataclass
class BrokerInfo:
    """Information about a detected broker."""

    broker_type: BrokerType
    host: str
    port: int
    status: BrokerStatus
    error: Optional[str] = None
    extras: Dict[str, str] = None

    def __post_init__(self):
        if self.extras is None:
            self.extras = {}

    @property
    def address(self) -> str:
        """Get broker address."""
        return f"{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "type": self.broker_type.value,
            "host": self.host,
            "port": str(self.port),
            "status": self.status.value,
            "address": self.address,
            "error": self.error or "",
        }


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# BROKER AUTO-DETECTION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerDetector:
    """Auto-detect available message brokers."""

    # Default broker addresses
    DEFAULT_ADDRESSES = {
        BrokerType.KAFKA: [
            ("localhost", 9092),
            ("kafka", 9092),
            ("127.0.0.1", 9092),
        ],
        BrokerType.MQTT: [
            ("localhost", 1883),
            ("mqtt", 1883),
            ("127.0.0.1", 1883),
        ],
        BrokerType.RABBITMQ: [
            ("localhost", 5672),
            ("rabbitmq", 5672),
            ("127.0.0.1", 5672),
        ],
        BrokerType.REDIS: [
            ("localhost", 6379),
            ("redis", 6379),
            ("127.0.0.1", 6379),
        ],
    }

    def __init__(self, timeout: float = 2.0):
        """
        Initialize broker detector.

        Args:
            timeout: Connection timeout in seconds
        """
        self.timeout = timeout
        self.detected_brokers: List[BrokerInfo] = []

    def detect_all(self) -> List[BrokerInfo]:
        """
        Detect all available brokers.

        Returns:
            List of detected BrokerInfo objects
        """
        self.detected_brokers = []

        # Check each broker type
        for broker_type in BrokerType:
            if broker_type == BrokerType.UNKNOWN:
                continue

            brokers = self._detect_broker_type(broker_type)
            self.detected_brokers.extend(brokers)

        logger.info("Detected %d brokers", len(self.detected_brokers))
        return self.detected_brokers

    def _detect_broker_type(self, broker_type: BrokerType) -> List[BrokerInfo]:
        """
        Detect specific broker type.

        Args:
            broker_type: Type to detect

        Returns:
            List of detected brokers of this type
        """
        brokers = []
        addresses = self.DEFAULT_ADDRESSES.get(broker_type, [])

        for host, port in addresses:
            info = self._test_broker_connection(broker_type, host, port)
            if info:
                brokers.append(info)
                # Only return first available for each type
                return [info]

        return brokers

    def _test_broker_connection(
        self,
        broker_type: BrokerType,
        host: str,
        port: int,
    ) -> Optional[BrokerInfo]:
        """
        Test connection to a broker.

        Args:
            broker_type: Type of broker
            host: Broker hostname/IP
            port: Broker port

        Returns:
            BrokerInfo if available, None otherwise
        """
        try:
            # Quick socket test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                info = BrokerInfo(
                    broker_type=broker_type,
                    host=host,
                    port=port,
                    status=BrokerStatus.AVAILABLE,
                )
                logger.debug("Found %s broker at %s:%d", broker_type.value, host, port)
                return info

        except Exception as e:
            logger.debug("Error testing %s:%d: %s", host, port, e)

        return None

    def get_broker_by_type(self, broker_type: BrokerType) -> Optional[BrokerInfo]:
        """
        Get detected broker by type.

        Args:
            broker_type: Type to find

        Returns:
            BrokerInfo if found, None otherwise
        """
        for broker in self.detected_brokers:
            if broker.broker_type == broker_type:
                return broker
        return None

    def is_broker_available(self, broker_type: BrokerType) -> bool:
        """
        Check if specific broker type is available.

        Args:
            broker_type: Type to check

        Returns:
            True if available
        """
        broker = self.get_broker_by_type(broker_type)
        return broker is not None and broker.status == BrokerStatus.AVAILABLE


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# AUTO-CONFIGURATION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class AutoBrokerConfig:
    """
    Automatic broker configuration with environment variable support.

    Priority order:
    1. Explicit environment variables (DEVS_BROKER_TYPE, DEVS_BROKER_HOST, etc.)
    2. Detected available brokers
    3. Default fallback (Kafka on localhost:9092)
    """

    ENV_BROKER_TYPE = "DEVS_BROKER_TYPE"
    ENV_BROKER_HOST = "DEVS_BROKER_HOST"
    ENV_BROKER_PORT = "DEVS_BROKER_PORT"
    ENV_AUTO_DETECT = "DEVS_AUTO_DETECT"

    def __init__(self, auto_detect: bool = True):
        """
        Initialize auto-configuration.

        Args:
            auto_detect: Enable broker auto-detection
        """
        self.auto_detect = auto_detect
        self.detector = BrokerDetector() if auto_detect else None
        self.selected_broker: Optional[BrokerInfo] = None

    def configure(self) -> BrokerInfo:
        """
        Auto-configure broker.

        Returns:
            Selected BrokerInfo

        Raises:
            RuntimeError: If no broker can be configured
        """
        # 1. Check environment variables
        broker = self._from_environment()
        if broker:
            self.selected_broker = broker
            logger.info("Configured broker from environment: %s", broker.address)
            return broker

        # 2. Try auto-detection
        if self.auto_detect and self.detector:
            self.detector.detect_all()
            brokers = self.detector.detected_brokers

            if brokers:
                # Prefer Kafka, then MQTT, then others
                broker = self._select_best_broker(brokers)
                self.selected_broker = broker
                logger.info("Auto-detected broker: %s at %s", broker.broker_type.value, broker.address)
                return broker

        # 3. Fallback to default
        broker = self._get_default_broker()
        self.selected_broker = broker
        logger.warning(
            "Using default broker (not tested): %s",
            broker.address,
        )
        return broker

    def _from_environment(self) -> Optional[BrokerInfo]:
        """
        Get broker config from environment variables.

        Returns:
            BrokerInfo if configured, None otherwise
        """
        broker_type_str = os.environ.get(self.ENV_BROKER_TYPE, "").lower()
        if not broker_type_str:
            return None

        try:
            broker_type = BrokerType(broker_type_str)
        except ValueError:
            logger.warning("Invalid DEVS_BROKER_TYPE: %s", broker_type_str)
            return None

        host = os.environ.get(self.ENV_BROKER_HOST, "localhost")
        port_str = os.environ.get(self.ENV_BROKER_PORT, "")

        if not port_str:
            # Use default port for this broker type
            defaults = BrokerDetector.DEFAULT_ADDRESSES.get(broker_type, [])
            if defaults:
                _, port = defaults[0]
            else:
                port = 9092  # Fallback
        else:
            try:
                port = int(port_str)
            except ValueError:
                logger.warning("Invalid DEVS_BROKER_PORT: %s", port_str)
                return None

        return BrokerInfo(
            broker_type=broker_type,
            host=host,
            port=port,
            status=BrokerStatus.UNTESTED,
        )

    def _select_best_broker(self, brokers: List[BrokerInfo]) -> BrokerInfo:
        """
        Select best available broker from list.

        Priority: Kafka > MQTT > RabbitMQ > Redis

        Args:
            brokers: Available brokers

        Returns:
            Selected BrokerInfo
        """
        priority = {
            BrokerType.KAFKA: 4,
            BrokerType.MQTT: 3,
            BrokerType.RABBITMQ: 2,
            BrokerType.REDIS: 1,
        }

        return max(
            brokers,
            key=lambda b: priority.get(b.broker_type, 0),
        )

    def _get_default_broker(self) -> BrokerInfo:
        """
        Get default broker (Kafka on localhost).

        Returns:
            Default BrokerInfo
        """
        return BrokerInfo(
            broker_type=BrokerType.KAFKA,
            host="localhost",
            port=9092,
            status=BrokerStatus.UNTESTED,
        )

    def validate(self) -> bool:
        """
        Validate selected broker connectivity.

        Returns:
            True if broker is reachable
        """
        if not self.selected_broker:
            return False

        detector = BrokerDetector()
        info = detector._test_broker_connection(
            self.selected_broker.broker_type,
            self.selected_broker.host,
            self.selected_broker.port,
        )

        if info:
            self.selected_broker.status = BrokerStatus.AVAILABLE
            return True
        else:
            self.selected_broker.status = BrokerStatus.UNAVAILABLE
            return False


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# ADAPTER FACTORY
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class AutoBrokerAdapterFactory:
    """Factory for creating broker adapters from detected/configured brokers."""

    @staticmethod
    def create_from_info(broker_info: BrokerInfo):
        """
        Create broker adapter from BrokerInfo.

        Args:
            broker_info: Detected or configured broker info

        Returns:
            BrokerAdapter instance

        Raises:
            ValueError: If broker type is unsupported
            ImportError: If broker library not available
        """
        broker_type = broker_info.broker_type
        address = broker_info.address

        if broker_type == BrokerType.KAFKA:
            try:
                from DEVSKernel.BrokerDEVS.Brokers.kafka.KafkaAdapter import (
                    KafkaAdapter,
                )

                logger.info("Creating Kafka adapter for %s", address)
                return KafkaAdapter(address)
            except ImportError as e:
                logger.error("Kafka library not available: %s", e)
                raise ValueError(f"Kafka support not available") from e

        elif broker_type == BrokerType.MQTT:
            try:
                from DEVSKernel.BrokerDEVS.Brokers.mqtt.MqttAdapter import (
                    MqttAdapter,
                )

                logger.info("Creating MQTT adapter for %s", address)
                return MqttAdapter(broker_info.host)
            except ImportError as e:
                logger.error("MQTT library not available: %s", e)
                raise ValueError(f"MQTT support not available") from e

        elif broker_type == BrokerType.RABBITMQ:
            try:
                from DEVSKernel.BrokerDEVS.Brokers.rabbitmq.RabbitmqAdapter import (
                    RabbitmqAdapter,
                )

                logger.info("Creating RabbitMQ adapter for %s", address)
                return RabbitmqAdapter(address)
            except ImportError as e:
                logger.error("RabbitMQ library not available: %s", e)
                raise ValueError(f"RabbitMQ support not available") from e

        else:
            raise ValueError(
                f"Unsupported broker type: {broker_type.value}"
            )


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CONVENIENCE API
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def auto_configure_broker() -> Tuple[BrokerInfo, bool]:
    """
    Auto-configure broker with auto-detection.

    Returns:
        Tuple of (BrokerInfo, is_validated)

    Example:
        broker_info, validated = auto_configure_broker()
        if validated:
            adapter = AutoBrokerAdapterFactory.create_from_info(broker_info)
    """
    config = AutoBrokerConfig(auto_detect=True)
    broker_info = config.configure()
    validated = config.validate()

    if not validated:
        logger.warning(
            "Selected broker %s not reachable, will attempt to create anyway",
            broker_info.address,
        )

    return broker_info, validated


def create_adapter_auto():
    """
    Create broker adapter with automatic detection and configuration.

    Returns:
        BrokerAdapter instance

    Raises:
        ValueError: If no suitable broker found or creation failed
        ImportError: If required libraries not available
    """
    broker_info, validated = auto_configure_broker()

    if not validated:
        logger.warning(
            "Creating adapter for untested broker at %s",
            broker_info.address,
        )

    adapter = AutoBrokerAdapterFactory.create_from_info(broker_info)
    return adapter


def list_available_brokers() -> List[BrokerInfo]:
    """
    List all available brokers via auto-detection.

    Returns:
        List of detected BrokerInfo objects
    """
    detector = BrokerDetector()
    return detector.detect_all()


def detect_broker_type() -> Optional[BrokerType]:
    """
    Detect primary available broker type.

    Returns:
        BrokerType of first available broker, None if none found
    """
    brokers = list_available_brokers()
    if brokers:
        return brokers[0].broker_type
    return None


def get_broker_status() -> Dict[str, str]:
    """
    Get status of all common brokers.

    Returns:
        Dictionary mapping broker type to status
    """
    detector = BrokerDetector()
    detector.detect_all()

    status = {}
    for broker_type in BrokerType:
        if broker_type == BrokerType.UNKNOWN:
            continue

        broker = detector.get_broker_by_type(broker_type)
        if broker:
            status[broker_type.value] = f"AVAILABLE at {broker.address}"
        else:
            status[broker_type.value] = "UNAVAILABLE"

    return status


def print_broker_status():
    """Print human-readable broker status report."""
    print("\n" + "=" * 70)
    print("DEVS Broker Auto-Detection Report")
    print("=" * 70)

    status = get_broker_status()
    for broker_type, broker_status in status.items():
        print(f"  {broker_type.upper():12} {broker_status}")

    print("=" * 70 + "\n")
