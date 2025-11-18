# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Strategies.py --- Strategies for DEVSimPy simulation
#                     --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                      last modified:  05/11/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import sys
import time
import copy
import weakref
import heapq
import threading
import importlib
import json
import builtins
import re
import os
	
from PluginManager import PluginManager #trigger_event
from Utilities import getOutDir
from Patterns.Strategy import SimStrategy

### import the DEVS module depending on the selected DEVS package in DEVSKernel directory
for pydevs_dir, path in getattr(builtins,'DEVS_DIR_PATH_DICT').items():
	if os.path.exists(path):
		### split from DEVSKernel string and replace separator with point
		d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')

		### for py 3.X
		import importlib
		exec("%s = importlib.import_module('DEVSKernel%s.DEVS')"%(pydevs_dir,d))
		
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

def getFlatImmChildrenList(model, flat_imm_list: list = None) -> list:
	"""Set priority flat list compatible avec DEFAULT_DEVS_DIRNAME."""
	if flat_imm_list is None:
		flat_imm_list = []

	# Récupère le module DEVS actif à partir du nom par défaut
	devs_backend_name = getattr(builtins, 'DEFAULT_DEVS_DIRNAME', 'PyDEVS')
	devs_mod = globals().get(devs_backend_name, None)
	if devs_mod is None:
		raise RuntimeError(f"Backend DEVS '{devs_backend_name}' non importé")

	AtomicDEVS = getattr(devs_mod, 'AtomicDEVS', None)
	CoupledDEVS = getattr(devs_mod, 'CoupledDEVS', None)
	if AtomicDEVS is None or CoupledDEVS is None:
		raise RuntimeError(f"Classes AtomicDEVS/CoupledDEVS introuvables dans backend '{devs_backend_name}'")

	for m in model.immChildren:
		if isinstance(m, AtomicDEVS):
			flat_imm_list.append(m)
		elif isinstance(m, CoupledDEVS):
			getFlatImmChildrenList(m, flat_imm_list)

	return flat_imm_list


def getFlatPriorityList(model, flat_priority_list: list = None) -> list:
	"""Set priority flat list compatible avec DEFAULT_DEVS_DIRNAME."""
	if flat_priority_list is None:
		flat_priority_list = []

	# Résolution du backend DEVS actif
	devs_backend_name = getattr(builtins, 'DEFAULT_DEVS_DIRNAME', 'PyDEVS')
	devs_mod = globals().get(devs_backend_name, None)
	if devs_mod is None:
		raise RuntimeError(f"Backend DEVS '{devs_backend_name}' non importé")

	AtomicDEVS = getattr(devs_mod, 'AtomicDEVS', None)
	CoupledDEVS = getattr(devs_mod, 'CoupledDEVS', None)
	if AtomicDEVS is None or CoupledDEVS is None:
		raise RuntimeError(f"Classes AtomicDEVS/CoupledDEVS introuvables dans backend '{devs_backend_name}'")

	# Si la PRIORITY_LIST n'a jamais été éditée, l'ordre par défaut est componentSet
	L = model.PRIORITY_LIST if hasattr(model, 'PRIORITY_LIST') and model.PRIORITY_LIST else model.componentSet

	for m in L:
		if isinstance(m, AtomicDEVS):
			flat_priority_list.append(m)
		elif isinstance(m, CoupledDEVS):
			getFlatPriorityList(m, flat_priority_list)
		else:
			sys.stdout.write(_(f'Unknow model {m}'))

	return flat_priority_list


def HasActiveChild(L:list)->bool:
	""" Return true if a children of master is active.
	"""
	return L and True in [a.timeNext != INFINITY for a in L]

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASS DEFINITION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class OriginalPyDEVSSimStrategy(SimStrategy):
	""" Original strategy for PyDEVS simulation.
	"""

	def __init__(self, simulator = None):
		""" Constructor.
		"""
		super().__init__(simulator)

	def simulate(self, T = 1e8):
		"""Simulate the model (Root-Coordinator).
		"""

		if self._simulator is None:
			raise ValueError("Simulator instance must be provided to OriginalPyDEVSSimStrategy.")

		clock = 0.0
		model = self._simulator.getMaster()
		send = self._simulator.send

		# Initialize the model --- set the simulation clock to 0.
		send(model, (0, [], 0))

		# Main loop repeatedly sends $(*,\,t)$ messages to the model's root DEVS.
		while clock <= T:

			send(model, (1, model.immChildren, clock))
			clock = model.myTimeAdvance

		self._simulator.terminate()

