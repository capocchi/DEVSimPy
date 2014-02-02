# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Strategy.py --- Strategy Pattern
#                     --------------------------------
#                                Copyright (c) 2014
#                                 Laurent CAPOCCHI
#                               University of Corsica
#                     --------------------------------
# Version 3.1                                      last modified:  23/03/12
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import sys
import time
import copy
import weakref
import threading
import heapq
import inspect

import __builtin__
import re
import os

# import Core.DEVSKernel.PyDEVS.DEVS as DEVS
import Core.Utilities.pluginmanager as pluginmanager

### import the DEVS module depending on the selected DEVS package in DEVSKernel directory
for pydevs_dir in __builtin__.__dict__['DEVS_DIR_PATH_DICT']:
    path = __builtin__.__dict__['DEVS_DIR_PATH_DICT'][pydevs_dir]
    ### split from DEVSKernel string and replace separator with point
    d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')
    exec "import Core.DEVSKernel%s.DEVS as %s"%(d,pydevs_dir)

#import DEVSKernel.PyDEVS.DEVS as PyDEVS
#import DEVSKernel.PyPDEVS.DEVS as PyPDEVS

def getFlatImmChildrenList(model, flat_imm_list=None):
	""" Set priority flat list
	"""
	if not flat_imm_list: flat_imm_list = []

	for m in model.immChildren:
		if isinstance(m, PyDEVS.AtomicDEVS):
			flat_imm_list.append(m)
		elif isinstance(m, PyDEVS.CoupledDEVS):
			getFlatImmChildrenList(m, flat_imm_list)

	return flat_imm_list


def getFlatPriorityList(model, flat_priority_list=None):
	""" Set priority flat list
	"""
	if not flat_priority_list: flat_priority_list = []

	### if priority list never edited, priority is componentList order. 
	if hasattr(model, 'PRIORITY_LIST') and model.PRIORITY_LIST != []:
		L = model.PRIORITY_LIST
	else:
		L = model.componentSet

	for m in L:
		if isinstance(m, PyDEVS.AtomicDEVS):
			flat_priority_list.append(m)
		elif isinstance(m, PyDEVS.CoupledDEVS):
			getFlatPriorityList(m, flat_priority_list)
		else:
			sys.stdout.write(_('Unknow model'))

	return flat_priority_list


def HasActiveChild(L):
	""" Return true if a children of master is active
	"""
	return L != [] and True in map(lambda a: a.timeNext != INFINITY, L)


class SimStrategy:
	""" Strategy abstract class or interface 
	"""

	def __init__(self, simulator=None):
		self._simulator = simulator

	def simulate(self, T=sys.maxint):
		""" Simulate abstract method
		"""
		pass


class SimStrategy1(SimStrategy):
	""" Original strategy for PyDEVS simulation
	"""

	def __init__(self, simulator=None):
		SimStrategy.__init__(self, simulator)

	def simulate(self, T=sys.maxint):
		"""Simulate the model (Root-Coordinator).
		"""

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


class SimStrategy2(SimStrategy):
	""" Strategy for DEVSimPy hierarchical simulation.

		This strategy is based on Zeigler's hierarchical simulation algorithm based on atomic and coupled Solver.
	"""

	def __init__(self, simulator=None):
		SimStrategy.__init__(self, simulator)

	def simulate(self, T=sys.maxint):
		"""
		"""

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
				pluginmanager.trigger_event("SIM_VERBOSE", clock=clock)

				send(master, (1, {}, clock))

				clock = master.myTimeAdvance

				self._simulator.cpu_time = old_cpu_time + (time.time() - t_start)

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
	#print "thread version"
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
		apply(val[2], (val[1],))

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
	return filter(lambda a: a[1] is not None, map(lambda p: (p, peek(p)), self.IPorts))

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

	def AddHosts(self, p):
		""" Make host list composed by tuple of priority, model and transition function
		"""
		model = p.host
		v = (model.priority / 10000.0, model, execExtTransition)
		if v not in self._host:
			if hasattr(model, 'priority'):
				self._host.append(v)

	def GetHosts(self):
		return self._host


