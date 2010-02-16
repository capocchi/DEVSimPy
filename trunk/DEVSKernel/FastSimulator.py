# -*- coding: utf-8 -*-

###############################################################################
# FastSimulator.py --- Classes and Tools for 'Classic' DEVS Model Spec
#                     --------------------------------
#                            Copyright (c) 2009
#                            Laurent Capocchi
#                       Corsican University (France)
#                     --------------------------------
# Version                                        last modified:
###############################################################################
# NOTES:
###############################################################################

import sys
from itertools import*
from DEVS import AtomicDEVS, CoupledDEVS

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

class Strategy:
	""" Strategy pattern for shows 
	"""

	def simulate(self, T):
		raise NotImplementedError('simulate')

class Sender:
	
	def send(self, d, msg):
		""" Dispatch messages to the right method.
		"""
		
		if isinstance(d, CoupledDEVS):
			#CoupledSolverWorker(self, d,msg, self.__queue).start()
			#return self.__queue.get()
			CS = CoupledSolver()
			return CS.receive(d, msg)
		else:
			#AtomicSolverWorker(d,msg, self.__queue).start()
			#return self.__queue.get()
			AS = AtomicSolver()
			return AS.receive(d, msg)

class AtomicSolver:
	"""Simulator for atomic-DEVS.
	
		Atomic-DEVS can receive three types of messages: $(i,\,t)$, $(x,\,t)$ and
		$(*,\,t)$. The latter is the only one that triggers another message-
		sending, namely, $(y,\,t)$ is sent back to the parent coupled-DEVS. This is
		actually implemented as a return value (to be completed).
	"""
	  
	###
	def receive(self, aDEVS, msg):
		
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
			aDEVS.timeNext=aDEVS.timeLast+aDEVS.myTimeAdvance
			if aDEVS.myTimeAdvance != INFINITY: aDEVS.myTimeAdvance += t
			aDEVS.elapsed = 0
			
			if __VERBOSE__:
				sys.stdout.write("\n\tINTERNAL TRANSITION: %s (%s)\n" % (aDEVS.__class__.__name__,aDEVS.myID))
				sys.stdout.write("\t  New State: %s\n" % (aDEVS.state))
				
				sys.stdout.write("\t  Output Port Configuration:\n")
				for I in range(0, len(aDEVS.OPorts) ):
					if aDEVS.OPorts[I] in aDEVS.myOutput.keys():
						sys.stdout.write("\t    %s: %s\n" % (aDEVS.OPorts[I], aDEVS.myOutput[aDEVS.OPorts[I]]))
					else:
						sys.stdout.write("\t    %s: None\n" % (aDEVS.OPorts[I]))
				if aDEVS.myTimeAdvance == INFINITY:
					sys.stdout.write("\t  Next scheduled internal transition at INFINITY\n")
				else:
					sys.stdout.write("\t  Next scheduled internal transition at %f\n" % aDEVS.myTimeAdvance)
			
			# Return the DEVS' output to the parent coupled-DEVS (rather than
			# sending $(y,\,t)$ message).
			return aDEVS.myOutput

		# ${x,\,t)$ message --- triggers external transition, where $x$ is the
		# input dictionnary to the DEVS:
		elif type(msg[0]) == type({}):
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
			aDEVS.timeNext=aDEVS.timeLast+aDEVS.myTimeAdvance
			if aDEVS.myTimeAdvance != INFINITY: aDEVS.myTimeAdvance += t
			aDEVS.elapsed = 0
			
			if __VERBOSE__:
				sys.stdout.write("\n\tEXTERNAL TRANSITION: %s (%s)\n" % (aDEVS.__class__.__name__,aDEVS.myID))
				
				sys.stdout.write("\t  Input Port Configuration:\n")
				for I in range(0, len(aDEVS.IPorts)):
					sys.stdout.write("\t    %s: %s\n" % (aDEVS.IPorts[I], aDEVS.peek(aDEVS.IPorts[I])))
				sys.stdout.write("\t  New State: %s\n" % (aDEVS.state))
				if aDEVS.myTimeAdvance == INFINITY:
					sys.stdout.write("\t  Next scheduled internal transition at INFINITY\n")
				else:
					sys.stdout.write("\t  Next scheduled internal transition at %f\n" % aDEVS.myTimeAdvance)
			
		# $(i,\,t)$ message --- sets origin of time at {\tt t}:
		elif msg[0] == 0:
			aDEVS.timeLast = t - aDEVS.elapsed
			aDEVS.myTimeAdvance = aDEVS.timeAdvance()
			aDEVS.timeNext=aDEVS.timeLast+aDEVS.myTimeAdvance
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
	
	###
	def receive(self, cDEVS, msg):

		# For any received message, the time {\tt t} (time at which the message 
		# is sent) is the second item in the list {\tt msg}.
		t = msg[2]

		# $(*,\,t)$ message --- triggers internal transition and returns
		# $(y,\,t)$ message for parent coupled-DEVS:
		if msg[0] == 1:
			if t != cDEVS.myTimeAdvance:
			  Error("Bad synchronization...3", 1)
				
			# Build the list {\tt immChildren} of {\sl imminent children\/} based
			# on the sorted event-list, and select the active-child {\tt dStar}. If
			# there are more than one imminent child, the coupled-DEVS {\tt select}
			# function is used to decide the active-child.
			
			if len(cDEVS.immChildren) == 1:
				dStar = cDEVS.immChildren[0]
			else:
				try:
					dStar = cDEVS.select(cDEVS.immChildren)
				# si pas d'imminentChildren il faut stoper la simulation
				except IndexError:
					raise  IndexError

				if __VERBOSE__:
					sys.stdout.write("\n\tCollision occured in %s, involving:\n" % (cDEVS.__class__.__name__))
					for I in cDEVS.immChildren:
						sys.stdout.write("    \t   %s\n" % (I.__class__.__name__))
					sys.stdout.write("\t  select chooses %s\n" % (dStar.__class__.__name__))
				
			# Send $(*,\,t)$ message to active children, which returns (or sends
			# back) message $(y,\,t)$. In the present implementation, just the
			# sub-DEVS output dictionnary $y$ is returned and stored in {\tt Y}:
			Y = self.send(dStar, msg)
			
			cDEVS.timeLast = t
			cDEVS.myTimeAdvance = INFINITY
			cDEVS.myOutput.clear()
			
			send=self.send
			for p in Y:
				X={}
				for pp in p.outLine:
					X[pp]=Y[p]
					if pp.host is CoupledDEVS:
						cDEVS.myOutput[pp.host]=Y[p]
					send(pp.host, [X, cDEVS.immChildren, t])
					
			cDEVS.myTimeAdvance=min([c.myTimeAdvance for c in cDEVS.componentSet]+[cDEVS.myTimeAdvance])
			# Get all components which tied for the smallest time advance and append
			
			
			# each to the coupled DEVS' immChildren list
			cDEVS.immChildren = [d for d in cDEVS.componentSet if cDEVS.myTimeAdvance == d.myTimeAdvance]
	
			return cDEVS.myOutput
    
		# ${x,\,t)$ message --- triggers external transition, where $x$ is the
		# input dictionnary to the DEVS:
		elif type(msg[0]) == type({}):
			if not(cDEVS.timeLast <= t <= cDEVS.myTimeAdvance):
			  Error("Bad synchronization...4", 1)
			
			cDEVS.myInput = msg[0]
		
			# Send $(x,\,t)$ messages to those sub-DEVS influenced by the coupled-
			# DEVS input ports (ref. {\tt EIC}). This is essentially the same code
			# as above that also updates the coupled-DEVS' time variables in
			# parallel.
			cDEVS.timeLast = t
			cDEVS.myTimeAdvance = INFINITY
			cDEVS.myOutput.clear()
		
			send=self.send
			imm=cDEVS.immChildren
			for p in cDEVS.myInput:
				X={}
				for pp in p.outLine:
					X[pp]=cDEVS.myInput[p]			
					if pp.host is CoupledDEVS:
						cDEVS.myOutput[pp.host]=cDEVS.myInput[p]
					send(pp.host, [X, imm, t])
			
			
			for d in cDEVS.componentSet:
				if cDEVS.myTimeAdvance > d.myTimeAdvance:
					setattr(cDEVS,'myTimeAdvance',d.myTimeAdvance)
					
			# Get all components which tied for the smallest time advance and append
			# each to the coupled DEVS' immChildren list
			
			cDEVS.immChildren = [d for d in cDEVS.componentSet if cDEVS.myTimeAdvance == d.myTimeAdvance]
		
		# $(i,\,t)$ message --- sets origin of time at {\tt t}:
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
 
