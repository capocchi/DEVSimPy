#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################
# simulator.py --- Classes and Tools for 'Classic' DEVS Model Spec
#                     --------------------------------
#                            Copyright (c) 2011
#                            Laurent Capocchi
#                       Corsican University (France)
#                     --------------------------------
# Version                                        last modified: 17/11/2013
###############################################################################
# NOTES:
###############################################################################

import sys
from itertools import *
import threading
import array

from .DEVS import CoupledDEVS
#from Patterns.Strategy import SimStrategy1

from PluginManager import PluginManager

### avec ce flag, on gere a totalité des messages sur les ports une seul fois dans delta_ext.
WITHOUT_DELTA_EXT_FOR_ALL_PORT = True
### avec ce flag on peut faire de l'execution en paralle de modèle qui s'active en meme emps mais pas avec des modèles couplé dans des modèle couplé
WITH_PARALLEL_EXECUTION = False

###############################################################################
# GLOBAL VARIABLES AND FUNCTIONS
###############################################################################

def Error(message = '', esc = 1):
	"""Error-handling function: reports an error and exits interpreter if
	{\tt esc} evaluates to true.

	To be replaced later by exception-handling mechanism.
	"""
	from sys import exit, stderr
	stderr.write("ERROR: %s\n" % message)
	if esc: exit(1)

###############################################################################
# SIMULATOR CLASSES
###############################################################################

class Sender:
	"""
	"""

	def t_send(self, X, imm, t):
		"""
		"""
		threads = []
		for m in X:
			thread = ThreadingAtomicSolver(m,(dict(X[m]), imm, t))
			threads.append(thread)
			thread.start()

		for thread in threads:
			thread.finish()

	def send(self, d, msg):
		""" Dispatch messages to the right method.
		"""
		if isinstance(d, CoupledDEVS):
			CS = CoupledSolver()
			r = CS.receive(d, msg)
		else:
			AS = AtomicSolver()
			r = AS.receive(d, msg)

			PluginManager.trigger_event("SIM_BLINK", model=d, msg=msg)
			PluginManager.trigger_event("SIM_TEST", model=d, msg=msg)

		return r

class ThreadingAtomicSolver(threading.Thread):
	"""
	"""
	def __init__(self, d, msg):
		"""
		"""
		threading.Thread.__init__(self) # init the thread
		self.value = {} # initial value
		self.alive = False # controls the while loop in the run command
		self.d = d
		self.msg = msg

	def run(self): # this is the main function that will run in a separate thread
		self.alive = True
		#while self.alive:
		self.receive(self.d, self.msg)

	def receive(self, d, msg):
		self.value = AtomicSolver.receive(d, msg)

	def peek(self): # return the current value
		return self.value

	def finish(self): # close the thread, return final value
		self.alive = False # stop the while loop in 'run'
		return self.value # return value

class AtomicSolver:
	"""Simulator for atomic-DEVS.

		Singleton class.

		Atomic-DEVS can receive three types of messages: $(i,\,t)$, $(x,\,t)$ and
		$(*,\,t)$. The latter is the only one that triggers another message-
		sending, namely, $(y,\,t)$ is sent back to the parent coupled-DEVS. This is
		actually implemented as a return value (to be completed).
	"""
	_instance = None
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance=super(AtomicSolver, cls).__new__(cls,*args, **kwargs)
		return cls._instance

	###
	@staticmethod
	def receive(aDEVS, msg):

		# For any received message, the time {\tt t} (time at which the message
		# is sent) is the second item in the list {\tt msg}.
		t = msg[2]

		# $(*,\,t)$ message --- triggers internal transition and returns
		# $(y,\,t)$ message for parent coupled-DEVS:
		if msg[0] == 1:
			if t != aDEVS.timeNext:
				Error("Bad synchronization...1", 1)

			# First call the output function, which (amongst other things) rebuilds
			# the output dictionnary {\tt myOutput}:
			aDEVS.myOutput = {}
			aDEVS.outputFnc()

			aDEVS.elapsed = t - aDEVS.timeLast
			aDEVS.intTransition()

			aDEVS.timeLast = t
			aDEVS.myTimeAdvance = aDEVS.timeAdvance()
			aDEVS.timeNext = aDEVS.timeLast + aDEVS.myTimeAdvance
			if aDEVS.myTimeAdvance != INFINITY: aDEVS.myTimeAdvance += t
			aDEVS.elapsed = 0

			# The SIM_VERBOSE event occurs
			PluginManager.trigger_event("SIM_VERBOSE", model=aDEVS, msg=0)

			# Return the DEVS' output to the parent coupled-DEVS (rather than
			# sending $(y,\,t)$ message).
			return aDEVS.myOutput

		# ${x,\,t)$ message --- triggers external transition, where $x$ is the
		# input dictionnary to the DEVS:
		elif isinstance(msg[0], dict):
			if not(aDEVS.timeLast <= t <= aDEVS.timeNext):
				Error("Bad synchronization...2", 1)

			aDEVS.myInput = msg[0]

			# update elapsed time. This is necessary for the call to the external
			# transition function, which is used to update the DEVS' state.
			aDEVS.elapsed = t - aDEVS.timeLast
			aDEVS.extTransition()

			# Udpate time variables:
			aDEVS.timeLast = t
			aDEVS.myTimeAdvance = aDEVS.timeAdvance()
			aDEVS.timeNext = aDEVS.timeLast + aDEVS.myTimeAdvance
			if aDEVS.myTimeAdvance != INFINITY: aDEVS.myTimeAdvance += t
			aDEVS.elapsed = 0

			# The SIM_VERBOSE event occurs
			PluginManager.trigger_event("SIM_VERBOSE", model=aDEVS, msg=1)

		# $(i,\,t)$ message --- sets origin of time at {\tt t}:
		elif msg[0] == 0:
			aDEVS.timeLast = t - aDEVS.elapsed
			aDEVS.myTimeAdvance = aDEVS.timeAdvance()
			aDEVS.timeNext = aDEVS.timeLast + aDEVS.myTimeAdvance
			if aDEVS.myTimeAdvance != INFINITY: aDEVS.myTimeAdvance += t

		else:
			Error("Unrecognized message", 1)

