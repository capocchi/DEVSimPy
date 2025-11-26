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
	"""Set priority flat list."""
	if flat_priority_list is None:
		flat_priority_list = []

	# Résolution du backend DEVS actif
	# devs_backend_name = getattr(builtins, 'DEFAULT_DEVS_DIRNAME', 'PyDEVS')
	# devs_mod = globals().get(devs_backend_name, None)
	# if devs_mod is None:
	# 	raise RuntimeError(f"Backend DEVS '{devs_backend_name}' non importé")

	# AtomicDEVS = getattr(devs_mod, 'DomainBehavior', None)
	# CoupledDEVS = getattr(devs_mod, 'DomainStructure', None)
	# if AtomicDEVS is None or CoupledDEVS is None:
	# 	raise RuntimeError(f"Classes AtomicDEVS/CoupledDEVS introuvables dans backend '{devs_backend_name}'")

	from DomainInterface import DomainBehavior, DomainStructure
	# AtomicDEVS = DomainBehavior
	# CoupledDEVS = DomainStructure

	# Si la PRIORITY_LIST n'a jamais été éditée, l'ordre par défaut est componentSet
	L = model.PRIORITY_LIST if hasattr(model, 'PRIORITY_LIST') and model.PRIORITY_LIST else model.componentSet

	for m in L:
		if isinstance(m, DomainBehavior):
			flat_priority_list.append(m)
		elif isinstance(m, DomainStructure):
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

import logging

### LOGGING LEVEL: 
###  - logging.DEBUG for development
###  - logging.WARNING for production
LOGGING_LEVEL = logging.DEBUG

import threading
import json
import time

# Requires: pip install confluent-kafka
try:
	from confluent_kafka import Producer, Consumer
	from confluent_kafka.admin import AdminClient, NewTopic
	from confluent_kafka import KafkaException, KafkaError
except Exception:
	Producer = None
	Consumer = None

from DEVSKernel.KafkaDEVS.MS4Me.MS4MeKafkaWorker import MS4MeKafkaWorker
from DEVSKernel.KafkaDEVS.MS4Me.ms4me_kafka_wire_adapters import StandardWireAdapter
from DEVSKernel.KafkaDEVS.MS4Me.ms4me_kafka_messages import (
	BaseMessage,
	SimTime,
	InitSim,
	NextTime,
	ExecuteTransition,
	SendOutput,
	ModelOutputMessage,
	PortValue,
	TransitionDone,
	SimulationDone,
)
from DEVSKernel.KafkaDEVS.auto_kafka import ensure_kafka_broker 
from DEVSKernel.KafkaDEVS.logconfig import configure_logging, LOGGING_LEVEL, coord_kafka_logger
from DEVSKernel.KafkaDEVS.kafkaconfig import KAFKA_BOOTSTRAP, AUTO_START_KAFKA_BROKER

configure_logging()
logger = logging.getLogger("DEVSKernel.Strategies")
logger.setLevel(LOGGING_LEVEL)

class MultiKeyDict:
    def __init__(self):
        self._data = {}
        self._keys = {}  # valeur → liste de clés
    
    def add(self, keys, value):
        """Associer plusieurs clés à une valeur"""
        for key in keys:
            self._data[key] = value
        self._keys[value] = keys
    
    def get(self, key):
        return self._data.get(key)
    
    def values(self):
        """Retourne les valeurs uniques"""
        return set(self._data.values())
    
    def keys(self):
        """Retourne toutes les clés"""
        return self._data.keys()
    
    def items(self):
        """Retourne tous les couples (clé, valeur)"""
        return self._data.items()
    
    def __getitem__(self, key):
        """Permet d'utiliser mkd[key]"""
        return self._data[key]
    
    def __setitem__(self, key, value):
        """Permet d'utiliser mkd[key] = value"""
        self._data[key] = value
    
    def __len__(self):
        """Retourne le nombre de valeurs uniques"""
        return len(set(self._data.values()))
    
    def __contains__(self, key):
        """Permet d'utiliser 'key in mkd'"""
        return key in self._data
	
