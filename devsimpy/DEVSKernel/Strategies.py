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
# New: Kafka-based distributed strategy derived from DirectCouplingPyDEVSSimStrategy
# ---------------------------------------------------------------------------
# Requires: pip install confluent-kafka
try:
	from confluent_kafka import Producer, Consumer
except Exception:
	Producer = None
	Consumer = None

class SimStrategyKafka(DirectCouplingPyDEVSSimStrategy):
	"""
	Kafka-backed strategy: the root coordinator orchestrates AtomicSolver workers
	via Kafka. Optionally auto-spawns a worker per atomic model at simulate().
	"""
	def __init__(self, simulator=None, kafka_bootstrap="localhost:9092",
				 cmd_topic="strategy.commands", evt_topic="strategy.events",
				 group_id="root-coord", request_timeout=30.0):
		super().__init__(simulator)
		if Producer is None or Consumer is None:
			raise RuntimeError("confluent-kafka not available. Please install it.")
		self.bootstrap = kafka_bootstrap
		self.cmd_topic = cmd_topic
		self.evt_topic = evt_topic
		self.group_id = group_id
		self.request_timeout = request_timeout

		self._producer = Producer({
			"bootstrap.servers": self.bootstrap,
			"enable.idempotence": True,
			"acks": "all",
		})
		self._consumer = Consumer({
			"bootstrap.servers": self.bootstrap,
			"group.id": self.group_id,
			"auto.offset.reset": "earliest",
			"enable.auto.commit": False,
		})
		self._consumer.subscribe([self.evt_topic])

		self._id2model = {str(m.myID): m for m in self.flat_priority_list}
		self._spawned = []

	# --------- Worker spawning helpers ----------
	def _build_spawn_env(self, atomic_id: str):
		env = os.environ.copy()
		env["KAFKA_BOOTSTRAP"] = self.bootstrap
		env["CMD_TOPIC"] = self.cmd_topic
		env["EVT_TOPIC"] = self.evt_topic
		env["WORKER_GROUP_ID"] = "atomic-workers"
		env["ATOMIC_ID"] = atomic_id
		env["PYTHONPATH"] = os.pathsep.join([env.get("PYTHONPATH", ""), os.getcwd()])
		return env

	def _spawn_worker_cmd(self, atomic_id: str, worker_script: str = "atomic_worker.py", extra_args: list = None):
		import sys as _sys
		args = [_sys.executable, os.path.join("DEVSKernel","KafkaDEVS",worker_script), "--single", "--atomic-id", atomic_id]
		if extra_args:
			args.extend(extra_args)
		return args

	def _spawn_workers_for_all_atomics(self, worker_script="atomic_worker.py"):
		import subprocess
		self._spawned = []
		for m in self.flat_priority_list:
			aid = str(m.myID)
			env = self._build_spawn_env(aid)
			cmd = self._spawn_worker_cmd(aid, worker_script)
			proc = subprocess.Popen(cmd, env=env)
			self._spawned.append((aid, proc))

	def _terminate_spawned_workers(self, timeout=5.0):
		import time as _time
		if not self._spawned:
			return
		# Ask graceful shutdown via Kafka
		for aid, _ in self._spawned:
			self._send_cmd(aid, {"op": "shutdown", "t": self.ts.Get(), "corr_id": "shutdown", "atomic_id": aid})
		t0 = _time.time()
		for aid, proc in self._spawned:
			try:
				proc.wait(timeout=max(0.0, timeout - (_time.time() - t0)))
			except Exception:
				try:
					proc.terminate()
				except Exception:
					pass
		self._spawned = []

	# --------- Kafka send/receive ----------
	def _send_cmd(self, atomic_id: str, payload: dict):
		self._producer.produce(self.cmd_topic, json.dumps(payload), key=atomic_id)
		self._producer.poll(0)

	def _broadcast(self, ids, payload):
		for aid in ids:
			p = dict(payload)
			p["atomic_id"] = aid
			self._send_cmd(aid, p)

	def _await_events(self, expected_ids, corr_id, kinds=None):
		import json as _json, time as _time
		pending = set(expected_ids)
		received = {}
		deadline = _time.time() + self.request_timeout
		while pending and _time.time() < deadline:
			msg = self._consumer.poll(0.1)
			if msg is None or msg.error():
				continue
			try:
				data = _json.loads(msg.value().decode())
			except Exception:
				continue
			if data.get("corr_id") != corr_id:
				continue
			op = data.get("op")
			if kinds and op not in kinds:
				continue
			key = msg.key().decode() if msg.key() else None
			if key in pending:
				received[key] = data
				pending.remove(key)
		if pending:
			raise TimeoutError(f"Kafka timeout: missing {sorted(pending)} for corr_id={corr_id}")
		return received

	def _route_outputs_build_X(self, out_events):
		# out_events: dict[atomic_id] -> { "y": {OPortName: value}, ... }
		X = {}
		for src_id, evt in out_events.items():
			ydict = evt.get("y", {}) or {}
			src_model = self._id2model[src_id]
			for p in src_model.OPorts:
				if p.name not in ydict:
					continue
				val = ydict[p.name]
				if hasattr(p, "weak"):
					for _prio, host_model, _exec in p.weak.GetHosts():
						did = str(host_model.myID)
						in_name = host_model.IPorts[0].name if host_model.IPorts else "IN"
						X.setdefault(did, {})[in_name] = val
		return X

	# --------- Main simulate ----------
	def simulate(self, T=1e8, spawn_workers=True, worker_script="atomic_worker.py"):
		if self._simulator is None:
			raise ValueError("Simulator instance must be provided to SimStrategyKafka.")
		
		print("\nKafkaDEVS SimStrategy: using Kafka bootstrap servers:", self.bootstrap)
			
		# Optional auto-spawn: one worker per atomic model
		if spawn_workers:
			self._spawn_workers_for_all_atomics(worker_script)

		try:
			# i,,0 to all atomics
			atomic_ids = [str(m.myID) for m in self.flat_priority_list]
			corr_id = 0.0
			self._broadcast(atomic_ids, {"op": "init", "t": 0.0, "corr_id": corr_id})
			self._await_events(atomic_ids, corr_id, kinds={"ack"})

			t_start = time.time()
			old_cpu_time = 0
			condition = lambda clk: HasActiveChild(getFlatPriorityList(self.master, [])) if self._simulator.ntl else clk <= T

			L = [m.myTimeAdvance for m in self.flat_priority_list if m.myTimeAdvance < INFINITY] or [INFINITY]
			self.ts.Set(min(L))

			while condition(self.ts.Get()) and self._simulator.end_flag == False:
				if self._simulator.thread_sleep:
					time.sleep(self._simulator._sleeptime)
				elif self._simulator.thread_suspend:
					while self._simulator.thread_suspend:
						time.sleep(1.0)
					old_cpu_time = self._simulator.cpu_time
					t_start = time.time()
				else:
					PluginManager.trigger_event("SIM_VERBOSE", self.master, None, clock=self.ts.Get())
					# Determine tmin and imminents
					imminents = []
					tmin = float("inf")
					for m in self.flat_priority_list:
						if m.myTimeAdvance < tmin:
							tmin = m.myTimeAdvance
							imminents = [m]
						elif m.myTimeAdvance == tmin:
							imminents.append(m)
					if tmin == float("inf"):
						break
					corr_id = tmin
					imm_ids = [str(m.myID) for m in imminents]

					# 1) Request outputs and internal transition
					self._broadcast(imm_ids, {"op": "step-int", "t": tmin, "corr_id": corr_id})
					out_events = self._await_events(imm_ids, corr_id, kinds={"y"})

					# 2) Build X and send external transitions
					X = self._route_outputs_build_X(out_events)
					dest_ids = list(X.keys())
					for did in dest_ids:
						self._send_cmd(did, {"op": "step-ext", "t": tmin, "inputs": X[did], "corr_id": corr_id})
					if dest_ids:
						self._await_events(dest_ids, corr_id, kinds={"ack"})

					# 3) Sync state to compute next min
					self._broadcast(atomic_ids, {"op": "state-ack", "t": tmin, "corr_id": corr_id})
					states = self._await_events(atomic_ids, corr_id, kinds={"ack-state"})
					new_min = float("inf")
					for m in self.flat_priority_list:
						s = states.get(str(m.myID), {})
						ta = s.get("myTimeAdvance", m.myTimeAdvance)
						m.myTimeAdvance = ta
						if ta < new_min:
							new_min = ta
					self.ts.Set(new_min if new_min != float("inf") else self.ts.Get())

					self.master.timeLast = self.ts.Get() if self.ts.Get() != INFINITY else self.master.timeLast
					self._simulator.cpu_time = old_cpu_time + (time.time()-t_start)

			self._simulator.terminate()
		finally:
			# Try to shutdown workers gracefully
			if spawn_workers:
				self._terminate_spawned_workers()