class BagBasedPyDEVSSimStrategy(SimStrategy):
	""" Strategy for DEVSimPy hierarchical simulation.

		This strategy is based on Zeigler's hierarchical simulation algorithm based on atomic and coupled Solver.
	"""

	def __init__(self, simulator=None):
		""" Constructor.
		"""
		super().__init__(simulator)

	def simulate(self, T = 1e8):
		""" Simulate for T
		"""

		if self._simulator is None:
			raise ValueError("Simulator instance must be provided to BagBasedPyDEVSSimStrategy.")
		
		master = self._simulator.getMaster()
		send = self._simulator.send
		#clock = master.myTimeAdvance

		# Initialize the model --- set the simulation clock to 0.
		send(master, (0, [], 0))

		clock = master.myTimeAdvance

		### ref to cpu time evaluation
		t_start = time.time()

		### if suspend, we could store the future ref
		old_cpu_time = 0

		### stoping condition depend on the ntl (no time limit for the simulation)
		condition = lambda clock: HasActiveChild(getFlatImmChildrenList(master, [])) if self._simulator.ntl else clock <= T

		# Main loop repeatedly sends $(*,\,t)$ messages to the model's root DEVS.
		while condition(clock) and self._simulator.end_flag == False:

			##Optional sleep
			if self._simulator.thread_sleep:
				time.sleep(self._simulator._sleeptime)

			elif self._simulator.thread_suspend:
				### Optional suspend
				while self._simulator.thread_suspend:
					time.sleep(1.0)
					old_cpu_time = self._simulator.cpu_time
					t_start = time.time()

			else:
				# The SIM_VERBOSE event occurs
				PluginManager.trigger_event("SIM_VERBOSE", clock = clock)

				send(master, (1, {}, clock))

				clock = master.myTimeAdvance

				self._simulator.cpu_time = old_cpu_time + (time.time()-t_start)

		self._simulator.terminate()

###--------------------------------------------------------------------Strategy

### decorator for poke
def Post_Poke(f):
	def wrapper(*args):
		p = args[0]
		v = args[1]
		r = f(*args)
		#parallel_ext_transtion_manager(p)
		serial_ext_transtion_manager(p)
		return r
	return wrapper


def parallel_ext_transtion_manager(p):

	hosts = p.weak.GetHosts()

	###----------------------------------------------------------------------------------------
	### thread version
	threads = []

	for val in hosts:
		t = threading.Thread(target=val[2], args=(val[1],))
		threads.append(t)
		t.start()

	#### Wait for all worker threads to finish
	for thread in threads:
		thread.join()
	###-----------------------------------------------------------------------------------------

	### clear output port (then input port of hosts) of model in charge of activate hosts
	p.weak.SetValue(None)

def serial_ext_transtion_manager(p):
	""" achieve external transition function of host from p
	 """


	hosts = p.weak.GetHosts()

	### serial version
	for val in hosts:
		val[2](*(val[1],))

	### clear output port (then input port of hosts) of model in charge of activate hosts
	p.weak.SetValue(None)

###
@Post_Poke
def poke(p, v):
	p.weak.SetValue(v)

	### just for plugin verbose
	p.host.myOutput[p] = v

###
def peek(p):
	return copy.deepcopy(p.weak.GetValue())

def peek_all(self):
	"""Retrives messages from all input port {\tt p}.
	"""
	return [a for a in [(p, peek(p)) for p in self.IPorts] if a[1]!=None]

###
class WeakValue:
	""" Weak Value class
	"""
	def __init__(self, port=None):
		""" Constructor
		"""

		### port of weak value
		self.port = port

		### value and time of msg
		self._value = None
		self._host = []

	def SetValue(self, v):
		""" Set value and time
		"""

		self._value = v

	def GetValue(self):
		""" Get value at time t
		"""

		return self._value

	def AddHosts(self,p):
		""" Make host list composed by tuple of priority, model and transition function.
		"""
		model = p.host
		v = (model.priority/10000.0, model, execExtTransition)
		if v not in self._host and hasattr(model, 'priority'):
			self._host.append(v)

	def GetHosts(self):
		""" Return the host.
		"""
		return self._host