def purge_kafka_topic(consumer, max_seconds=2.0):
    logger.info("Warming up consumer...")
    flushed = 0
    start_flush = time.time()
    while time.time() - start_flush < max_seconds:
        msg = consumer.poll(timeout=0.1)
        if msg is None:
            break
        flushed += 1
    if flushed > 0:
        logger.info("  Flushed %s old messages", flushed)
    logger.info("System ready")
	
class SimStrategyKafkaMS4Me(DirectCouplingPyDEVSSimStrategy):
	"""
	Kafka strategy with in-memory workers (threads instead of processes),
	utilisant des messages DEVS typés et un adaptateur de wire (Standard/Local).
	"""

	def __init__(self, simulator=None,
				 kafka_bootstrap=KAFKA_BOOTSTRAP,
				 request_timeout=30.0):
		super().__init__(simulator)

		if Producer is None or Consumer is None:
			raise RuntimeError("confluent-kafka not available. Please install it.")

		# sure thate Kafka broker is alive
		if AUTO_START_KAFKA_BROKER:
			try:
				self.bootstrap = ensure_kafka_broker(bootstrap=kafka_bootstrap)
			except RuntimeError as e:
				logger.error("%s", e)
				print(
					"ERREUR : impossible de démarrer KafkaDEVS.\n"
					"Vérifie que Docker Desktop est lancé puis relance la simulation."
				)
				raise
		else:
			self.bootstrap = kafka_bootstrap
			
		# Choix de l'adaptateur de wire
		self.wire = StandardWireAdapter
		
		# Group ID unique pour ce run
		group_id = f"coordinator-{int(time.time() * 1000)}"

		self.request_timeout = request_timeout

		# Kafka producer/consumer
		self._producer = Producer({
			"bootstrap.servers": self.bootstrap,
			"enable.idempotence": True,
			"acks": "all",
		})

		self._consumer = Consumer({
			"bootstrap.servers": self.bootstrap,
			"group.id": group_id,
			"auto.offset.reset": "latest",
			"enable.auto.commit": True,
			"session.timeout.ms": 30000,
		})
		self._consumer.subscribe([MS4MeKafkaWorker.OUT_TOPIC])

		### check if atomic models have been loaded properly
		assert(self.flat_priority_list != [])

		# DEVS Atomic models list
		self._atomic_models = list(self.flat_priority_list)
		self._num_atomics = len(self._atomic_models)
		self._index2model = {i: m for i, m in enumerate(self._atomic_models)}

		### workers threads
		self._workers = MultiKeyDict()
		
		logger.info("KafkaDEVS SimStrategy initialized (In-Memory Workers)")
		logger.info(f"  Bootstrap servers: {self.bootstrap}")
		logger.info(f"  Consumer group: {group_id}")
		logger.info(f"  Number of atomic models: {self._num_atomics}")
		logger.info(f"  Index Mapping:")
		for i, m in enumerate(self._atomic_models):
			logger.info(f"    Index {i} -> {m.myID} ({m.getBlockModel().label})")

	# ------------------------------------------------------------------
	#  Simulation
	# ------------------------------------------------------------------

	def simulate(self, T=1e8, **kwargs):
		"""Main simulation loop with Kafka coordination and message routing"""
		if self._simulator is None:
			raise ValueError("Simulator instance must be provided.")

		logger.info("=" * 60)
		logger.info("  KafkaDEVS Simulation Starting (In-Memory)")
		logger.info("=" * 60)
		
		self._create_workers()
		self._create_topics()

		logger.info("Waiting for workers to initialize (2s)...")
		time.sleep(2)

		### Purge old messages
		purge_kafka_topic(self._consumer, max_seconds=2.0)

		### chose the specific message type used
		return self._simulate_for_ms4me(T)
	
	# ------------------------------------------------------------------
	#  Topics & workers
	# ------------------------------------------------------------------

	def _create_workers(self):
		"""Spawn in-memory worker threads"""

		logger.info("Spawning %s worker threads...", self._num_atomics)

		for i, model in enumerate(self._atomic_models):

			worker = MS4MeKafkaWorker(model.getBlockModel().label, model, self.bootstrap)

			logger.info(f"  Model {model.myID} ({ worker.get_model_label()}):")
			logger.info(f"    Real class: {model.__class__.__module__}.{model.__class__.__name__}")
			logger.info(f"    Python file: {model.__class__.__module__}")
			logger.info(f"    OPorts: {[p.name for p in model.OPorts]}")
			logger.info(f"    IPorts: {[p.name for p in model.IPorts]}")
			logger.info(f"  Model {model.myID} ({ worker.get_model_label()}) - %s): in_topic={worker.get_topic_to_write()}, out_topic={worker.get_topic_to_read()}")

			worker.start()

			### is a dict with multiple keys
			self._workers.add([i, model.myID], worker)

		logger.info("  All %s threads started", self._num_atomics)

	def _create_topics(self):
		"""Create Kafka topics for local or standard mode."""
		
		admin = AdminClient({"bootstrap.servers": self.bootstrap})

		# Topics already existants
		try:
			metadata = admin.list_topics(timeout=10)
		except KafkaException as e:
			err = e.args[0]
			if err.code() == KafkaError._TRANSPORT:
				logger.error(
					"Unable to connect to Kafka broker at %s.\n"
					"Please verify that the 'kafkabroker' container is running and that Kafka is listening.",
					self.bootstrap,
				)
			else:
				logger.error("Kafka error while listing topics: %s", err)
			raise

		existing = set(metadata.topics.keys())

		# Build the set of topic names to create (avoids duplicates up front)
		desired = set()

		# Topics d'entrée des workers
		for w in self._workers.values():
			desired.add(w.get_topic_to_write())

		# Topic de sortie (coordinateur / collecteur)
		desired.add(MS4MeKafkaWorker.OUT_TOPIC)

		# Filtrer ceux qui n'existent pas encore
		topics_to_create = [t for t in desired if t not in existing]

		if not topics_to_create:
			logger.info(
				"All required Kafka topics already exist: %s",
				sorted(existing),
			)
			return

		logger.info("  Topics to create: %s", topics_to_create)

		new_topics = [
			NewTopic(
				t,
				num_partitions=(3 if t == MS4MeKafkaWorker.OUT_TOPIC else 1),
				replication_factor=1,
			)
			for t in topics_to_create
		]

		fs = admin.create_topics(new_topics)

		for topic, f in fs.items():
			try:
				logger.info("Waiting for topic %s creation...", topic)
				f.result()
				logger.info("  Topic %s created", topic)
			except KafkaException as e:
				err = e.args[0]
				if err.code() == KafkaError.TOPIC_ALREADY_EXISTS:
					logger.info("  Topic %s already exists", topic)
				else:
					logger.error(
						"  Error creating topic %s: code=%s, reason=%s",
						topic, err.code(), err.str(),
					)
					raise
			except Exception as e:
				logger.exception("  Unexpected error creating topic %s", topic)
				raise

	def _terminate_workers(self):
		"""Stop all worker threads"""
		logger.info("Stopping worker threads...")

		for worker in self._workers.values():
			worker.stop()

		for worker in self._workers.values():
			worker.join(timeout=2.0)

		logger.info("  All workers stopped")

	# ------------------------------------------------------------------
	#  Envoi / réception via messages typés + adaptateur de wire
	# ------------------------------------------------------------------

	def _send_msg_to_kafka(self, topic: str, msg: BaseMessage):
		""" 

		Args:
			topic (str): _description_
			msg (BaseMessage): _description_
		"""
		msg_dict = msg.to_dict()
	
		payload = json.dumps(msg_dict).encode("utf-8")

		self._producer.produce(topic, value=payload)
		self._producer.flush()

		coord_kafka_logger.debug("OUT: topic=%s value=%s", topic, payload)


	def _await_msgs_from_kafka(self, pending:list = None):
		"""
		Attend les réponses des workers pour les indices donnés.
		"""
		
		timeout = self.request_timeout

		if not pending:
			pending = [model for model in self._atomic_models]
		
		received = {}
		deadline = time.time() + timeout

		while pending and time.time() < deadline:
			msg = self._consumer.poll(timeout=0.5)
			if msg is None or msg.error():
				continue

			data = json.loads(msg.value().decode("utf-8"))
		
			coord_kafka_logger.debug(
				"IN: topic=%s value=%s",
				msg.topic(),
				json.dumps(data),
			)
			
			devs_msg = self.wire.from_wire(data)
			
			model_name = data['sender']

			### find the index corresponding to the current model
			index_to_delete = 0
			for i,m in enumerate(pending):
				if m.getBlockModel().label == model_name:
					index_to_delete = i
					break

			### pop the right model
			model = pending.pop(index_to_delete)
			
			### store the model and the assiated msg
			received[model] = devs_msg

		if pending:
			raise TimeoutError(
				f"Kafka timeout: missing indices {sorted(pending)}"
			)
		
		return received

	def _simulate_for_ms4me(self, T=1e8):
		"""Simulate using standard KafkaDEVS message routing.

		Args:
			T (_type_, optional): _description_. Defaults to 1e8.
		"""
		try:

			# STEP 0 : distributed init
			logger.info("Initializing atomic models...")

			### simulation time
			st = SimTime(t=self.ts.Get())

			for worker in self._workers.values():
				self._send_msg_to_kafka(msg=InitSim(st), 
										topic=worker.get_topic_to_write())

			
			init_workers_results = self._await_msgs_from_kafka()
			
			### Check time consistency - TODO: remove to improve sim performance
			for model in self._atomic_models:
				label = model.getBlockModel().label
				devs_msg = init_workers_results[model]
				ta = devs_msg.time.t

				### message received after a InitSim is NextTime
				assert(isinstance(devs_msg, NextTime))
				### confirmation of the time matching
				assert(ta==model.timeNext)

				logger.info(f"  Model {label}: next={model.timeNext}")

			# sys.exit(1)

			# MAIN SIMULATION LOOP
			logger.info(f"Simulation loop starting (T={T})...")
			iteration = 0
			t_start = time.time()
			old_cpu_time = 0.0

			### first tmin is calculated form kafka init messages sended by all atomic models
			tmin = min(a.time.t for a in init_workers_results.values())

			### This is the main simulation loop
			while self.ts.Get() < T and not self._simulator.end_flag:
				iteration += 1
				
				if tmin == float("inf"):
					logger.info("No more events - simulation complete")
					break
				if tmin > T:
					logger.info("Next event at t=%s exceeds T=%s", tmin, T)
					break

				### update the simulation time
				self.ts.Set(tmin)
				
				### take imminents worker and model
				imminents_worker, imminents_model = zip(*[
			    									(w, w.get_model())
    												for w in self._workers.values()
    												if w.get_model_time_next() == tmin
												]) if tmin is not None else ((), ())

				imminents_model = list(imminents_model)

				logger.info("=" * 60)
				logger.info(f"Iteration {iteration}: t={tmin}")
				logger.info(f"  Imminent models: {list(map(str,imminents_model))}")
				logger.info("=" * 60)
				
				# sys.exit(1)

				# STEP 1: send msg to execute output of imminents
				logger.info("[1/4] Executing output functions...")
				st = SimTime(t=tmin)
				for w in imminents_worker:
					self._send_msg_to_kafka(msg=SendOutput(st), 
							 				topic=w.get_topic_to_write())

				output_msgs = self._await_msgs_from_kafka(imminents_model)

				### check msg consistency
				assert(all(isinstance(msg, ModelOutputMessage) for msg in output_msgs.values()))
				
				# sys.exit(1)
				
				### juste for trace
				for model in imminents_model:
					# model = w.get_model()
					logger.info(f"  Model {model}")

					for k,v in model.myOutput.items():
						logger.info(f"    - {str(k)}: {str(v)}")

				# sys.exit(1)

				# STEP 2: routing (from ModelOutputMessage)
				logger.info("[2/4] Routing outputs to destinations...")
				externals_to_send = {}
				parent_model = (
					self._atomic_models[0].parent if self._atomic_models else None
				)

				if parent_model is None:
					logger.warning("  WARNING: No parent model, cannot route outputs")
				else:
					for model, devs_msg in output_msgs.items():

						if devs_msg is None:
							continue
						
						if not isinstance(devs_msg, ModelOutputMessage):
							logger.debug(f"  Ignoring non-output message from {model.getBlockModel().label}: {type(devs_msg).__name__}")
							continue

						outputs = devs_msg.modelOutput
						if not outputs:
							continue

						logger.info("  Model %s produced %s", model.myID, str(outputs))

						for pv in outputs:
							port_name = pv.portIdentifier
							value = pv.value

							src_port = None
							for p in model.OPorts:
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

								if src_m is model and src_p is src_port:
									dest_idx = None
									for idx, m in self._index2model.items():
										if m is dest_m:
											dest_idx = idx
											break
									if dest_idx is None:
										continue

									logger.info(
										"    -> Routing %s.%s -> %s.%s (value=%s)",
										model.myID, port_name,
										dest_m.myID, dest_p.name, value
									)

									if dest_idx not in externals_to_send:
										externals_to_send[dest_idx] = {}
									externals_to_send[dest_idx][dest_p.name] = value

				# sys.exit(1)

				# STEP 2b: external transition execution
				transition_done_msgs = {}

				if externals_to_send:
					for dest_idx, inputs in externals_to_send.items():
						pv_list = [
							PortValue(v, port, type(v).__name__)
							for port, v in inputs.items()
						]

						current_worker = self._workers.get(dest_idx)

						logger.info(f"  Sending external transitions to {current_worker.get_model_label()} model...")
						
						self._send_msg_to_kafka(msg=ExecuteTransition(st, pv_list), 
							  					topic=current_worker.get_topic_to_write())

					# récupérer les TransitionDone des modèles qui ont reçu une external
					td_ext = self._await_msgs_from_kafka([self._workers.get(i).get_model() for i in externals_to_send.keys()])
					transition_done_msgs.update(td_ext)

					### check msg consistency
					assert(all(isinstance(msg, TransitionDone) for msg in td_ext.values()))

				else:
					logger.info("  No outputs to route!")

				# sys.exit(1)

				# STEP 3: internal_transition
				### take imminents worker and model
				imminents_worker, imminents_model = zip(*[
			    									(w, w.get_model())
    												for w in self._workers.values()
    												if w.get_model_time_next() == tmin
												]) if tmin is not None else ((), ())
				imminents_model = list(imminents_model)

				logger.info(f"[3/4] Executing internal transitions for: {imminents_model}")
				for w in imminents_worker:
					self._send_msg_to_kafka(msg=ExecuteTransition(st), 
							 				topic=w.get_topic_to_write())

				td_int = self._await_msgs_from_kafka(imminents_model)
				transition_done_msgs.update(td_int)

				### check msg consistency
				assert(all(isinstance(msg, TransitionDone) for msg in td_int.values()))

				### update tmin
				tmin = min([t.nextTime.t for _,t in td_int.items()]+[t.nextTime.t for _,t in td_ext.items()])
				
				### for the progress bar of devsimpy
				self.master.timeLast = tmin
				### for stat
				self._simulator.cpu_time = old_cpu_time + (time.time() - t_start)

				# if iteration >= 3:  # garde‑fou
				# 	logger.info("Reached iteration limit (%s iterations)", iteration)
				# 	break

				# sys.exit(1)

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

		# Après la boucle principale, quand tu sais que la simu est finie
		logger.info("Broadcasting SimulationDone to all workers...")

		st = SimTime(t=self.ts.Get())
		for w in self._workers.values():
			self._send_msg_to_kafka(msg=SimulationDone(time=st), 
						   			topic=w.get_topic_to_write())

		self._terminate_workers()

		logger.info("=" * 60)
		logger.info("  MS4Me KafkaDEVS Simulation Ended")
		logger.info("=" * 60)