###############################################################################

class CoupledSolver(Sender):
	"""Simulator (coordinator) for coupled-DEVS.

	Coupled-DEVS can receive the same three types of messages as for atomic-
	DEVS, plus the $(y,\,t)$ message. The latter is implemented as a returned
	value rather than a message. This is possible because the $(y,\,t)$ message
	is always sent to a coupled-DEVS in response from its sending a $(*,\,t)$
	message. (This implementation makes it possible to easily distinguish
	$(y,\,t)$ from $(x,\,t)$ messages... to be completed)
	Description of {\tt eventList} and {\tt dStar} (to be completed)
	"""

	_instance = None
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(Sender, cls).__new__(cls,*args, **kwargs)
		return cls._instance

	def threading_send(self, Y, cDEVS, t):

		send = self.send
		send_parallel = self.t_send

		cDEVS.timeLast = t
		cDEVS.myTimeAdvance = INFINITY
		cDEVS.myOutput.clear()

		imm = cDEVS.immChildren
		if WITHOUT_DELTA_EXT_FOR_ALL_PORT:

			X = dict((pp.host,[(pp, Y[p])]) for p in Y for pp in p.outLine)

			#for b,val in X.items():
				#if b is CoupledDEVS:
					#cDEVS.myOutput[b] = val[-1][-1]

				#if WITH_PARALLEL_EXECUTION:
					#send_parallel(X,imm,t)
				#else:
					#send(b, (dict(val), imm, t))

			X = {}
			for p in Y:
				a = Y[p]
				for pp in p.outLine:
					b = pp.host
					if b not in X:
						X[b] = [(pp,a)]
					else:
						X[b].append((pp,a))

					if b is CoupledDEVS:
						cDEVS.myOutput[b] = a

			if WITH_PARALLEL_EXECUTION:
				send_parallel(X,imm,t)
			else:
				for m in X:
					send(m, (dict(X[m]), imm, t))
		else:
			for p in Y:
				X = {}
				a = Y[p]
				for pp in p.outLine:
					X[pp] = a
					b = pp.host
					if b is CoupledDEVS:
						cDEVS.myOutput[b] = a
					send(b, (X, imm, t))

		#L.append((cDEVS.myTimeAdvance, cDEVS.myOutput, cDEVS.componentSet))

	###
	def receive(self, cDEVS, msg):

		# For any received message, the time {\tt t} (time at which the message
		# is sent) is the second item in the list {\tt msg}.
		t = msg[2]

		send = self.send

		# $(*,\,t)$ message --- triggers internal transition and returns
		# $(y,\,t)$ message for parent coupled-DEVS:
		if msg[0] == 1:
			if t != cDEVS.myTimeAdvance:
				Error("Bad synchronization...3", 1)

			# Build the list {\tt immChildren} of {\sl imminent children\/} based
			# on the sorted event-list, and select the active-child {\tt dStar}.
			# The coupled-DEVS {\tt select} function is used to decide the active-child.

			try:
				dStar = cDEVS.select(cDEVS.immChildren)
			# si pas d'imminentChildren il faut stoper la simulation
			except IndexError:
				raise IndexError

			# Send $(*,\,t)$ message to active children, which returns (or sends
			# back) message $(y,\,t)$. In the present implementation, just the
			# sub-DEVS output dictionnary $y$ is returned and stored in {\tt Y}:

			self.threading_send(send(dStar, msg), cDEVS, t)

			cDEVS.myTimeAdvance = min(array.array('d',[c.myTimeAdvance for c in cDEVS.componentSet]+[cDEVS.myTimeAdvance]))

			###each to the coupled DEVS' immChildren list
			cDEVS.immChildren = [d for d in cDEVS.componentSet if cDEVS.myTimeAdvance == d.myTimeAdvance]

			return cDEVS.myOutput

		# ${x,\,t)$ message --- triggers external transition, where $x$ is the
		# input dictionnary to the DEVS:
		elif isinstance(msg[0], dict):
			if not(cDEVS.timeLast <= t <= cDEVS.myTimeAdvance):
				Error("Bad synchronization...4", 1)

			cDEVS.myInput = msg[0]

			# Send $(x,\,t)$ messages to those sub-DEVS influenced by the coupled-
			# DEVS input ports (ref. {\tt EIC}). This is essentially the same code
			# as above that also updates the coupled-DEVS' time variables in
			# parallel.

			self.threading_send(cDEVS.myInput, cDEVS, t)

			for t in array.array('d', [d.myTimeAdvance for d in cDEVS.componentSet]):
				if cDEVS.myTimeAdvance > t:
					cDEVS.myTimeAdvance = t

			# Get all components which tied for the smallest time advance and append
			# each to the coupled DEVS' immChildren list

			cDEVS.immChildren = [d for d in cDEVS.componentSet if cDEVS.myTimeAdvance == d.myTimeAdvance]

		# $(i,\,t)$cDEVS.myOutput message --- sets origin of time at {\tt t}:
		elif msg[0] == 0:
			# Rebuild event-list and update time variables, by sending the
			# initialization message to all the children of the coupled-DEVS. Note
			# that the event-list is not sorted here, but only when the list of
			# {\sl imminent children\/} is needed. Also note that {\tt None} is
			# defined as bigger than any number in Python (stands for $+\infty$).
			cDEVS.timeLast = 0
			cDEVS.myTimeAdvance = INFINITY

			for d in cDEVS.componentSet:
				self.send(d, msg)
				cDEVS.myTimeAdvance = min(cDEVS.myTimeAdvance, d.myTimeAdvance)
				cDEVS.timeLast = max(cDEVS.timeLast, d.timeLast)

			# Get all the components which have tied for the smallest time advance
			# and put them into the coupled DEVS' immChildren list
			cDEVS.immChildren = [d for d in cDEVS.componentSet if cDEVS.myTimeAdvance == d.myTimeAdvance]

		else:
			Error("Unrecognized message", 1)

