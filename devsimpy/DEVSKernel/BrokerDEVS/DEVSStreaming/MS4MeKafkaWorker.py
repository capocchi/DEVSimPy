import logging
import json

from DEVSKernel.BrokerDEVS.logconfig import LOGGING_LEVEL, worker_kafka_logger

logger = logging.getLogger("DEVSKernel.BrokerDEVS.InMemoryKafkaWorker")
logger.setLevel(LOGGING_LEVEL)

from DEVSKernel.BrokerDEVS.Workers.InMemoryKafkaWorker import InMemoryKafkaWorker

from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import (
	BaseMessage,
	SimTime,
	InitSim,
	ExecuteTransition,
	SendOutput,
	NextTime,
	TransitionDone,
	ModelOutputMessage,
	ModelDone,
	PortValue,
	SimulationDone,
)

from DEVSKernel.BrokerDEVS.DEVSStreaming.ms4me_kafka_wire_adapters import StandardWireAdapter
from DomainInterface.Object import Message

class MS4MeKafkaWorker(InMemoryKafkaWorker):
	"""Worker thread that manages one atomic model in memory."""

	OUT_TOPIC = "ms4meOut"

	def __init__(self, model_name, aDEVS, bootstrap_server):
		""" Constructor
		"""
		super().__init__(model_name, aDEVS, bootstrap_server, in_topic=f"ms4me{model_name}In", out_topic=MS4MeKafkaWorker.OUT_TOPIC)

		self.wire = StandardWireAdapter

	def get_topic_to_write(self) -> str:
		""" Return the topic used to contact the model
		"""
		return self.in_topic

	def get_topic_to_read(self) -> str:
		""" Return the name of the topic to used to read the results od the model
		"""
		return self.out_topic
	
	def output_msg_mapping(self) -> ModelOutputMessage:
		""" Returns aModelOutputMessage message that contain the output port values from Ms4me
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
		""" Receive a BaseMessage (InitSim, ExecuteTransition, SendOutput, ...)
		and send a BasMessage in repsonce (NextTime, ModelOutputMessage, ...).
		"""
		logger.debug(f"[{self.model_name}] Received message type: {type(msg).__name__}, devsType: {getattr(msg, 'devsType', 'UNKNOWN')}")
		
		# Ensure we have the time attribute
		if not hasattr(msg, 'time'):
			logger.error(f"[{self.model_name}] Message missing 'time' attribute: {msg}")
			raise ValueError(f"Message missing 'time' attribute: {type(msg).__name__}")
		
		t = msg.time.t

		# --- InitSim : initialisation + timeAdvance initial ---
		if isinstance(msg, InitSim):
			logger.debug(f"[{self.model_name}] Processing InitSim message")
			self.do_initialize(t)
			result = NextTime(SimTime(t=float(self.aDEVS.timeNext)), sender=self.model_name)
			logger.debug(f"[{self.model_name}] Returning NextTime with timeNext={self.aDEVS.timeNext}")
			return result

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
		
			return TransitionDone(time=SimTime(t=t), nextTime=SimTime(t=ta), sender=self.model_name)
		
		# --- SendOutput : outputFnc + calcul des sorties ---
		if isinstance(msg, SendOutput):
			t = msg.time.t

			self.do_output_function()
			port_values = self.output_msg_mapping()
		
			next_time = SimTime(t=t)
			return ModelOutputMessage(
				modelOutput = port_values,
				nextTime = next_time,
				sender = self.model_name,
			)		

		if isinstance(msg, SimulationDone):
			self.running = False
			return ModelDone(
				time = msg.time,
				sender = self.model_name,
			)
		
		raise ValueError(f"Unsupported message type in worker: {type(msg).__name__}")

	def _process_standard(self, data):
		"""Process standard DEVS message format."""
		
		# Handle both raw data and already-deserialized BaseMessage objects
		if isinstance(data, BaseMessage):
			# Already deserialized, use directly
			devs_msg = data
			logger.debug(f"[{self.model_name}] Message already deserialized: {type(devs_msg).__name__}")
		else:
			# Raw data (dict or bytes), deserialize it
			logger.debug(f"[{self.model_name}] Deserializing raw data: {type(data).__name__}")
			devs_msg = self.wire.from_wire(data)
			logger.debug(f"[{self.model_name}] Deserialized to: {type(devs_msg).__name__}")
		
		# handel the DEVS msessage
		try:
			reply_msg = self._handle_devs_message(devs_msg)
		except Exception as e:
			logger.exception("  [Thread-%s] Error handling message: %s", self.aDEVS.myID, e)
			return  # Exit early if message handling fails

		# define a msg to send
		reply_wire = self.wire.to_wire(reply_msg)					
		reply_json = json.dumps(reply_wire).encode("utf-8")

		# Log
		worker_kafka_logger.debug(
			f"[Thread-{self.aDEVS.myID}] OUT: topic={self.out_topic} value={reply_json.decode('utf-8')}"
		)
		
		# send the msg to the out_topic
		self.producer.produce(
			self.out_topic,
			value=reply_json,
		)
		self.producer.flush()