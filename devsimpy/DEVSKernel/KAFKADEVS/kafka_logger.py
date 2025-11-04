#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime
from pathlib import Path
import sys

class KafkaActivityLogger:
    """Logger Kafka avec contrôle par booléens"""
    
    def __init__(self, 
                 enabled=True,
                 log_file='kafka_activity.log', 
                 log_to_file=True,
                 log_to_console=False,
                 log_level='INFO'):
        """
        Args:
            enabled: Activer/désactiver complètement le logging
            log_file: Chemin du fichier de log
            log_to_file: Écrire dans un fichier
            log_to_console: Afficher en console
            log_level: Niveau de logging ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        """
        self.enabled = enabled
        
        if not self.enabled:
            # Logger désactivé : utiliser un logger null
            self.logger = logging.getLogger('KafkaActivity')
            self.logger.addHandler(logging.NullHandler())
            self.logger.setLevel(logging.CRITICAL + 1)
            self.stats = {}
            return
        
        self.logger = logging.getLogger('KafkaActivity')
        
        # Convertir le niveau de log
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # Supprimer les handlers existants
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Handler fichier (si activé)
        if log_to_file:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Handler console (si activé)
        if log_to_console:
            console_handler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setLevel(numeric_level)
            
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Compteurs
        self.stats = {
            'total_messages': 0,
            'sent_success': 0,
            'sent_failed': 0,
            'received': 0,
            'errors': 0,
            'transforms': 0
        }
    
    def log_send(self, model_id, msg_type, success, details=None):
        """Log un envoi (respecte KAFKA_LOG_SEND)"""
        if not self.enabled:
            return
        
        # Importer depuis simulator pour accéder aux flags
        try:
            from . import simulator
            if not simulator.KAFKA_LOG_SEND:
                return
        except:
            pass
        
        self.stats['total_messages'] += 1
        
        if success:
            self.stats['sent_success'] += 1
            status = "[OK]"
        else:
            self.stats['sent_failed'] += 1
            status = "[FAIL]"
        
        log_msg = f"{status} SENT | TO: {model_id} | TYPE: {msg_type}"
        if details:
            log_msg += f" | {details}"
        
        self.logger.info(log_msg)
    
    def log_receive(self, model_id, msg_type, details=None):
        """Log une réception (respecte KAFKA_LOG_RECEIVE)"""
        if not self.enabled:
            return
        
        try:
            from . import simulator
            if not simulator.KAFKA_LOG_RECEIVE:
                return
        except:
            pass
        
        self.stats['received'] += 1
        log_msg = f"[<-] RECEIVED | FROM: {model_id} | TYPE: {msg_type}"
        if details:
            log_msg += f" | {details}"
        
        self.logger.info(log_msg)
    
    def log_error(self, error_type, error_msg, context=None):
        """Log une erreur (respecte KAFKA_LOG_ERRORS)"""
        if not self.enabled:
            return
        
        try:
            from . import simulator
            if not simulator.KAFKA_LOG_ERRORS:
                return
        except:
            pass
        
        self.stats['errors'] += 1
        log_msg = f"[!] ERROR | {error_type}: {error_msg}"
        if context:
            log_msg += f" | {context}"
        
        self.logger.error(log_msg)
    
    def log_transform(self, direction, success, data_preview):
        """Log une transformation (respecte KAFKA_LOG_TRANSFORM)"""
        if not self.enabled:
            return
        
        try:
            from . import simulator
            if not simulator.KAFKA_LOG_TRANSFORM:
                return
        except:
            pass
        
        self.stats['transforms'] += 1
        status = "[OK]" if success else "[FAIL]"
        
        preview = str(data_preview)[:100] if data_preview else ""
        preview = preview.encode('ascii', 'ignore').decode('ascii')
        
        self.logger.debug(f"{status} TRANSFORM | {direction} | {preview}...")
    
    def get_stats(self):
        """Retourne les statistiques"""
        return self.stats.copy() if self.enabled else {}
    
    def log_stats(self):
        """Affiche les statistiques (respecte KAFKA_LOG_STATS)"""
        if not self.enabled:
            return
        
        try:
            from . import simulator
            if not simulator.KAFKA_LOG_STATS:
                return
        except:
            pass
        
        total = self.stats.get('total_messages', 0)
        if total == 0:
            return
        
        success_rate = (self.stats['sent_success'] / total * 100) if total > 0 else 0
        
        stats_msg = f"""
========================================
KAFKA ACTIVITY STATISTICS
========================================
Total Messages:    {total}
Sent Successfully: {self.stats['sent_success']} ({success_rate:.1f}%)
Send Failed:       {self.stats['sent_failed']}
Received:          {self.stats['received']}
Transforms:        {self.stats['transforms']}
Errors:            {self.stats['errors']}
========================================
"""
        self.logger.info(stats_msg)

# Instance globale
_KAFKA_LOGGER = None

def get_kafka_logger():
    """Retourne l'instance globale (utilise les paramètres de simulator)"""
    global _KAFKA_LOGGER
    if _KAFKA_LOGGER is None:
        # Importer la config depuis simulator
        try:
            from . import simulator
            _KAFKA_LOGGER = KafkaActivityLogger(
                enabled=simulator.ENABLE_KAFKA_LOGGING,
                log_to_file=simulator.KAFKA_LOG_TO_FILE,
                log_to_console=simulator.KAFKA_LOG_TO_CONSOLE,
                log_level=simulator.KAFKA_LOG_LEVEL
            )
        except:
            # Fallback : logger désactivé
            _KAFKA_LOGGER = KafkaActivityLogger(enabled=False)
    
    return _KAFKA_LOGGER