#def worker(d, msg, q):
	#CS = CoupledSolver()
	#r = CS.receive(d, msg)
	#q.put((r,d.myInput, d.myOutput, d.myTimeAdvance, d.timeLast))

###############################################################################

class Simulator(Sender):
	""" Simulator(model)

		Associates a hierarchical DEVS model with the simulation engine.
		To simulate the model, use simulate(T) strategy method.
	"""

	###
	def __init__(self, model = None):
		"""Constructor.

		{\tt model} is an instance of a valid hierarchical DEVS model. The
		constructor stores a local reference to this model and augments it with
		{\sl time variables\/} required by the simulator.
		"""

		self.model = model
		self.__augment(self.model)
#		self.__algorithm = SimStrategy1(self)

	###
	def __augment(self, d = None):
		"""Recusively augment model {\tt d} with {\sl time variables\/}.
		"""

		# {\tt timeLast} holds the simulation time when the last event occured
		# within the given DEVS, and (\tt myTimeAdvance} holds the amount of time until
		# the next event.
		d.timeLast = d.myTimeAdvance = 0.

		if isinstance(d, CoupledDEVS):
			# {\tt eventList} is the list of pairs $(tn_d,\,d)$, where $d$ is a
			# reference to a sub-model of the coupled-DEVS and $tn_d$ is $d$'s
			# time of next event.
			for subd in d.componentSet:
				self.__augment(subd)

##	def simulate(self, T = sys.maxint):
##		return self.__algorithm.simulate(T)
##
##	def getMaster(self):
##		return self.model
##
##	def setMaster(self, model):
##		self.model = model
##
##	def setAlgorithm(self, s):
##		self.__algorithm = s
##
##	def getAlgorithm(self):
##		return self.__algorithm

## Set to False to disable the use of CyDEVS...
#__USE_CYDEVS__ = True
#if __USE_CYDEVS__:
	#try:
		#from cydevs import *
	#except ImportError:
		#print("Couldn't load CyDEVS, falling back to PyDEVS")
		#print("To disable this message, run the build.sh script, or set __USE_CYDEVS__ to False in simulator.py")