def FlatConnection(p1, p2):
	"""
	"""
	if isinstance(p1.host, PyDEVS.AtomicDEVS) and isinstance(p2.host, PyDEVS.AtomicDEVS):
		if isinstance(p1, PyDEVS.OPort) and isinstance(p2, PyDEVS.IPort):
			#print str(p1.host.getBlockModel().label), '->', str(p2.host.getBlockModel().label)
			if not isinstance(p1.weak, weakref.ProxyType):
				wr = weakref.proxy(p1.weak)
				p2_weak_old = p2.weak
				if not isinstance(p2.weak, weakref.ProxyType):
					#print "yes"
					p2.weak = wr
				else:
					p1.weak = p2.weak
				#print "\t",id(wr), "weakref (%d)"%id(p1.weak), "->", id(p2.weak), "old (%d)"%id(p2_weak_old)
			else:
				p2.weak = p1.weak
				#print '\t', id(p1.weak), "->", id(p2.weak)

			## build hosts list in WeakValue class
			p1.weak.AddHosts(p2)

	elif isinstance(p1.host, PyDEVS.AtomicDEVS) and isinstance(p2.host, PyDEVS.CoupledDEVS):
		if isinstance(p1, PyDEVS.OPort):
			### update outLine port list removing ports of coupled model
			p1.outLine = filter(lambda a: isinstance(a.host, PyDEVS.AtomicDEVS), p1.outLine)
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

	for i, m in enumerate(atomic_model_list):
		m.elapsed = m.timeLast = m.timeNext = 0.0
		m.myTimeAdvance = m.timeAdvance()
		m.poke = poke
		m.peek = peek
		funcType = type(PyDEVS.AtomicDEVS.peek_all)
		m.peek_all = funcType(peek_all, m, PyDEVS.AtomicDEVS)
		setattr(m, 'priority', i)
		setattr(m, 'ts', ts())

	for m in atomic_model_list:
		for p1 in m.OPorts:
			if not hasattr(p1, 'weak'): setattr(p1, 'weak', WeakValue(p1))
			for p2 in p1.outLine:
				if not hasattr(p2, 'weak'): setattr(p2, 'weak', WeakValue(p2))

				#p2.weak = p1.weak
				#print "Connection for ",p1.host.getBlockModel().label, p1.weak, "to", p2.host.getBlockModel().label, p2.weak
				FlatConnection(p1, p2)

		for p1 in m.IPorts:
			if not hasattr(p1, 'weak'): setattr(p1, 'weak', WeakValue(p1))
			for p2 in p1.inLine:
				if not hasattr(p2, 'weak'): setattr(p2, 'weak', WeakValue(p2))

			#p1.weak = p2.weak
			#print "Connection for ",p1.host.getBlockModel().label, p1.weak, "to", p2.host.getBlockModel().label, p2.weak
			#FlatConnection(p1,p2)

###
def execExtTransition(m):
	"""
	"""

	ts = m.ts.Get()

	m.elapsed = ts - m.timeLast

	m.extTransition()

	m.timeLast = ts
	m.myTimeAdvance = m.timeAdvance()
	m.timeNext = m.timeLast + m.myTimeAdvance
	if m.myTimeAdvance != INFINITY: m.myTimeAdvance += ts
	m.elapsed = 0.0

	# The SIM_VERBOSE event occurs
	pluginmanager.trigger_event("SIM_VERBOSE", model=m, msg=1)
	pluginmanager.trigger_event("SIM_BLINK", model=m, msg=[{}])
	pluginmanager.trigger_event("SIM_TEST", model=m, msg=[{}])

	return m

###
def execIntTransition(m):
	"""
	"""

	ts = m.ts.Get()

	if m.timeNext != INFINITY:
		m.outputFnc()

	m.elapsed = ts - m.timeLast

	m.intTransition()
	m.timeLast = ts
	m.myTimeAdvance = m.timeAdvance()
	m.timeNext = m.timeLast + m.myTimeAdvance
	if m.myTimeAdvance != INFINITY: m.myTimeAdvance += ts
	m.elapsed = 0.0

	# The SIM_VERBOSE event occurs
	pluginmanager.trigger_event("SIM_VERBOSE", model=m, msg=0)
	pluginmanager.trigger_event("SIM_BLINK", model=m, msg=[1])
	pluginmanager.trigger_event("SIM_TEST", model=m, msg=[1])


class Clock(object):
	def __init__(self, time):
		self._val = time

	def Get(self):
		return self._val

	def Set(self, val):
		self._val = val