def FlatConnection(p1, p2):
	""" Make flat connection.
	"""

	if isinstance(p1.host, PyDEVS.AtomicDEVS) and isinstance(p2.host, PyDEVS.AtomicDEVS):
		if isinstance(p1, PyDEVS.OPort) and isinstance(p2, PyDEVS.IPort):
			if not isinstance(p1.weak, weakref.ProxyType):
				wr = weakref.proxy(p1.weak)
				p2_weak_old = p2.weak
				if not isinstance(p2.weak, weakref.ProxyType):
					p2.weak = wr
				else:
					p1.weak = p2.weak
			else:
				p2.weak = p1.weak

			## build hosts list in WeakValue class
			p1.weak.AddHosts(p2)

	elif isinstance(p1.host, PyDEVS.AtomicDEVS) and isinstance(p2.host, PyDEVS.CoupledDEVS):
		if isinstance(p1, PyDEVS.OPort):
			### update outLine port list removing ports of coupled model
			p1.outLine = [a for a in p1.outLine if isinstance(a.host, PyDEVS.AtomicDEVS)]
			for p in p2.outLine:
				if not hasattr(p, 'weak'): setattr(p, 'weak', WeakValue(p))
				FlatConnection(p1, p)

	elif isinstance(p1.host, PyDEVS.CoupledDEVS) and isinstance(p2.host, PyDEVS.AtomicDEVS):
		if isinstance(p1, PyDEVS.OPort) and isinstance(p2, PyDEVS.IPort):
			for p in p1.inLine:
				if not hasattr(p, 'weak'): setattr(p, 'weak', WeakValue(p))
				FlatConnection(p, p2)

	elif isinstance(p1.host, PyDEVS.CoupledDEVS) and isinstance(p2.host, PyDEVS.CoupledDEVS):
		if isinstance(p1, PyDEVS.OPort) and isinstance(p2, PyDEVS.IPort):
			for p in p1.inLine:
				for pp in p2.outLine:
					FlatConnection(p, pp)

def setAtomicModels(atomic_model_list, ts):
	""" Set atomic DEVS model flat list and initialize it.
	"""

	for i,m in enumerate(atomic_model_list):
		m.elapsed = m.timeLast = m.timeNext = 0.0
		m.myTimeAdvance = m.timeAdvance()
		m.poke = poke
		m.peek = peek
		# Fix: Directly bind the peek_all method instead of using funcType
		m.peek_all = lambda self=m: peek_all(self)
		setattr(m, 'priority', i)
		setattr(m, 'ts', ts())

	for m in atomic_model_list:
		for p1 in m.OPorts:
			if not hasattr(p1, 'weak'): 
				setattr(p1, 'weak', WeakValue(p1))
			for p2 in p1.outLine:
				if not hasattr(p2, 'weak'): 
					setattr(p2, 'weak', WeakValue(p2))
				FlatConnection(p1,p2)

		for p1 in m.IPorts:
			if not hasattr(p1, 'weak'): 
				setattr(p1, 'weak', WeakValue(p1))
			for p2 in p1.inLine:
				if not hasattr(p2, 'weak'): 
					setattr(p2, 'weak', WeakValue(p2))

###
def execExtTransition(m):
	"""
	"""

	ts =  m.ts.Get()

	m.elapsed =ts - m.timeLast

	m.extTransition()

	m.timeLast = ts
	m.myTimeAdvance = m.timeAdvance()
	m.timeNext = m.timeLast+m.myTimeAdvance
	if m.myTimeAdvance != INFINITY: m.myTimeAdvance += ts
	m.elapsed = 0.0

	# The SIM_VERBOSE event occurs
	PluginManager.trigger_event("SIM_VERBOSE", model=m, msg=1)
	PluginManager.trigger_event("SIM_BLINK", model=m, msg=[{}])
	PluginManager.trigger_event("SIM_TEST", model=m, msg=[{}])

	return m

