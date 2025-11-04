#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import pickle
import base64
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from typing import Dict, Any, Optional, Union
import threading

from .kafka_logger import get_kafka_logger

# Import de la configuration
from .config import KAFKA_CONFIG

# Import de la configuration
try:
    from .kafka_config import KAFKA_CONFIG
except ImportError:
    KAFKA_CONFIG = {
        'bootstrap_servers': 'localhost:9092',
        'base_topic': 'devs_simulation',
        'producer': {'acks': 'all', 'retries': 3},
        'consumer': {'auto_offset_reset': 'latest', 'enable_auto_commit': True}
    }


class MessageTransformer:
    """
    Client MT (Microservice de Transformation)
    Gère la transformation des messages DEVS complexes en JSON
    avec support pour les objets Python non-sérialisables
    """
    
    # Modes de sérialisation
    MODE_JSON_ONLY = 'json_only'      # Seulement les types JSON natifs
    MODE_MIXED = 'mixed'              # JSON + pickle pour objets complexes
    MODE_PICKLE_FULL = 'pickle_full'  # Tout en pickle (base64)
    
    def __init__(self, mode=MODE_MIXED):
        """
        Args:
            mode: Mode de sérialisation (json_only, mixed, pickle_full)
        """
        self.mode = mode
    
    @staticmethod
    def devs_to_json(model_id: str, msg: tuple, msg_type: str) -> str:
        """
        Convertit un message DEVS en JSON standardisé
        
        Args:
            model_id: Identifiant du modèle cible
            msg: Message DEVS (data, imminent_list, time)
            msg_type: Type de message ('init', 'external', 'internal')
        
        Returns:
            Message JSON sérialisé
        """
        try:
            # Extraire les composants du message
            data = msg[0] if len(msg) > 0 else {}
            imminent = msg[1] if len(msg) > 1 else []
            timestamp = msg[2] if len(msg) > 2 else 0
            
            # Construire le payload
            payload = {
                "target_model_id": model_id,
                "message_type": msg_type,
                "timestamp": float(timestamp),
                "imminent_models": MessageTransformer._serialize_imminent(imminent),
                "data": MessageTransformer._serialize_data(data)
            }
            
            return json.dumps(payload, ensure_ascii=False)
            
        except Exception as e:
            logging.error(f"Error in devs_to_json: {e}")
            raise
    
    @staticmethod
    def _serialize_imminent(imminent) -> list:
        """
        Sérialise la liste des modèles imminents
        
        Args:
            imminent: Liste ou objet représentant les modèles imminents
        
        Returns:
            Liste sérialisée
        """
        if not imminent:
            return []
        
        if isinstance(imminent, list):
            result = []
            for model in imminent:
                if hasattr(model, 'myID'):
                    result.append({
                        'model_id': str(model.myID),
                        'model_type': type(model).__name__
                    })
                else:
                    result.append({
                        'model_id': str(id(model)),
                        'model_type': type(model).__name__
                    })
            return result
        else:
            return [str(imminent)]
    
    @staticmethod
    def _serialize_data(data: Any) -> Dict[str, Any]:
        """
        Sérialise les données DEVS (ports et messages)
        Gère les objets complexes non-sérialisables en JSON
        
        Args:
            data: Dictionnaire {port: message} ou autre structure
        
        Returns:
            Dictionnaire sérialisé
        """
        if not data:
            return {}
        
        if isinstance(data, dict):
            serialized = {}
            
            for key, value in data.items():
                # Sérialiser la clé (port)
                if hasattr(key, 'host') and hasattr(key, 'name'):
                    # C'est un port DEVS
                    key_str = MessageTransformer._serialize_port(key)
                else:
                    key_str = str(key)
                
                # Sérialiser la valeur (message)
                value_serialized = MessageTransformer._serialize_message(value)
                
                serialized[key_str] = value_serialized
            
            return serialized
        
        elif isinstance(data, (int, float, str, bool)):
            return {"__simple_value__": data}
        
        elif isinstance(data, (list, tuple)):
            return {
                "__list__": [MessageTransformer._serialize_message(item) for item in data]
            }
        
        else:
            # Objet complexe - utiliser pickle
            return MessageTransformer._serialize_complex_object(data)
    
    @staticmethod
    def _serialize_port(port) -> str:
        """
        Sérialise un port DEVS en string unique
        
        Args:
            port: Objet IPort ou OPort
        
        Returns:
            String au format "model_id:port_name:port_type"
        """
        try:
            model_id = str(port.host.myID) if hasattr(port.host, 'myID') else str(id(port.host))
            port_name = str(port.name)
            port_type = type(port).__name__
            return f"{model_id}:{port_name}:{port_type}"
        except Exception as e:
            logging.warning(f"Error serializing port: {e}")
            return str(port)
    
    @staticmethod
    def _serialize_message(message: Any) -> Dict[str, Any]:
        """
        Sérialise un message (peut être un objet Message ou une valeur simple)
        
        Args:
            message: Message à sérialiser
        
        Returns:
            Dictionnaire sérialisé
        """
        # Cas 1: Types simples JSON-compatibles
        if isinstance(message, (int, float, str, bool, type(None))):
            return {
                "type": "simple",
                "value": message
            }
        
        # Cas 2: Listes et tuples
        elif isinstance(message, (list, tuple)):
            return {
                "type": "list",
                "value": [MessageTransformer._serialize_message(item) for item in message]
            }
        
        # Cas 3: Dictionnaires
        elif isinstance(message, dict):
            return {
                "type": "dict",
                "value": {str(k): MessageTransformer._serialize_message(v) for k, v in message.items()}
            }
        
        # Cas 4: Objet Message DEVS avec attributs
        elif hasattr(message, '__dict__'):
            try:
                # Essayer d'extraire les attributs importants
                attrs = {}
                for attr_name in dir(message):
                    if not attr_name.startswith('_'):
                        try:
                            attr_value = getattr(message, attr_name)
                            if not callable(attr_value):
                                # Sérialiser récursivement les attributs simples
                                if isinstance(attr_value, (int, float, str, bool, type(None))):
                                    attrs[attr_name] = attr_value
                        except:
                            pass
                
                return {
                    "type": "object",
                    "class": type(message).__name__,
                    "attributes": attrs,
                    "pickle": MessageTransformer._pickle_encode(message)
                }
            except:
                # Si l'extraction échoue, utiliser pickle uniquement
                return MessageTransformer._serialize_complex_object(message)
        
        # Cas 5: Objet complexe - utiliser pickle
        else:
            return MessageTransformer._serialize_complex_object(message)
    
    @staticmethod
    def _serialize_complex_object(obj: Any) -> Dict[str, Any]:
        """
        Sérialise un objet complexe en utilisant pickle + base64
        
        Args:
            obj: Objet Python quelconque
        
        Returns:
            Dictionnaire avec données pickle encodées
        """
        return {
            "type": "complex",
            "class": type(obj).__name__,
            "pickle": MessageTransformer._pickle_encode(obj)
        }
    
    @staticmethod
    def _pickle_encode(obj: Any) -> str:
        """
        Encode un objet Python en pickle puis base64
        
        Args:
            obj: Objet à encoder
        
        Returns:
            String base64
        """
        try:
            pickled = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
            encoded = base64.b64encode(pickled).decode('utf-8')
            return encoded
        except Exception as e:
            logging.error(f"Pickle encoding failed for {type(obj).__name__}: {e}")
            return ""
    
    @staticmethod
    def _pickle_decode(encoded_str: str) -> Any:
        """
        Décode une string base64+pickle en objet Python
        
        Args:
            encoded_str: String base64
        
        Returns:
            Objet Python original
        """
        try:
            decoded = base64.b64decode(encoded_str.encode('utf-8'))
            obj = pickle.loads(decoded)
            return obj
        except Exception as e:
            logging.error(f"Pickle decoding failed: {e}")
            return None
    
    @staticmethod
    def json_to_devs(json_msg: str) -> tuple:
        """
        Convertit un message JSON en format DEVS
        
        Args:
            json_msg: Message JSON sérialisé
        
        Returns:
            Tuple DEVS (data, imminent, time)
        """
        try:
            payload = json.loads(json_msg)
            
            # Reconstruire les données
            data = MessageTransformer._deserialize_data(payload.get("data", {}))
            
            # Reconstruire la liste imminent
            imminent = payload.get("imminent_models", [])
            
            # Extraire le timestamp
            timestamp = payload.get("timestamp", 0)
            
            return (data, imminent, timestamp)
            
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON message: {e}")
            return ({}, [], 0)
        except Exception as e:
            logging.error(f"Error in json_to_devs: {e}")
            return ({}, [], 0)
    
    @staticmethod
    def _deserialize_data(data: Dict[str, Any]) -> Any:
        """
        Désérialise les données JSON vers format DEVS
        
        Args:
            data: Dictionnaire sérialisé
        
        Returns:
            Structure de données DEVS
        """
        if "__simple_value__" in data:
            return data["__simple_value__"]
        
        if "__list__" in data:
            return [MessageTransformer._deserialize_message(item) for item in data["__list__"]]
        
        # Reconstruire le dictionnaire {port: message}
        result = {}
        for key_str, value_data in data.items():
            # Pour l'instant, garder la clé comme string
            # (la reconstruction complète du port nécessiterait l'accès au modèle)
            deserialized_value = MessageTransformer._deserialize_message(value_data)
            result[key_str] = deserialized_value
        
        return result
    
    @staticmethod
    def _deserialize_message(message_data: Dict[str, Any]) -> Any:
        """
        Désérialise un message
        
        Args:
            message_data: Données sérialisées du message
        
        Returns:
            Message reconstruit
        """
        if not isinstance(message_data, dict):
            return message_data
        
        msg_type = message_data.get("type", "simple")
        
        if msg_type == "simple":
            return message_data.get("value")
        
        elif msg_type == "list":
            return [MessageTransformer._deserialize_message(item) 
                    for item in message_data.get("value", [])]
        
        elif msg_type == "dict":
            return {k: MessageTransformer._deserialize_message(v) 
                    for k, v in message_data.get("value", {}).items()}
        
        elif msg_type in ("object", "complex"):
            # Essayer de reconstruire depuis pickle
            pickle_data = message_data.get("pickle", "")
            if pickle_data:
                obj = MessageTransformer._pickle_decode(pickle_data)
                if obj is not None:
                    return obj
            
            # Sinon, retourner les attributs
            return message_data.get("attributes", {})
        
        else:
            return message_data


