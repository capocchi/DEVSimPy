# ---------------------------------------------------------------------------
# Kafka-based IN-MEMORY worker (thread) Class
# ---------------------------------------------------------------------------
# Requires: pip install confluent-kafka
import threading
import json
import logging

logging.basicConfig(
	level=logging.DEBUG,  # DEBUG pour le dev et WARNING pour la prod
	format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
	handlers=[
		logging.StreamHandler(),                    # console
		logging.FileHandler("kafka_devssim.log")    # fichier
	]
)

logger = logging.getLogger(__name__)

try:
	from confluent_kafka import Producer, Consumer
except Exception:
	Producer = None
	Consumer = None

class InMemoryKafkaWorker(threading.Thread):
	"""Worker thread that manages one atomic model in memory"""
	
	def __init__(self, atomic_model, atomic_index, bootstrap_servers):
		super().__init__(daemon=True)
		self.atomic_model = atomic_model
		self.atomic_index = atomic_index
		self.bootstrap_servers = bootstrap_servers
		self.running = True
		
		# Kafka consumer for dedicated topic
		self.consumer = Consumer({
			'bootstrap.servers': bootstrap_servers,
			'group.id': f'worker-thread-{atomic_index}',
			'auto.offset.reset': 'earliest',
			'enable.auto.commit': True,
		})
		self.consumer.subscribe([f'work_{atomic_index}'])
		
		# Kafka producer for results
		self.producer = Producer({
			'bootstrap.servers': bootstrap_servers
		})
		
		logger.info("  [Thread-%s] Created for model %s", atomic_index, atomic_model.myID)
	
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
	
	def run(self):
		"""Main thread loop"""
		logger.info("  [Thread-%s] Started", self.atomic_index)
		
		while self.running:
			msg = self.consumer.poll(timeout=0.5)
			
			if msg is None:
				continue
			
			if msg.error():
				continue
			
			try:
				work_data = json.loads(msg.value().decode('utf-8'))
				operation = work_data['operation']
				correlation_id = work_data['correlation_id']
				
				# Execute operation on in-memory model
				result = self.execute_operation(operation, work_data)
				
				# Send result
				response = {
					'correlation_id': correlation_id,
					'atomic_index': self.atomic_index,
					'result': result
				}
				
				self.producer.produce(
					'atomic_results',
					value=json.dumps(response).encode('utf-8')
				)
				self.producer.flush()
			
			except Exception as e:
				logger.exception("  [Thread-%s] Error: %s", self.atomic_index, e)
		
		self.consumer.close()
		logger.info("  [Thread-%s] Stopped", self.atomic_index)
	
	def stop(self):
		"""Stop the worker thread"""
		self.running = False