###
def execIntTransition(m):
	"""
	"""

	ts =  m.ts.Get()

	if m.timeNext != INFINITY:
		m.outputFnc()

	m.elapsed = ts - m.timeLast

	m.intTransition()
	m.timeLast = ts
	m.myTimeAdvance = m.timeAdvance()
	m.timeNext = m.timeLast+m.myTimeAdvance
	if m.myTimeAdvance != INFINITY: m.myTimeAdvance += ts
	m.elapsed = 0.0

	# The SIM_VERBOSE event occurs
	PluginManager.trigger_event("SIM_VERBOSE", model=m, msg=0)
	PluginManager.trigger_event("SIM_BLINK", model=m, msg=[1])
	PluginManager.trigger_event("SIM_TEST", model=m, msg=[1])

class Clock(object):
	def __init__(self, time):
		self._val = time
	def Get(self):
		return self._val
	def Set(self, val):
		self._val = val

###
class DirectCouplingPyDEVSSimStrategy(SimStrategy):
	""" Strategy 3 for DEVSimPy thread-based direct-coupled simulation

		The simulate methode use heapq tree-like data library to manage model priority for activation
		and weak library to simplify the connexion algorithm between port.
		The THREAD_LIMIT control the limit of models to thread (default 5).
		The performance of this algorithm depends on the THREAD_LIMIT number and the number of coupled models.
	"""

	def __init__(self, simulator=None):
		""" Cosntructor.
		"""

		super().__init__(simulator)

		### simulation time
		self.ts = Clock(0.0)

		### master model and flat list of atomic model
		self.master = self._simulator.getMaster()
		self.flat_priority_list = getFlatPriorityList(self.master, [])

		### init all atomic model from flat list
		setAtomicModels(self.flat_priority_list, weakref.ref(self.ts))

		### udpate the componentSet list of master (that no longer contains coupled model)
		self.master.componentSet = self.flat_priority_list


	def simulate(self, T = 1e8):
		""" Simulate for T.
		"""

		if self._simulator is None:
			raise ValueError("Simulator instance must be provided to DirectCouplingPyDEVSSimStrategy.")
		
		### ref to cpu time evaluation
		t_start = time.time()
		### if suspend, we could store the future ref
		old_cpu_time = 0

		### stopping condition depend on the ntl (no time limit for the simulation)
		condition = lambda clk: HasActiveChild(getFlatPriorityList(self.master, [])) if self._simulator.ntl else clk <= T

		### simulation time and list of flat models ordered by devs priority
		L = [m.myTimeAdvance for m in self.flat_priority_list if m.myTimeAdvance < INFINITY] or [INFINITY]
		self.ts.Set(min(L))
		formated_priority_list = [(1+i/10000.0, m, execIntTransition) for i,m in enumerate(self.flat_priority_list)]

		while condition(self.ts.Get()) and self._simulator.end_flag == False:

			### Optional sleep
			if self._simulator.thread_sleep:
				time.sleep(self._simulator._sleeptime)

			elif self._simulator.thread_suspend:
			### Optional suspend
				while self._simulator.thread_suspend:
					time.sleep(1.0)
					old_cpu_time = self._simulator.cpu_time
					t_start = time.time()

			else:

				### The SIM_VERBOSE event occurs
				PluginManager.trigger_event("SIM_VERBOSE", self.master, None, clock = self.ts.Get())

				### tree-like data structure ordered by devsimpy priority
				priority_scheduler = [a for a in formated_priority_list if self.ts.Get() == a[1].myTimeAdvance]
				heapq.heapify(priority_scheduler)

				### TODO: execute with process of model are parallel !
				while(priority_scheduler):
					### get most priority model and apply its internal transition
					priority, model, transition_fct = heapq.heappop(priority_scheduler)
					transition_fct(*(model,))

				### update simulation time
				self.ts.Set(min([m.myTimeAdvance for m in self.flat_priority_list]))

				### just for progress bar
				self.master.timeLast = self.ts.Get() if self.ts.Get() != INFINITY else self.master.timeLast
				self._simulator.cpu_time = old_cpu_time + (time.time()-t_start)

		self._simulator.terminate()


def terminate_never(model, clock):
	return False

