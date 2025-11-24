import logging
import json

from DEVSKernel.KafkaDEVS.logconfig import LOGGING_LEVEL, worker_kafka_logger

logger = logging.getLogger("DEVSKernel.KafkaDEVS.InMemoryKafkaWorker")
logger.setLevel(LOGGING_LEVEL)

from DEVSKernel.KafkaDEVS.InMemoryKafkaWorker import InMemoryKafkaWorker

from .ms4me_kafka_messages import (
	BaseMessage,
	SimTime,
	InitSim,
	ExecuteTransition,
	SendOutput,
	NextTime,
	TransitionDone,
	ModelOutputMessage,
	PortValue,
	SimulationDone,
	ModelDone,
)

from .ms4me_kafka_wire_adapters import StandardWireAdapter
from DomainInterface.Object import Message

class MS4MeKafkaWorker(InMemoryKafkaWorker):
	"""Worker thread that manages one atomic model in memory."""

	OUT_TOPIC = "ms4meOut"

	def __init__(self, aDEVS, index, bootstrap_servers):
		super().__init__(aDEVS, index, bootstrap_servers, in_topic=f"ms4me{aDEVS.getBlockModel().label}In", out_topic=MS4MeKafkaWorker.OUT_TOPIC)

		self.wire = StandardWireAdapter

	def get_topic_to_write(self) -> str:
		"""
		Retourne le nom de topic à utiliser pour contacter ce modèle (obj)
		"""
		
		return self.in_topic
	
	@staticmethod
	def get_topic_to_read() -> str:
		"""
		Retourne le nom de topic à utiliser pour lire les résultats de tous les modèles
		"""
		return MS4MeKafkaWorker.OUT_TOPIC
	
	def output_msg_mapping(self) -> ModelOutputMessage:
		"""

		Args:
			aDEVS (AtomicDEVS): DEVS atomic model from DomainBehaviorInterface

		Returns:
			ModelOutputMessage: ModelOutputMessage containing the output port values from Ms4me
		"""

		result_portvalue_list = []
		for port, m in self.aDEVS.myOutput.items():
			if isinstance(m, Message):
				value = getattr(m, "value", m)
				port_name = getattr(port, "name", str(port))
				result_portvalue_list.append(
					PortValue(
						value=value,
						portIdentifier=port_name,
						portType=type(value).__name__,
					)
				)
			else:
				value = m
				port_name = getattr(port, "name", str(port))
				result_portvalue_list.append(
					PortValue(
						value=value,
						portIdentifier=port_name,
						portType=type(value).__name__,
					)
				)

		return result_portvalue_list

	def _handle_devs_message(self, msg: BaseMessage) -> BaseMessage:
		"""
		Reçoit un BaseMessage (InitSim, ExecuteTransition, SendOutput, ...)
		et renvoie un BaseMessage de réponse (NextTime, ModelOutputMessage, ...).
		"""
		t = msg.time.t

		# --- InitSim : initialisation + timeAdvance initial ---
		if isinstance(msg, InitSim):
			self.do_initialize(t)
			return NextTime(SimTime(t=float(self.aDEVS.timeNext)), sender=self.aBlock.label)

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
					for iport in self.aDEVS.IPorts:
						if iport.name == pv.portIdentifier:
							m = Message(pv.value, t)
							port_inputs[iport] = m
							break

				# Sauvegarder l'ancien peek()
				old_peek = getattr(self.aDEVS, "peek", None)

				def temp_peek(port, *args):
					if args and isinstance(args[0], dict):
						return args[0].get(port)
					return port_inputs.get(port)

				# Override temporairement peek()
				self.aDEVS.peek = temp_peek

				try:
					# with self._temporary_peek(port_inputs):
					self.do_external_transition(t, msg)
					# self.aDEVS.extTransition(port_inputs)
				finally:
					if old_peek is not None:
						self.aDEVS.peek = old_peek
					else:
						# On enlève l'attribut si inexistant avant
						if hasattr(self.aDEVS, "peek"):
							delattr(self.aDEVS, "peek")
			else:
				# Pas d'inputs : transition interne
				# self.aDEVS.intTransition()
				self.do_internal_transition(t)

			# Après extTransition, on recalcule le ta
			ta = self.aDEVS.timeNext
			
			ta = float(ta) if ta is not None else float("inf")
		
			return TransitionDone(time=SimTime(t=t), nextTime=SimTime(t=ta), sender=self.aBlock.label)
		
		# --- SendOutput : outputFnc + calcul des sorties ---
		if isinstance(msg, SendOutput):
			t = msg.time.t

			self.do_output_function()
			port_values = self.output_msg_mapping()
		
			next_time = SimTime(t=t)
			return ModelOutputMessage(
				modelOutput = port_values,
				nextTime = next_time,
				sender = self.aBlock.label,
			)		

		if isinstance(msg, SimulationDone):
			self.running = False
			return ModelDone(
				time = msg.time,
				sender = self.aDEVS.getBlockModel().label,
			)

		# --- NextTime, ModelOutputMessage, etc. ---
		# Ces types sont normalement utilisés comme réponses, pas comme requêtes
		# côté worker, donc on ne les traite pas ici.
		raise ValueError(f"Unsupported message type in worker: {type(msg).__name__}")

	def _process_standard(self, data):
		"""Process standard DEVS message format."""
		
		devs_msg = self.wire.from_wire(data)
		
		# Traiter le message DEVS
		try:
			reply_msg = self._handle_devs_message(devs_msg)
		except Exception as e:
			logger.exception("  [Thread-%s] Error handling message: %s", self.index, e)

		# Préparer le message de réponse
		reply_wire = self.wire.to_wire(reply_msg)					
		reply_json = json.dumps(reply_wire).encode("utf-8")

		# Log et envoi de la réponse
		worker_kafka_logger.debug(
			f"[Thread-{self.index}] OUT: topic={self.out_topic} value={reply_json.decode("utf-8")}"
		)
		
		# Envoi de la réponse
		self.producer.produce(
			self.out_topic,
			value=reply_json,
		)
		self.producer.flush()