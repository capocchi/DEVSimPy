# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# InMemoryKafkaWorker.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/21/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

# Requires: pip install confluent-kafka
import threading
import json
import logging
import time

from abc import ABC, abstractmethod
from typing import Dict, Any

from DEVSKernel.KafkaDEVS.logconfig import LOGGING_LEVEL, worker_kafka_logger

logger = logging.getLogger("DEVSKernel.KafkaDEVS.InMemoryKafkaWorker")
logger.setLevel(LOGGING_LEVEL)

try:
	from confluent_kafka import Producer, Consumer
except Exception:
	Producer = None
	Consumer = None

class InMemoryKafkaWorker(threading.Thread, ABC):
	"""Worker thread that manages one atomic model in memory."""

	def __init__(self, model_name, aDEVS, bootstrap_server, in_topic=None, out_topic=None):
		super().__init__(daemon=True)
		self.aDEVS = aDEVS
		self.model_name = model_name
		self.bootstrap_server = bootstrap_server
		self.running = True

		# Topics explicitly provided by the strategy
		self.in_topic = in_topic  ### from coordinator
		self.out_topic = out_topic ### to coordinator
		
		group_id = f"worker-thread-{self.aDEVS.myID}-{int(time.time() * 1000)}"

		# Kafka consumer for the dedicated work topic
		self.consumer = Consumer({
			"bootstrap.servers": bootstrap_server,
			"group.id": group_id,
			"auto.offset.reset": "latest",
			"enable.auto.commit": True,
		})
		self.consumer.subscribe([self.in_topic])

		# Kafka producer to send responses back
		self.producer = Producer({
			"bootstrap.servers": bootstrap_server
		})

		logger.info(
            "  [Thread-%s] Created for model %s (in topic=%s, out topic=%s)",
            self.aDEVS.myID, self.model_name, self.in_topic, self.out_topic
        )
	
	def get_model(self):
		"""Returns the atomic DEVS model managed by this worker."""
		return self.aDEVS
	
	def get_model_label(self):
		return self.model_name
	
	def get_model_time_next(self):
		return self.aDEVS.timeNext
	
	# ------------------------------------------------------------------
	#  DEVS message translation -> model calls
	# ------------------------------------------------------------------

	def do_initialize(self, t:float):
		"""Initialize the atomic model before starting the loop."""
		self.aDEVS.sigma = 0.0
		self.aDEVS.timeLast = 0.0
		self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
		self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance
	
		if self.aDEVS.myTimeAdvance != float("inf"): 
			self.aDEVS.myTimeAdvance += t

	def do_external_transition(self, t, msg):
		"""Perform an external transition on the atomic model."""
		
		port_inputs = {}

		# Build dict {port_obj -> Message(value, time)}
		from DomainInterface.Object import Message
		for pv in msg.portValueList:
			# pv.portIdentifier must match the input port name
			for iport in self.aDEVS.IPorts:
				if iport.name == pv.portIdentifier:
					m = Message(pv.value, t)
					port_inputs[iport] = m
					break
		
		self.aDEVS.myInput = port_inputs

		# update elapsed time. This is necessary for the call to the external
		# transition function, which is used to update the DEVS' state.
		self.aDEVS.elapsed = t - self.aDEVS.timeLast

		self.aDEVS.extTransition()

		# Update time variables:
		self.aDEVS.timeLast = t
		self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
		self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance
		if self.aDEVS.myTimeAdvance != float("inf"): self.aDEVS.myTimeAdvance += t
		self.aDEVS.elapsed = 0

	def do_internal_transition(self, t:float):
		"""Perform an internal transition on the atomic model."""
		
		time_last = self.aDEVS.timeLast
		self.aDEVS.elapsed = t - time_last

		self.aDEVS.intTransition()

		self.aDEVS.timeLast = t
		self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
		self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance
		if self.aDEVS.myTimeAdvance != float('inf'): self.aDEVS.myTimeAdvance += t
		self.aDEVS.elapsed = 0

	def do_output_function(self):
		"""Call outputFnc() on the atomic model and return the outputs."""

		self.aDEVS.outputFnc()

	@abstractmethod
	def _process_standard(self, data: Dict[str, Any]) -> None:
		"""
		Process standard DEVS message format.
		Must be implemented by subclasses.
		
		Args:
			data (dict): Parsed JSON message data
		"""
		...

	# ------------------------------------------------------------------
	#  Main loop
	# ------------------------------------------------------------------

	def run(self):
		logger.info(f"  [Thread-{self.aDEVS.myID}] Started")

		while self.running:
			msg = self.consumer.poll(timeout=0.5)
			if msg is None or msg.error():
				continue

			try:
				raw = msg.value().decode("utf-8")
				data = json.loads(raw)

				worker_kafka_logger.debug(f"[Thread-{self.aDEVS.myID}] IN: topic={msg.topic()} value={raw}")
				
				self._process_standard(data)

			except Exception as e:
				logger.exception("[Thread-%s] Error in run loop: %s", self.aDEVS.myID, e)

		self.consumer.close()
		logger.info(f"  [Thread-{self.aDEVS.myID}] Stopped")


	def stop(self):
		"""Stop the worker thread."""
		self.running = False