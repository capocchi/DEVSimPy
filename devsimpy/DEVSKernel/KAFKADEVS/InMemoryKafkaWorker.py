# ---------------------------------------------------------------------------
# Kafka-based IN-MEMORY worker (thread) Class
# ---------------------------------------------------------------------------
# Requires: pip install confluent-kafka
import threading
import json
import logging
import time

from .logconfig import LOGGING_LEVEL, worker_kafka_logger

logger = logging.getLogger("DEVSKernel.KafkaDEVS.InMemoryKafkaWorker")
logger.setLevel(LOGGING_LEVEL)

try:
	from confluent_kafka import Producer, Consumer
except Exception:
	Producer = None
	Consumer = None

class InMemoryKafkaWorker(threading.Thread):
	"""Worker thread that manages one atomic model in memory."""

	def __init__(self, aDEVS, index, bootstrap_servers, in_topic=None, out_topic=None):
		super().__init__(daemon=True)
		self.aDEVS = aDEVS
		self.index = index
		self.bootstrap_servers = bootstrap_servers
		self.running = True

		# Topics explicitement fournis par la stratégie
		self.in_topic = in_topic  ### from coodinator
		self.out_topic = out_topic ### to coordinator
	
		self.aBlock = aDEVS.getBlockModel()
		
		group_id = f"worker-thread-{index}-{int(time.time() * 1000)}"

		# Kafka consumer pour le topic de travail dédié
		self.consumer = Consumer({
			"bootstrap.servers": bootstrap_servers,
			"group.id": group_id,
			"auto.offset.reset": "latest",
			"enable.auto.commit": True,
		})
		self.consumer.subscribe([self.in_topic])

		# Kafka producer pour renvoyer les réponses
		self.producer = Producer({
			"bootstrap.servers": bootstrap_servers
		})

		logger.info(
            "  [Thread-%s] Created for model %s (in topic=%s, out topic=%s)",
            index, self.aBlock.label, self.in_topic, self.out_topic
        )

	def get_index(self):
		"""Returns the index of the model"""
		return self.index
	
	def get_model(self):
		"""Returns the atomic DEVS model managed by this worker."""
		return self.aDEVS
	
	def get_model_label(self):
		return self.aDEVS.getBlockModel().label
	
	def get_model_time_next(self):
		return self.aDEVS.timeNext
	
	# ------------------------------------------------------------------
	#  Traduction message DEVS -> appels sur le modèle
	# ------------------------------------------------------------------

	def do_initialize(self, t:float):
		"""Initialise le modèle atomique avant de démarrer la boucle."""
		self.aDEVS.sigma = 0.0
		self.aDEVS.timeLast = 0.0
		self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
		self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance
	
		if self.aDEVS.myTimeAdvance != float("inf"): 
			self.aDEVS.myTimeAdvance += t

	def do_external_transition(self, t, msg):
		"""Effectue une transition interne sur le modèle atomique."""
		
		port_inputs = {}

		# Construire dict {port_obj -> Message(value, time)}
		from DomainInterface.Object import Message
		for pv in msg.portValueList:
			# pv.portIdentifier doit matcher le nom du port d'entrée
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

		# Udpate time variables:
		self.aDEVS.timeLast = t
		self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
		self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance
		if self.aDEVS.myTimeAdvance != float("inf"): self.aDEVS.myTimeAdvance += t
		self.aDEVS.elapsed = 0

	def do_internal_transition(self, t:float):
		"""Effectue une transition interne sur le modèle atomique."""
		
		time_last = self.aDEVS.timeLast
		self.aDEVS.elapsed = t - time_last

		self.aDEVS.intTransition()

		self.aDEVS.timeLast = t
		self.aDEVS.myTimeAdvance = self.aDEVS.timeAdvance()
		self.aDEVS.timeNext = self.aDEVS.timeLast + self.aDEVS.myTimeAdvance
		if self.aDEVS.myTimeAdvance != float('inf'): self.aDEVS.myTimeAdvance += t
		self.aDEVS.elapsed = 0

	def do_output_function(self):
		"""Appelle outputFnc() sur le modèle atomique et retourne les sorties."""

		self.aDEVS.outputFnc()

	# ------------------------------------------------------------------
	#  Boucle principale
	# ------------------------------------------------------------------

	def run(self):
		logger.info("  [Thread-%s] Started", self.index)

		while self.running:
			msg = self.consumer.poll(timeout=0.5)
			if msg is None or msg.error():
				continue

			try:
				raw = msg.value().decode("utf-8")
				data = json.loads(raw)

				worker_kafka_logger.debug(
					"[Thread-%s] IN: topic=%s value=%s",
					self.index,
					msg.topic(),
					raw,
				)
				
				self._process_standard(data)

			except Exception as e:
				logger.exception("[Thread-%s] Error in run loop: %s", self.index, e)

		self.consumer.close()
		logger.info("  [Thread-%s] Stopped", self.index)


	def stop(self):
		"""Stop the worker thread."""
		self.running = False