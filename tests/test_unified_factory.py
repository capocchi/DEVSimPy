# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# test_unified_factory.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/28/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# Unit tests for the unified worker factory system.
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, MagicMock, patch

from devsimpy.DEVSKernel.BrokerDEVS.simulation_config import (
    SimulationConfig,
    AutoSimulationConfig,
    auto_configure_simulation,
)
from devsimpy.DEVSKernel.BrokerDEVS.worker_factory import WorkerFactory
from devsimpy.DEVSKernel.BrokerDEVS.standard_registry import (
    StandardRegistry,
    MessageStandard,
    BrokerType,
    StandardWorkerBase,
)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MOCK IMPLEMENTATIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class TestMqttWorker(StandardWorkerBase):
    """Mock MQTT worker for testing."""
    
    def connect(self):
        pass
    
    def disconnect(self):
        pass
    
    def send_message(self, topic, message):
        return True
    
    def receive_message(self, topic, timeout=1.0):
        return None


class TestKafkaWorker(StandardWorkerBase):
    """Mock Kafka worker for testing."""
    
    def connect(self):
        pass
    
    def disconnect(self):
        pass
    
    def send_message(self, topic, message):
        return True
    
    def receive_message(self, topic, timeout=1.0):
        return None


class TestStandard:
    """Mock standard for testing."""
    MQTT_WORKER = TestMqttWorker
    KAFKA_WORKER = TestKafkaWorker


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# TESTS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class TestSimulationConfig:
    """Test SimulationConfig dataclass."""
    
    def test_basic_creation(self):
        """Test basic SimulationConfig creation."""
        config = SimulationConfig(
            broker_type='mqtt',
            broker_host='localhost',
            broker_port=1883,
            message_standard='ms4me',
        )
        
        assert config.broker_type == 'mqtt'
        assert config.broker_host == 'localhost'
        assert config.broker_port == 1883
        assert config.message_standard == 'ms4me'
    
    def test_with_authentication(self):
        """Test config with authentication."""
        config = SimulationConfig(
            broker_type='mqtt',
            broker_host='localhost',
            broker_port=1883,
            message_standard='ms4me',
            username='user',
            password='pass',
        )
        
        assert config.username == 'user'
        assert config.password == 'pass'
    
    def test_broker_address_property(self):
        """Test broker_address convenience property."""
        config = SimulationConfig(
            broker_type='mqtt',
            broker_host='example.com',
            broker_port=1883,
            message_standard='ms4me',
        )
        
        assert config.broker_address == 'example.com:1883'
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = SimulationConfig(
            broker_type='kafka',
            broker_host='localhost',
            broker_port=9092,
            message_standard='ms4me',
            username='user',
            password='pass',
        )
        
        config_dict = config.to_dict()
        assert config_dict['broker_type'] == 'kafka'
        assert config_dict['broker_host'] == 'localhost'
        assert config_dict['broker_port'] == 9092
        assert config_dict['message_standard'] == 'ms4me'
        assert config_dict['broker_address'] == 'localhost:9092'


class TestStandardRegistry:
    """Test message standard registry."""
    
    def setup_method(self):
        """Setup before each test."""
        # Clear registry
        StandardRegistry._standards.clear()
    
    def test_register_standard(self):
        """Test registering a standard."""
        StandardRegistry.register_standard(
            MessageStandard.GENERIC,
            {
                BrokerType.MQTT: TestMqttWorker,
                BrokerType.KAFKA: TestKafkaWorker,
            }
        )
        
        # Verify registration
        assert MessageStandard.GENERIC in StandardRegistry._standards
        assert len(StandardRegistry._standards[MessageStandard.GENERIC]) == 2
    
    def test_get_worker_class(self):
        """Test retrieving worker class."""
        StandardRegistry.register_standard(
            MessageStandard.GENERIC,
            {
                BrokerType.MQTT: TestMqttWorker,
                BrokerType.KAFKA: TestKafkaWorker,
            }
        )
        
        worker = StandardRegistry.get_worker_class(
            MessageStandard.GENERIC,
            BrokerType.MQTT
        )
        assert worker == TestMqttWorker
    
    def test_get_worker_class_unsupported(self):
        """Test error when combination not supported."""
        StandardRegistry.register_standard(
            MessageStandard.GENERIC,
            {BrokerType.MQTT: TestMqttWorker}
        )
        
        worker = StandardRegistry.get_worker_class(
            MessageStandard.GENERIC,
            BrokerType.KAFKA
        )
        assert worker is None
    
    def test_is_supported(self):
        """Test checking if combination is supported."""
        StandardRegistry.register_standard(
            MessageStandard.GENERIC,
            {BrokerType.MQTT: TestMqttWorker}
        )
        
        assert StandardRegistry.is_supported(
            MessageStandard.GENERIC,
            BrokerType.MQTT
        )
        assert not StandardRegistry.is_supported(
            MessageStandard.GENERIC,
            BrokerType.KAFKA
        )
    
    def test_list_standards(self):
        """Test listing registered standards."""
        StandardRegistry.register_standard(
            MessageStandard.GENERIC,
            {BrokerType.MQTT: TestMqttWorker}
        )
        
        standards = StandardRegistry.list_standards()
        assert MessageStandard.GENERIC in standards
    
    def test_list_brokers_for_standard(self):
        """Test listing supported brokers."""
        StandardRegistry.register_standard(
            MessageStandard.GENERIC,
            {
                BrokerType.MQTT: TestMqttWorker,
                BrokerType.KAFKA: TestKafkaWorker,
            }
        )
        
        brokers = StandardRegistry.list_brokers_for_standard(MessageStandard.GENERIC)
        assert BrokerType.MQTT in brokers
        assert BrokerType.KAFKA in brokers