class ClassicPyPDEVSSimStrategy(SimStrategy):
	""" classic strategy for PyPDEVS simulation
		setClassicDEVS is True and confTransition in disabled
	"""

	def __init__(self, simulator = None):
		super().__init__(simulator)

	def simulate(self, T = 1e8):
		"""Simulate the model (Root-Coordinator).
		"""
		
		if self._simulator is None:
			raise ValueError("Simulator instance must be provided to ClassicPyPDEVSSimStrategy.")
		
		# Import the correct simulator module dynamically
		path = getattr(builtins, 'DEVS_DIR_PATH_DICT').get('PyPDEVS', None)
		if not path:
			raise ValueError("PyPDEVS path not found in DEVS_DIR_PATH_DICT")

		d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')
		simulator_module = importlib.import_module(f"DEVSKernel{d}.simulator")

		print("\nAvailable classes and methods:")
		for item in dir(simulator_module.Simulator):
			if not item.startswith('_'):
				print(f"- {item}")

		# Create simulator instance with the model
		sim = simulator_module.Simulator(self._simulator.model)

		# Configure simulation parameters
		if hasattr(sim, 'setVerbose'):
			if self._simulator.verbose:
				sim.setVerbose(None)
			else:
				out_dir = os.path.join(getOutDir())
				if not os.path.exists(out_dir):
					os.makedirs(out_dir)
				verbose_file = os.path.join(out_dir, 'verbose.txt')
				sim.setVerbose(verbose_file)

		# Set termination condition
		if hasattr(sim, 'setTerminationTime'):
			if self._simulator.ntl:
				sim.setTerminationCondition(terminate_never)
			else:
				sim.setTerminationTime(T)

		# Run simulation using available method
		if hasattr(sim, 'simulate'):
			sim.simulate()
		elif hasattr(sim, 'run'):
			sim.run()
		else:
			raise AttributeError("Simulator has no 'simulate' or 'run' method")

		self._simulator.terminate()

	def SetClassicDEVSOption(self):
		return True

class ParallelPyPDEVSSimStrategy(ClassicPyPDEVSSimStrategy):
	""" Parallel strategy for PyPDEVS simulation
		setClassicDEVS is False and confTransition in enabled
	"""

	def __init__(self, simulator = None):
		""" Constructor.
		"""
		super(). __init__(simulator)

	def SetClassicDEVSOption(self):
		return False

# ---------------------------------------------------------------------------
# Kafka-based distributed strategy with IN-MEMORY workers (threads)
# ---------------------------------------------------------------------------
# Requires: pip install confluent-kafka
import threading
import json
import time
import logging

try:
	from confluent_kafka import Producer, Consumer
	from confluent_kafka.admin import AdminClient, NewTopic
except Exception:
	Producer = None
	Consumer = None

from DEVSKernel.KafkaDEVS.InMemoryKafkaWorker import InMemoryKafkaWorker

logging.basicConfig(
	level=logging.DEBUG,  # DEBUG pour le dev et WARNING pour la prod
	format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
	handlers=[
		logging.StreamHandler(),                    # console
		logging.FileHandler("kafka_devssim.log")    # fichier
	]
)

logger = logging.getLogger(__name__)

