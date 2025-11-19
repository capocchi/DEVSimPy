# ---------------------------------------------------------------------------
# Kafka-based IN-MEMORY worker (thread) Class
# ---------------------------------------------------------------------------
# Requires: pip install confluent-kafka
import threading
import json
import logging

from .logconfig import LOGGING_LEVEL, kafka_logger

logger = logging.getLogger("DEVSKernel.KafkaDEVS.InMemoryKafkaWorker")
logger.setLevel(LOGGING_LEVEL)

try:
	from confluent_kafka import Producer, Consumer
except Exception:
	Producer = None
	Consumer = None

from .devs_kafka_messages import (
	BaseMessage,
	SimTime,
	PortValue,
	InitSim,
	ExecuteTransition,
	SendOutput,
	NextTime,
	TransitionDone,
	ModelOutputMessage,
	SimulationDone,
	ModelDone,
)
from .devs_kafka_wire_adapters import StandardWireAdapter


class InMemoryKafkaWorker(threading.Thread):
	"""Worker thread that manages one atomic model in memory."""

	def __init__(self, atomic_model, atomic_index, bootstrap_servers, mode="local",in_topic=None, out_topic=None):
		super().__init__(daemon=True)
		self.atomic_model = atomic_model
		self.atomic_index = atomic_index
		self.bootstrap_servers = bootstrap_servers
		self.running = True

		# Topics explicitement fournis par la stratégie
		self.in_topic = in_topic  ### from coodinator
		self.out_topic = out_topic ### to coordinator
	
		# Mode de communication :
		#   - "local"  : ancien protocole (operation, inputs, result)
		#   - "standard": messages typés devs.msg.* via StandardWireAdapter

		if mode == "standard":
			self.wire = StandardWireAdapter
		else:
			# En mode local, on n'utilise PAS l'adaptateur pour les requêtes,
			# on garde ton ancien format dans run().
			self.wire = None

		# Kafka consumer pour le topic de travail dédié
		self.consumer = Consumer({
			"bootstrap.servers": bootstrap_servers,
			"group.id": f"worker-thread-{atomic_index}",
			"auto.offset.reset": "earliest",
			"enable.auto.commit": True,
		})
		self.consumer.subscribe([self.in_topic])

		# Kafka producer pour renvoyer les réponses
		self.producer = Producer({
			"bootstrap.servers": bootstrap_servers
		})

		logger.info(
            "  [Thread-%s] Created for model %s (in topic=%s, out topic=%s, mode=%s)",
            atomic_index, atomic_model.getBlockModel().label, self.in_topic, self.out_topic, mode
        )

	def execute_operation(self, operation, work_data):
		"""Execute DEVS operation on the in-memory model"""
		try: 
			if operation == 'init':
				# Appeler la logique d'initialisation du modèle
				ta = self.atomic_model.timeAdvance()
				ta = float(ta) if ta is not None else float('inf')

				# On renvoie juste le ta, la stratégie se chargera de remplir myTimeNext
				return {'status': 'success', 'result': ta}

			elif operation == 'time_advance':
				result = self.atomic_model.timeAdvance()
				return {'status': 'success', 'result': float(result if result is not None else float('inf'))}
		
			elif operation == 'internal_transition':
				result = self.atomic_model.intTransition()
				return {'status': 'success', 'result': str(result)}
			
			elif operation == 'external_transition':
				inputs = work_data.get('inputs', {})
				current_time = work_data.get('current_time', 0.0)
				
				# Construire le dictionnaire port -> message
				port_inputs = {}
				for port_name, value in inputs.items():
					for iport in self.atomic_model.IPorts:
						if iport.name == port_name:
							from DomainInterface.Object import Message
							msg = Message(value, current_time)
							port_inputs[iport] = msg
							break
				
				# Sauvegarder l'ancien peek()
				old_peek = self.atomic_model.peek if hasattr(self.atomic_model, 'peek') else None
				
				# Définir un peek() temporaire qui utilise port_inputs
				def temp_peek(port, *args):
					"""Temporary peek() for Kafka architecture"""
					if args and isinstance(args[0], dict):
						return args[0].get(port)
					return port_inputs.get(port)
				
				# Remplacer peek() temporairement
				self.atomic_model.peek = temp_peek
				
				try:
					# Appeler extTransition avec le dictionnaire
					result = self.atomic_model.extTransition(port_inputs)
				finally:
					# Restaurer l'ancien peek()
					if old_peek:
						self.atomic_model.peek = old_peek
				
				return {'status': 'success', 'result': str(result)}
			
			elif operation == 'output_function':
				current_time = work_data.get('current_time', 0.0)
	
				# Vider myOutput avant d'appeler outputFnc
				self.atomic_model.myOutput = {}
				
				# Appeler outputFnc qui remplit self.myOutput via poke()
				self.atomic_model.outputFnc()
				
				# Lire les valeurs depuis myOutput
				outputs = {}
				for port, msg in self.atomic_model.myOutput.items():
					if msg is not None:
						port_name = port.name if hasattr(port, 'name') else str(port)
						
						outputs[port_name] = {
							'value': msg.value if hasattr(msg, 'value') else msg,
							'time': current_time
						}
				
				return {'status': 'success', 'result': outputs}
			
			else:
				return {'status': 'error', 'message': f'Unknown operation: {operation}'}
		
		except Exception as e:
			import traceback
			return {
				'status': 'error',
				'message': str(e),
				'traceback': traceback.format_exc()
			}
		
	# ------------------------------------------------------------------
	#  Traduction message DEVS -> appels sur le modèle
	# ------------------------------------------------------------------

	def _handle_devs_message(self, msg: BaseMessage) -> BaseMessage:
		"""
		Reçoit un BaseMessage (InitSim, ExecuteTransition, SendOutput, ...)
		et renvoie un BaseMessage de réponse (NextTime, ModelOutputMessage, ...).
		"""

		# --- InitSim : initialisation + timeAdvance initial ---
		if isinstance(msg, InitSim):
			ta = self.atomic_model.timeAdvance()
			ta = float(ta) if ta is not None else float("inf")
			return NextTime(SimTime(t=ta), sender=self.atomic_model.getBlockModel().label)

		# --- ExecuteTransition
		if isinstance(msg, ExecuteTransition):
			t = msg.time.t

			# Si on a des inputs, c'est une extTransition
			if msg.portValueList:
				port_inputs = {}

				# Construire dict {port_obj -> Message(value, time)}
				from DomainInterface.Object import Message
				for pv in msg.portValueList:
					# pv.portIdentifier doit matcher le nom du port d'entrée
					for iport in self.atomic_model.IPorts:
						if iport.name == pv.portIdentifier:
							m = Message(pv.value, t)
							port_inputs[iport] = m
							break

				# Sauvegarder l'ancien peek()
				old_peek = getattr(self.atomic_model, "peek", None)

				def temp_peek(port, *args):
					if args and isinstance(args[0], dict):
						return args[0].get(port)
					return port_inputs.get(port)

				# Override temporairement peek()
				self.atomic_model.peek = temp_peek

				try:
					self.atomic_model.extTransition(port_inputs)
				finally:
					if old_peek is not None:
						self.atomic_model.peek = old_peek
					else:
						# On enlève l'attribut si inexistant avant
						if hasattr(self.atomic_model, "peek"):
							delattr(self.atomic_model, "peek")
			else:
				# Pas d'inputs : transition interne
				self.atomic_model.intTransition()

			# Après extTransition, on recalcule le ta
			ta = self.atomic_model.timeAdvance()
			
			ta = float(ta) if ta is not None else float("inf")
		
			return TransitionDone(time=SimTime(t=t), nextTime=SimTime(t=ta), sender=self.atomic_model.getBlockModel().label)
		
		# --- SendOutput : outputFnc + calcul des sorties ---
		if isinstance(msg, SendOutput):
			t = msg.time.t

			# Vider myOutput avant d'appeler outputFnc
			self.atomic_model.myOutput = {}

			# Appeler outputFnc (remplit myOutput via poke())
			self.atomic_model.outputFnc()

			port_values = []
			for port, m in self.atomic_model.myOutput.items():
				if m is None:
					continue
				value = getattr(m, "value", m)
				port_name = getattr(port, "name", str(port))
				port_values.append(
					PortValue(
						value=value,
						portIdentifier=port_name,
						portType=type(value).__name__,
					)
				)

			# Ici, pour rester simple, on renvoie nextTime=t (ou on pourrait
			# faire un timeAdvance immédiat après outputFnc et renvoyer ce ta).
			next_time = SimTime(t=t)
			return ModelOutputMessage(
				modelOutput=port_values,
				nextTime=next_time,
				sender=self.atomic_model.getBlockModel().label,
			)

		if isinstance(msg, SimulationDone):
			return ModelDone(
				time=msg.time,
				sender=self.atomic_model.getBlockModel().label,
			)


		# --- NextTime, ModelOutputMessage, etc. ---
		# Ces types sont normalement utilisés comme réponses, pas comme requêtes
		# côté worker, donc on ne les traite pas ici.
		raise ValueError(f"Unsupported message type in worker: {type(msg).__name__}")

	# ------------------------------------------------------------------
	#  Boucle principale
	# ------------------------------------------------------------------

	def run(self):
		logger.info("  [Thread-%s] Started", self.atomic_index)

		while self.running:
			msg = self.consumer.poll(timeout=0.5)
			if msg is None or msg.error():
				continue

			try:
				raw = msg.value().decode("utf-8")
				data = json.loads(raw)

				# Log brut de ce qui arrive sur work_{atomic_index}
				kafka_logger.debug(
					"  [Thread-%s] KAFKA-IN topic=%s key=%s value=%s",
					self.atomic_index,
					msg.topic(),
					msg.key().decode("utf-8") if msg.key() else None,
					raw,
				)

				if self.wire:
					# Nouveau mode : messages typés
					devs_msg = self.wire.from_wire(data)
					corr_id = data.get("correlation_id")
					atomic_index = data.get("atomic_index", self.atomic_index)

					try:
						reply_msg = self._handle_devs_message(devs_msg)
					except Exception as e:
						logger.exception("  [Thread-%s] Error handling message: %s",
										self.atomic_index, e)
						continue

					reply_wire = self.wire.to_wire(reply_msg, corr_id, atomic_index)
					
					reply_json = json.dumps(reply_wire).encode("utf-8")
					kafka_logger.debug(
						f"  [Thread-{self.atomic_index}] KAFKA-OUT topic={self.out_topic} value={reply_json.decode("utf-8")}"
					)
					
					self.producer.produce(
						self.out_topic,
						value=json.dumps(reply_wire).encode("utf-8"),
					)
					self.producer.flush()

				else:
					# Mode local : ancien comportement (operation / execute_operation)
					operation = data["operation"]
					correlation_id = data["correlation_id"]

					result = self.execute_operation(operation, data)

					response = {
						"correlation_id": correlation_id,
						"atomic_index": self.atomic_index,
						"result": result,
					}

					response_json = json.dumps(response).encode("utf-8")
					kafka_logger.debug(
						f"  [Thread-{self.atomic_index}] KAFKA-OUT topic={self.out_topic} value={response_json.decode("utf-8")}",
					)

					self.producer.produce(
						self.out_topic,
						value=json.dumps(response).encode("utf-8"),
					)
					self.producer.flush()

			except Exception as e:
				logger.exception("  [Thread-%s] Error in run loop: %s", self.atomic_index, e)

		self.consumer.close()
		logger.info("  [Thread-%s] Stopped", self.atomic_index)


	def stop(self):
		"""Stop the worker thread."""
		self.running = False