class TestWorkerFactory:
    """Test worker factory."""
    
    def setup_method(self):
        """Setup before each test."""
        StandardRegistry._standards.clear()
        StandardRegistry.register_standard(
            MessageStandard.GENERIC,
            {
                BrokerType.MQTT: TestMqttWorker,
                BrokerType.KAFKA: TestKafkaWorker,
            }
        )
    
    def test_create_worker(self):
        """Test creating a worker."""
        config = SimulationConfig(
            broker_type='mqtt',
            broker_host='localhost',
            broker_port=1883,
            message_standard='generic',
        )
        
        mock_model = Mock()
        
        worker = WorkerFactory.create_worker(
            'TestModel',
            mock_model,
            config
        )
        
        assert isinstance(worker, TestMqttWorker)
        assert worker.model_name == 'TestModel'
        assert worker.model == mock_model
    
    def test_create_worker_unsupported_combination(self):
        """Test error on unsupported combination."""
        config = SimulationConfig(
            broker_type='unsupported_broker',
            broker_host='localhost',
            broker_port=9999,
            message_standard='generic',
        )
        
        mock_model = Mock()
        
        with pytest.raises(ValueError):
            WorkerFactory.create_worker('TestModel', mock_model, config)
    
    def test_create_worker_unsupported_standard(self):
        """Test error on unsupported standard."""
        config = SimulationConfig(
            broker_type='mqtt',
            broker_host='localhost',
            broker_port=1883,
            message_standard='unsupported_standard',
        )
        
        mock_model = Mock()
        
        with pytest.raises(ValueError):
            WorkerFactory.create_worker('TestModel', mock_model, config)
    
    def test_get_supported_standards(self):
        """Test getting supported standards."""
        standards = WorkerFactory.get_supported_standards()
        assert 'generic' in standards
    
    def test_get_supported_brokers(self):
        """Test getting supported brokers for standard."""
        brokers = WorkerFactory.get_supported_brokers('generic')
        assert 'mqtt' in brokers
        assert 'kafka' in brokers


class TestAutoSimulationConfig:
    """Test auto-configuration."""
    
    def test_basic_auto_config(self):
        """Test basic auto-configuration."""
        # Mock broker detection
        with patch('devsimpy.DEVSKernel.BrokerDEVS.simulation_config.BrokerDetector') as mock_detector:
            mock_instance = MagicMock()
            mock_detector.return_value = mock_instance
            mock_instance.detect_all.return_value = []
            
            auto_config = AutoSimulationConfig('ms4me')
            config = auto_config.configure()
            
            assert config.message_standard == 'ms4me'
            assert config.broker_type == 'kafka'  # default
            assert config.broker_host == 'localhost'  # default
            assert config.broker_port == 9092  # default
    
    def test_auto_config_from_env(self):
        """Test auto-configuration from environment variables."""
        with patch.dict(os.environ, {
            'DEVS_MESSAGE_STANDARD': 'ms4me',
            'DEVS_BROKER_TYPE': 'mqtt',
            'DEVS_BROKER_HOST': 'example.com',
            'DEVS_BROKER_PORT': '1883',
        }):
            auto_config = AutoSimulationConfig('generic')
            config = auto_config.configure()
            
            assert config.message_standard == 'ms4me'
            assert config.broker_type == 'mqtt'
            assert config.broker_host == 'example.com'
            assert config.broker_port == 1883
    
    def test_auto_configure_convenience_function(self):
        """Test convenience function."""
        with patch.dict(os.environ, {}, clear=True):
            config = auto_configure_simulation(
                standard='ms4me',
                broker='mqtt',
                host='localhost',
                port=1883,
                auto_detect=False,
            )
            
            assert config.message_standard == 'ms4me'
            assert config.broker_type == 'mqtt'
            assert config.broker_host == 'localhost'
            assert config.broker_port == 1883


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MAIN
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
