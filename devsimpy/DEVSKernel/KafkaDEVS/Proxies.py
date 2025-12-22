import time
from typing import Protocol, Dict, Any, List
import json

from confluent_kafka import Producer, Consumer
from DEVSKernel.KafkaDEVS.MS4Me.ms4me_kafka_wire_adapters import StandardWireAdapter
from DEVSKernel.KafkaDEVS.logconfig import coord_kafka_logger
from Patterns.Proxy import AbstractStreamProxy, AbstractReceiverProxy

class BaseMessage(Protocol):
    """Protocol for any message type with serialization support"""
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        ...

class KafkaStreamProxy(AbstractStreamProxy):
    """
    Implémentation concrète du proxy d'envoi utilisant Kafka Producer.
    Encapsule toute la logique d'envoi de messages vers Kafka.
    """
    
    def __init__(self, bootstrap_servers: str, wire_adapter=None):
        """
        Initialise le proxy d'envoi Kafka.
        
        Args:
            bootstrap_servers: Adresse du broker Kafka
            wire_adapter: Adaptateur pour la sérialisation (par défaut: StandardWireAdapter)
        """
        self._producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "enable.idempotence": True,
            "acks": "all",
            "max.in.flight.requests.per.connection": 5,
            "retries": 10,
        })
        self.wire = wire_adapter or StandardWireAdapter
        self._logger = coord_kafka_logger
    
    def send_message(self, topic: str, msg: BaseMessage):
        """
        Envoie un message typé DEVS vers un topic Kafka.
        
        Args:
            topic: Le topic Kafka de destination
            msg: Le message DEVS typé à envoyer
        """
        msg_dict = msg.to_dict()
        payload = json.dumps(msg_dict).encode("utf-8")
        
        self._producer.produce(topic, value=payload)
        self._producer.flush()
        
        self._logger.debug("OUT: topic=%s value=%s", topic, payload)
    
    def flush(self):
        """Force l'envoi immédiat de tous les messages en attente"""
        self._producer.flush()
    
    def close(self):
        """Ferme proprement le producer Kafka"""
        self._producer.flush()
        self._logger.info("KafkaStreamProxy closed")


class KafkaReceiverProxy(AbstractReceiverProxy):
    """
    Implémentation concrète du proxy de réception utilisant Kafka Consumer.
    Encapsule toute la logique de réception et traitement des messages Kafka.
    """
    
    def __init__(self, bootstrap_servers: str, group_id: str, wire_adapter=None):
        """
        Initialise le proxy de réception Kafka.
        
        Args:
            bootstrap_servers: Adresse du broker Kafka
            group_id: Identifiant du groupe de consommateurs
            wire_adapter: Adaptateur pour la désérialisation (par défaut: StandardWireAdapter)
        """
        self._consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
            "session.timeout.ms": 30000,
            "max.poll.interval.ms": 300000,
        })
        self.wire = wire_adapter or StandardWireAdapter
        self._logger = coord_kafka_logger
        self._subscribed_topics = []
    
    def subscribe(self, topics: List[str]):
        """
        S'abonne à une liste de topics Kafka.
        
        Args:
            topics: Liste des noms de topics à écouter
        """
        self._consumer.subscribe(topics)
        self._subscribed_topics = topics
        self._logger.info("Subscribed to topics: %s", topics)
    
    def receive_messages(self, pending: List, timeout: float) -> Dict:
        """
        Attend et collecte les messages des workers spécifiés.
        
        Args:
            pending: Liste des modèles DEVS dont on attend une réponse
            timeout: Temps maximum d'attente en secondes
            
        Returns:
            Dictionnaire mappant chaque modèle à son message reçu
            
        Raises:
            TimeoutError: Si tous les messages attendus ne sont pas reçus
        """
        received = {}
        deadline = time.time() + timeout
        
        # Copie de la liste pour ne pas modifier l'originale
        remaining = list(pending)
        
        while remaining and time.time() < deadline:
            msg = self._consumer.poll(timeout=0.5)
            if msg is None or msg.error():
                continue
            
            try:
                data = json.loads(msg.value().decode("utf-8"))
                
                self._logger.debug(
                    "IN: topic=%s value=%s",
                    msg.topic(),
                    json.dumps(data),
                )
                
                # Désérialisation du message DEVS
                devs_msg = self.wire.from_wire(data)
                model_name = data.get('sender')
                
                if not model_name:
                    self._logger.warning("Message without sender field: %s", data)
                    continue
                
                # Trouve et retire le modèle correspondant
                for i, model in enumerate(remaining):
                    if model.getBlockModel().label == model_name:
                        matched_model = remaining.pop(i)
                        received[matched_model] = devs_msg
                        break
                        
            except json.JSONDecodeError as e:
                self._logger.error("JSON decode error: %s", e)
            except Exception as e:
                self._logger.error("Error processing message: %s", e)
        
        if remaining:
            missing_labels = [m.getBlockModel().label for m in remaining]
            raise TimeoutError(
                f"Kafka timeout: missing responses from models {missing_labels}"
            )
        
        return received
    
    def purge_old_messages(self, max_seconds: float = 2.0) -> int:
        """
        Vide les anciens messages présents dans le topic.
        
        Args:
            max_seconds: Temps maximum pour purger les messages
            
        Returns:
            Nombre de messages purgés
        """
        flushed = 0
        start_flush = time.time()
        
        self._logger.info("Purging old messages...")
        
        while time.time() - start_flush < max_seconds:
            msg = self._consumer.poll(timeout=0.1)
            if msg is None:
                break
            if not msg.error():
                flushed += 1
        
        if flushed > 0:
            self._logger.info("Flushed %s old messages", flushed)
        
        return flushed
    
    def close(self):
        """Ferme proprement le consumer Kafka"""
        self._consumer.close()
        self._logger.info("KafkaReceiverProxy closed")