class SimStrategyKafka(DirectCouplingPyDEVSSimStrategy):
	"""
	Kafka strategy with in-memory workers (threads instead of processes)
	No serialization issues, models stay in memory with all their parameters
	"""
	def __init__(self, simulator=None, 
				 kafka_bootstrap="localhost:9092",
				 group_id=None,
				 request_timeout=30.0):
		super().__init__(simulator)


		if Producer is None or Consumer is None:
			raise RuntimeError("confluent-kafka not available. Please install it.")
		
		self.bootstrap = kafka_bootstrap
		
		# Unique group ID per execution
		if group_id is None:
			group_id = f"coordinator-{int(time.time() * 1000)}"
		
		self.group_id = group_id
		self.request_timeout = request_timeout
		
		# Kafka producer/consumer
		self._producer = Producer({
			"bootstrap.servers": self.bootstrap,
			"enable.idempotence": True,
			"acks": "all",
		})
		
		self._consumer = Consumer({
			"bootstrap.servers": self.bootstrap,
			"group.id": self.group_id,
			"auto.offset.reset": "earliest",  # ← Garder earliest
			"enable.auto.commit": False,      # ← Désactiver auto-commit
			"session.timeout.ms": 30000
		})
		self._consumer.subscribe(["atomic_results"])
		
		# Use in-memory models
		self._atomic_models = list(self.flat_priority_list)
		self._num_atomics = len(self._atomic_models)
		self._index2model = {i: m for i, m in enumerate(self._atomic_models)}


		self._workers = []
		
		logger.info("KafkaDEVS SimStrategy initialized (In-Memory Workers)")
		logger.info("  Bootstrap servers: %s", self.bootstrap)
		logger.info("  Consumer group: %s", self.group_id)
		logger.info("  Number of atomic models: %s", self._num_atomics)
		logger.info("  Index Mapping:")
		for i, m in enumerate(self._atomic_models):
			logger.info("    Index %s -> %s (%s)", i, m.myID, type(m).__name__)


	def _create_topics(self):
		"""Create Kafka topics"""
		admin = AdminClient({'bootstrap.servers': self.bootstrap})
		metadata = admin.list_topics(timeout=10)
		existing = set(metadata.topics.keys())

		new_topics = []
		
		for i in range(self._num_atomics):
			topic = f'work_{i}'
			if topic not in existing:
				new_topics.append(NewTopic(topic, num_partitions=1, replication_factor=1))
		
		if 'atomic_results' not in existing:
			new_topics.append(NewTopic('atomic_results', num_partitions=3, replication_factor=1))
		
		if new_topics:
			logger.info("Creating %s Kafka topics...", len(new_topics))
			fs = admin.create_topics(new_topics)
			for topic, f in fs.items():
				try:
					f.result()
				except Exception:
					pass
		else:
			admin = AdminClient({"bootstrap.servers": self.bootstrap})

			# Récupérer la métadonnée du cluster
			md = admin.list_topics(timeout=10)
			topics = list(md.topics.keys())
			logger.info(f"All required Kafka topics already exist: {topics}")


	def _spawn_workers(self):
		"""Spawn in-memory worker threads"""
		logger.info("Spawning %s worker threads...", self._num_atomics)
		
		for i, model in enumerate(self._atomic_models):
			logger.info("  Model %s (%s - %s):", i, model.myID, type(model).__name__)
			logger.info("    Real class: %s.%s", model.__class__.__module__, model.__class__.__name__)
			logger.info("    Python file: %s", model.__class__.__module__)
			
			if hasattr(model, 'minStep'):
				logger.info("    -> This is a Generator (has minStep=%s)", model.minStep)
			
			logger.info("    OPorts: %s", [p.name for p in model.OPorts])
			logger.info("    IPorts: %s", [p.name for p in model.IPorts])
			logger.info("    OUT0 connected to:")
			
			worker = InMemoryKafkaWorker(model, i, self.bootstrap)
			worker.start()
			self._workers.append(worker)
		
		logger.info("  All %s threads started", self._num_atomics)


	def _terminate_workers(self):
		"""Stop all worker threads"""
		logger.info("Stopping worker threads...")
		
		for worker in self._workers:
			worker.stop()
		
		for worker in self._workers:
			worker.join(timeout=2.0)
		
		logger.info("  All workers stopped")


	def _send_work_to_atomic(self, index: int, operation: str, correlation_id: float, inputs=None, current_time=None):
		"""Send work to atomic model"""
		work_message = {
			'correlation_id': correlation_id,
			'operation': operation,
			'inputs': inputs or {},
			'current_time': current_time if current_time is not None else self.ts.Get()
		}
		
		self._producer.produce(
			f'work_{index}',
			value=json.dumps(work_message).encode('utf-8')
		)
		self._producer.flush()


	def _await_results(self, expected_indices, correlation_id, timeout=None):
		"""Wait for results from worker threads"""
		if timeout is None:
			timeout = self.request_timeout
		
		pending = set(expected_indices)
		received = {}
		deadline = time.time() + timeout
		
		while pending and time.time() < deadline:
			msg = self._consumer.poll(timeout=0.5)
			
			if msg is None:
				continue
			
			if msg.error():
				continue
			
			try:
				data = json.loads(msg.value().decode('utf-8'))
				msg_corr_id = data.get('correlation_id')
				msg_index = data.get('atomic_index')
				
				# Vérifier correlation_id
				if msg_corr_id != correlation_id:
					continue
				
				# Vérifier index attendu
				if msg_index not in pending:
					continue
				
				# Vérifier que le résultat est valide
				result_data = data.get('result', {})
				if isinstance(result_data, dict):
					actual_result = result_data.get('result')
					
					# Ignorer les résultats clairement invalides
					# (inf isolé sans être un timeAdvance légitime)
					if isinstance(actual_result, float) and actual_result == float('inf'):
						# Pour les output_function, inf n'est jamais valide
						# Seul time_advance peut retourner inf
						if actual_result == float('inf') and not isinstance(actual_result, dict):
							# C'est probablement un timeAdvance, on accepte
							pass
				
				# Message valide
				received[msg_index] = data
				pending.remove(msg_index)
				
			except Exception:
				continue
		
		if pending:
			raise TimeoutError(f"Kafka timeout: missing indices {sorted(pending)} for corr_id={correlation_id}")
		
		return received


	def simulate(self, T=1e8, spawn_workers=True, **kwargs):
		"""Main simulation loop with Kafka coordination and message routing"""
		if self._simulator is None:
			raise ValueError("Simulator instance must be provided.")
		
		logger.info("=" * 60)
		logger.info("  KafkaDEVS Simulation Starting (In-Memory)")
		logger.info("=" * 60)
		
		# Create topics
		self._create_topics()
		
		# Spawn worker threads
		if spawn_workers:
			self._spawn_workers()
		
		logger.info("Waiting for workers to initialize (2s)...")
		time.sleep(2)
		
		# Warm up consumer and FLUSH old messages
		logger.info("Warming up consumer...")
		flushed = 0
		start_flush = time.time()
		while time.time() - start_flush < 2.0:  # Flush pendant 2 secondes
			msg = self._consumer.poll(timeout=0.1)
			if msg is None:
				break
			flushed += 1
		
		if flushed > 0:
			logger.info("  Flushed %s old messages", flushed)
		logger.info("System ready")
		
		try:
			corr_id = 0.0
			all_indices = list(range(self._num_atomics))
			
			logger.info("Initializing atomic models...")

			# STEP 0 : envoyer une opération 'init' à chaque modèle atomique
			for i in all_indices:
				# Pas d'inputs ni de current_time particulier pour init
				self._send_work_to_atomic(i, 'init', corr_id)

			# Attendre les réponses de tous les modèles
			init_results = self._await_results(all_indices, corr_id)

			# Construire myTimeAdvance / myTimeNext à partir des réponses 'init'
			for i in all_indices:
				model = self._index2model[i]
				data = init_results.get(i, {})
				result_data = data.get('result', {})

				# result_data peut être soit {'status': 'success', 'result': ta},
				# soit directement un float selon ton implémentation.
				if isinstance(result_data, dict) and 'result' in result_data:
					ta = result_data['result']
				else:
					ta = result_data

				try:
					ta = float(ta) if ta is not None else float('inf')
				except (ValueError, TypeError):
					ta = float('inf')

				model.myTimeAdvance = ta
				model.myTimeNext = self.ts.Get() + ta

				logger.info(f"  Model {i} ({model.myID}): ta={ta}, next={model.myTimeNext}")

			corr_id += 1.0
			
			# MAIN SIMULATION LOOP
			logger.info("Simulation loop starting (T=%s)...", T)
			iteration = 0
			t_start = time.time()
			old_cpu_time = 0
			
			while self.ts.Get() < T and not self._simulator.end_flag:
				iteration += 1

				tmin = min([m.myTimeNext for m in self._atomic_models])
				
				if tmin == float('inf'):
					logger.info("No more events - simulation complete")
					break
				
				if tmin > T:
					logger.info("Next event at t=%s exceeds simulation time T=%s", tmin, T)
					break
				
				self.ts.Set(tmin)
				imminents = [i for i in all_indices if self._index2model[i].myTimeNext == tmin]
				
				logger.info("=" * 60)
				logger.info("Iteration %s: t=%.2f", iteration, tmin)
				logger.info("  Imminent models: %s", [f"{i}({self._index2model[i].myID})({type(self._index2model[i]).__name__})" for i in imminents])
				logger.info("=" * 60)
				
				# STEP 1: OUTPUT FUNCTION
				logger.info("[1/4] Executing output functions...")
				for i in imminents:
					self._send_work_to_atomic(i, 'output_function', corr_id, current_time=tmin)
				
				outputs = self._await_results(imminents, corr_id)
				corr_id += 1.0


				# STEP 2: ROUTING
				logger.info("[2/4] Routing outputs to destinations...")
				externals_to_send = {}
				parent_model = self._atomic_models[0].parent if self._atomic_models else None


				if parent_model is None:
					logger.warning("  WARNING: No parent model found, cannot route outputs")
				else:
					for src_idx, data in outputs.items():
						output_result = data.get('result', {}).get('result')
						
						if output_result and isinstance(output_result, dict) and output_result:
							src_model = self._index2model[src_idx]
							logger.info("  Model %s (%s) produced outputs: %s", src_idx, src_model.myID, output_result)
							
							for port_name, port_data in output_result.items():
								src_port = None
								for p in src_model.OPorts:
									if p.name == port_name:
										src_port = p
										break
								
								if src_port is None:
									continue
								
								for coupling in parent_model.IC:
									try:
										(src_m, src_p), (dest_m, dest_p) = coupling
									except Exception:
										continue
									
									if src_m is src_model and src_p is src_port:
										dest_idx = None
										for idx, model in self._index2model.items():
											if model is dest_m:
												dest_idx = idx
												break
										
										if dest_idx is not None:
											logger.info(
												"    -> Routing from %s.%s to %s.%s",
												src_model.myID,
												port_name,
												dest_m.myID,
												dest_p.name,
											)
											logger.info("       Value: %s", port_data['value'])
											
											if dest_idx not in externals_to_send:
												externals_to_send[dest_idx] = {}
											
											externals_to_send[dest_idx][dest_p.name] = port_data['value']
							
				if externals_to_send:
					logger.info("  Sending external transitions to %s models...", len(externals_to_send))
					for dest_idx, inputs in externals_to_send.items():
						self._send_work_to_atomic(dest_idx, 'external_transition', corr_id, inputs=inputs, current_time=tmin)
					
					self._await_results(list(externals_to_send.keys()), corr_id)
				else:
					logger.info("  No outputs to route")


				corr_id += 1.0
				
				# STEP 3: INTERNAL TRANSITIONS
				logger.info("[3/4] Executing internal transitions...")
				for i in imminents:
					self._send_work_to_atomic(i, 'internal_transition', corr_id)
				
				self._await_results(imminents, corr_id)
				corr_id += 1.0
				
				# STEP 4: UPDATE TIME ADVANCES
				logger.info("[4/4] Updating time advances...")
				affected = set(imminents) | set(externals_to_send.keys())
				
				for i in affected:
					self._send_work_to_atomic(i, 'time_advance', corr_id)
				
				results = self._await_results(list(affected), corr_id)


				for i, data in results.items():
					result_data = data.get('result', {})
					
					if isinstance(result_data, dict) and 'result' in result_data:
						ta = result_data['result']
					else:
						ta = result_data
					
					try:
						ta = float(ta) if ta is not None else float('inf')
					except (ValueError, TypeError):
						ta = float('inf')
					
					model = self._index2model[i]
					model.myTimeAdvance = ta
					model.myTimeNext = tmin + ta
					logger.info("  Model %s (%s): ta=%s -> next=%s", i, model.myID, ta, model.myTimeNext)
				
				corr_id += 1.0
				
				self.master.timeLast = tmin
				self._simulator.cpu_time = old_cpu_time + (time.time() - t_start)
				
				if iteration >= 20:
					logger.info("Reached iteration limit (%s iterations)", iteration)
					break
			
			logger.info("=" * 60)
			logger.info("Simulation completed:")
			logger.info("  Final time: %.2f", self.ts.Get())
			logger.info("  Total iterations: %s", iteration)
			logger.info("  CPU time: %.3fs", self._simulator.cpu_time)
			logger.info("=" * 60)
			
			self._simulator.terminate()
		
		except KeyboardInterrupt:
			logger.warning("Simulation interrupted by user")
		
		except Exception as e:
			logger.exception("Simulation error: %s", e)
		
		finally:
			if spawn_workers:
				self._terminate_workers()
			
			logger.info("=" * 60)
			logger.info("  KafkaDEVS Simulation Ended")
			logger.info("=" * 60)