###
class SimStrategy3(SimStrategy):
	""" Strategy 3 for DEVSimPy thread-based direct-coupled simulation

		The simulate methode use heapq tree-like data library to manage model priority for activation
		and weak library to simplify the connexion algorithm between port.
		The THREAD_LIMIT control the limit of models to thread (default 5).
		The performance of this algorithm depends on the THREAD_LIMIT number and the number of coupled models.
	"""

	def __init__(self, simulator=None):
		""" Cosntructor.
		"""

		SimStrategy.__init__(self, simulator)

		### simulation time
		self.ts = Clock(0.0)

		### master model and flat list of atomic model
		self.master = self._simulator.getMaster()
		self.flat_priority_list = getFlatPriorityList(self.master, [])

		### init all atomic model from flat list
		setAtomicModels(self.flat_priority_list, weakref.ref(self.ts))

		### udpate the componentSet list of master (that no longer contains coupled model)
		self.master.componentSet = self.flat_priority_list
	def simulate(self, T=sys.maxint):
		"""
		"""

		### ref to cpu time evaluation
		t_start = time.time()
		### if suspend, we could store the future ref
		old_cpu_time = 0

		### stopping condition depend on the ntl (no time limit for the simulation)
		condition = lambda clk: HasActiveChild(getFlatPriorityList(self.master, [])) if self._simulator.ntl else clk <= T

		### simulation time and list of flat models ordered by devs priority
		L = [m.myTimeAdvance for m in self.flat_priority_list if m.myTimeAdvance < INFINITY] or [INFINITY]
		self.ts.Set(min(L))
		formated_priority_list = [(1 + i / 10000.0, m, execIntTransition) for i, m in enumerate(self.flat_priority_list)]

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
				pluginmanager.trigger_event("SIM_VERBOSE", self.master, None, clock=self.ts.Get())

				### tree-like data structure ordered by devsimpy priority
				priority_scheduler = filter(lambda a: self.ts.Get() == a[1].myTimeAdvance, formated_priority_list)
				heapq.heapify(priority_scheduler)

				### TODO: execute with process of model are parallel !
				while priority_scheduler:
					### get most priority model and apply its internal transition
					priority, model, transition_fct = heapq.heappop(priority_scheduler)
					apply(transition_fct, (model,))

				### update simulation time
				self.ts.Set(min([m.myTimeAdvance for m in self.flat_priority_list]))

				### just for progress bar
				self.master.timeLast = self.ts.Get() if self.ts.Get() != INFINITY else self.master.timeLast
				self._simulator.cpu_time = old_cpu_time + (time.time() - t_start)

		self._simulator.terminate()

# A. Simulate forever.
#    The termination_condition function never returns True.
#
def terminate_never(model, clock):
	return False


class SimStrategy4(SimStrategy):
    """ Original strategy for PyPDEVS simulation
    """

    def __init__(self, simulator = None):
    	SimStrategy.__init__(self, simulator)

    def simulate(self, T = sys.maxint):
    	"""Simulate the model (Root-Coordinator).
    	"""

    	### for all available DEVS package (keys of built-in DEVS_DIR_PATH_DICT dictionary)
    	for pydevs_dir in __builtin__.__dict__['DEVS_DIR_PATH_DICT']:
    		### only the selected one
    		if pydevs_dir == __builtin__.__dict__['DEFAULT_DEVS_DIRNAME']:
    			path = __builtin__.__dict__['DEVS_DIR_PATH_DICT'][pydevs_dir]
    			### split from DEVSKernel string and replace separator with point
    			d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')
    			exec "from DEVSKernel%s.simulator import Simulator"%d

        S = Simulator(self._simulator.model)

        ### old version of PyPDEVS
        if len(inspect.getargspec(S.simulate).args) > 1:

        	kwargs = {'verbose':True}

            ### TODO
        	if self._simulator.ntl:
        		kwargs['termination_condition']=terminate_never
        	else:
        		kwargs['termination_time']=T

        	S.simulate(**kwargs)

        ### new version of PyPDEVS (due to the number of config param which is growing)
        else:

            ### see simconfig.py to have informations about setters
            S.setVerbose(None)

            ### TODO
            if self._simulator.ntl:
                S.setTerminationCondition(terminate_never)
            else:
                S.setTerminationTime(T)

            S.setClassicDEVS()
            S.simulate()

    	self._simulator.terminate()