###############################################################################
      
class Simulator(Sender, Strategy):
	""" Simulator(model)

		Associates a hierarchical DEVS model with the simulation engine.
		To simulate the model, use simulate(T) strategy method.
	"""
	
	###
	def __init__(self, model):
		"""Constructor.
	
		{\tt model} is an instance of a valid hierarchical DEVS model. The
		constructor stores a local reference to this model and augments it with
		{\sl time variables\/} required by the simulator.
		"""
		self.model = model
		self.augment(self.model)
		
		global __VERBOSE__ 
		global __FAULT_SIM__

		__VERBOSE__ = model.VERBOSE
		__FAULT_SIM__ = model.FAULT_SIM

	###
	def augment(self, d):
		"""Recusively augment model {\tt d} with {\sl time variables\/}.
		"""
	
		# {\tt timeLast} holds the simulation time when the last event occured
		# within the given DEVS, and (\tt myTimeAdvance} holds the amount of time until
		# the next event.
		d.timeLast = d.myTimeAdvance = 0.
		if isinstance(d,CoupledDEVS):
			# {\tt eventList} is the list of pairs $(tn_d,\,d)$, where $d$ is a
			# reference to a sub-model of the coupled-DEVS and $tn_d$ is $d$'s
			# time of next event.
			for subd in d.componentSet:
				self.augment(subd)

	###
	def simulate(self, T=100000):
		"""Simulate the model (Root-Coordinator).
		"""
	
		# Initialize the model --- set the simulation clock to 0.
		self.send(self.model, (0, [], 0))
		
		clock=0.0
		# Main loop repeatedly sends $(*,\,t)$ messages to the model's root DEVS.
		while clock <=T:
			
			clock=self.model.myTimeAdvance
					
			self.send(self.model, (1, self.model.immChildren, clock))