class KafkaBrokerAdapter:
    """
    Adaptateur pour le message broker Kafka
    Singleton qui gère les connexions producer/consumer
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KafkaBrokerAdapter, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, 
                bootstrap_servers: str = None,
                base_topic: str = None):
        """
        Initialise le broker adapter avec configuration
        """
        if self._initialized:
            return
        
        # Utiliser la configuration du fichier kafka_config.py
        self.bootstrap_servers = bootstrap_servers or KAFKA_CONFIG['bootstrap_servers']
        self.base_topic = base_topic or KAFKA_CONFIG['base_topic']
        self.transformer = MessageTransformer()
        
        # Initialiser le producer avec la config
        try:
            producer_config = KAFKA_CONFIG['producer'].copy()
            producer_config.update({
                'bootstrap_servers': self.bootstrap_servers,
                'value_serializer': lambda v: v.encode('utf-8'),
                'key_serializer': lambda k: k.encode('utf-8') if k else None
            })
            
            self.producer = KafkaProducer(**producer_config)
            logging.info(f"Kafka Producer connected to {self.bootstrap_servers}")
        except KafkaError as e:
            logging.error(f"Failed to create Kafka Producer: {e}")
            self.producer = None
        
        # Dictionnaire des consumers par modèle
        self.consumers = {}
        self._initialized = True
    
        self.kafka_logger = get_kafka_logger()

    def send_message(self, target_model_id, msg, msg_type='external'):
        """Envoie avec logging complet"""
        
        try:
            # Transformer le message
            json_msg = self.transformer.devs_to_json(target_model_id, msg, msg_type)
            
            # Logger la transformation
            self.kafka_logger.log_transform(
                "DEVS→JSON", 
                True, 
                json_msg
            )
            
            # Créer topic
            topic = f"{self.base_topic}.{target_model_id}"
            
            # Envoyer
            future = self.producer.send(topic=topic, key=target_model_id, value=json_msg)
            record_metadata = future.get(timeout=10)
            
            # Logger le succès avec détails
            details = f"Topic: {topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}"
            self.kafka_logger.log_send(target_model_id, msg_type, True, details)
            
            return True
            
        except Exception as e:
            # Logger l'erreur
            self.kafka_logger.log_error("SEND_FAILED", str(e), f"Model: {target_model_id}")
            self.kafka_logger.log_send(target_model_id, msg_type, False, str(e))
            return False
    
    def create_consumer(self, model_id: str, callback) -> Optional[KafkaConsumer]:
        """
        Crée un consumer avec la configuration
        """
        if model_id in self.consumers:
            return self.consumers[model_id]
        
        try:
            topic = f"{self.base_topic}.{model_id}"
            
            consumer_config = KAFKA_CONFIG['consumer'].copy()
            consumer_config.update({
                'bootstrap_servers': self.bootstrap_servers,
                'group_id': f'devs_sim_{model_id}',
                'value_deserializer': lambda m: m.decode('utf-8')
            })
            
            consumer = KafkaConsumer(topic, **consumer_config)
            
            # Lancer un thread pour écouter les messages
            thread = threading.Thread(
                target=self._consume_messages,
                args=(consumer, callback),
                daemon=True
            )
            thread.start()
            
            self.consumers[model_id] = consumer
            logging.info(f"Consumer created for model {model_id} on topic {topic}")
            return consumer
            
        except KafkaError as e:
            logging.error(f"Failed to create consumer for {model_id}: {e}")
            return None
    
    def _consume_messages(self, consumer: KafkaConsumer, callback):
        """
        Boucle de consommation des messages (exécutée dans un thread)
        """
        try:
            for message in consumer:
                json_msg = message.value
                devs_msg = self.transformer.json_to_devs(json_msg)
                callback(devs_msg)
        except Exception as e:
            logging.error(f"Error in consumer thread: {e}")
    
    def close(self):
        """
        Ferme proprement les connexions Kafka
        """
        if self.producer:
            self.producer.close()
        
        for consumer in self.consumers.values():
            consumer.close()
        
        logging.info("Kafka connections closed")
