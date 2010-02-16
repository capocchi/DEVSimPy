# -*- coding: utf-8 -*-

###############################################################################
# FastSimulator.py --- Classes and Tools for 'Classic' Real-Time DEVS Model Spec
#                     --------------------------------
#                            Copyright (c) 2009
#                            Laurent Capocchi
#                       Corsican University (France)
#                     --------------------------------
# Version                                        last modified:
###############################################################################
# NOTES:
###############################################################################

# Necessary to send COPIES of messages.

from itertools import*
#import threading, Queue

#import pprocess

from DEVS import AtomicDEVS, CoupledDEVS

###############################################################################
# GLOBAL VARIABLES AND FUNCTIONS
###############################################################################

# {\sl Verbose mode\/} set when {\tt __VERBOSE__} switch evaluates to true.
# Similar to {\tt #define _DEBUG_} convention in {\tt C++}.
#__VERBOSE__ = False
__CLOCK__ = False

#class Sender(threading.Thread):
	
	#def __init__(self, d, msg, queue):
		#self.__queue=queue
		#self.__d=d
		#self.__msg=msg
		#threading.Thread.__init__(self)
	
	#def run(self):
		
		#if isinstance(self.__d,CoupledDEVS):
			#CS = CoupledSolver()
			#r= CS.receive(self.__d, self.__msg)
		#else:
			#AS = AtomicSolver()
			#r= AS.receive(self.__d, self.__msg)
			
		#self.__queue.put(r)
		
class Sender:
	##
	def send(self, d, msg):
		"""Dispatch messages to the right method.
		"""
		
		if isinstance(d,CoupledDEVS):
			#CoupledSolverWorker(self, d,msg, self.__queue).start()
			#return self.__queue.get()
			CS = CoupledSolver()
			return CS.receive(d, msg)
		else:
			#AtomicSolverWorker(d,msg, self.__queue).start()
			#return self.__queue.get()
			AS = AtomicSolver()
			return AS.receive(d, msg)

#class CoupledSolverWorker(threading.Thread):

	#def __init__(self, simulator, d, msg, queue):
		#self.__queue = queue
		#self.__simulator=simulator
		#self.__d=d
		#self.__msg=msg
		#threading.Thread.__init__(self)

	#def run(self):
		#CS=CoupledSolver()
		#r = CS.receive(self.__simulator, self.__d, self.__msg)
		#self.__queue.put(r)

#class AtomicSolverWorker(threading.Thread):

	#def __init__(self, d, msg, queue):
		#self.__queue = queue
		#self.__d=d
		#self.__msg=msg
		#threading.Thread.__init__(self)

	#def run(self):
		#AS=AtomicSolver()
		#r = AS.receive(self.__d, self.__msg)
		#self.__queue.put(r)

def minEx(val1, val2):
	
	if val1 > val2:
		return val2
	else:
		return val1

def Error(message = '', esc = 1):
	"""Error-handling function: reports an error and exits interpreter if
	{\tt esc} evaluates to true.
	
	To be replaced later by exception-handling mechanism.
	"""
	from sys import exit, stderr
	stderr.write("ERROR: %s\n" % message)
	if esc:
		exit(1)

#INFINITY=4e10

###############################################################################
# SIMULATOR CLASSES
###############################################################################

class AtomicSolver:
	"""Simulator for atomic-DEVS.
	
	Atomic-DEVS can receive three types of messages: $(i,\,t)$, $(x,\,t)$ and
	$(*,\,t)$. The latter is the only one that triggers another message-
	sending, namely, $(y,\,t)$ is sent back to the parent coupled-DEVS. This is
	actually implemented as a return value (to be completed).
	"""
	#__instance = None
 
	#def __new__(cls,*args,**kwargs):
	  #"""
	  #Override the instantiation of the object
	  #"""
	  #if not cls.__instance or type(cls.__instance)!=cls:
            #cls.__instance = object.__new__(cls,*args,**kwargs)
	  #return cls.__instance
 
 
	#def destroy(self):
	  #CoupledDEVS.__instance=None
	  
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
						
			# Call the internal transition function to update the DEVS' state, and
			# update time variables:
			#prevState = aDEVS.state
		
			aDEVS.elapsed = t - aDEVS.timeLast
			aDEVS.intTransition()
			aDEVS.timeLast = t
			aDEVS.myTimeAdvance = aDEVS.timeAdvance()
			aDEVS.timeNext=aDEVS.timeLast+aDEVS.myTimeAdvance
			if aDEVS.myTimeAdvance != INFINITY: aDEVS.myTimeAdvance += t
			aDEVS.elapsed = 0
			
			if __VERBOSE__:
				print "\n\tINTERNAL TRANSITION: %s (%s)" % (aDEVS.__class__.__name__,aDEVS.myID)
				print "\t  New State: %s" % (aDEVS.state)
				
				print "\t  Output Port Configuration:"
				for I in range(0, len(aDEVS.OPorts) ):
					if aDEVS.OPorts[I] in aDEVS.myOutput.keys():
						print "\t    %s: %s" % (aDEVS.OPorts[I], aDEVS.myOutput[aDEVS.OPorts[I]])
					else:
						print "\t    %s: None" % (aDEVS.OPorts[I])
				if aDEVS.myTimeAdvance == INFINITY:
					print "\t  Next scheduled internal transition at INFINITY"
				else:
					print "\t  Next scheduled internal transition at %f" % aDEVS.myTimeAdvance
			
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
			#prevState = aDEVS.state
			aDEVS.extTransition()
			# Udpate time variables:
			aDEVS.timeLast = t
			aDEVS.myTimeAdvance = aDEVS.timeAdvance()
			aDEVS.timeNext=aDEVS.timeLast+aDEVS.myTimeAdvance
			if aDEVS.myTimeAdvance != INFINITY: aDEVS.myTimeAdvance += t
			aDEVS.elapsed = 0
			
			if __VERBOSE__:
				print "\n\tEXTERNAL TRANSITION: %s (%s)" % (aDEVS.__class__.__name__,aDEVS.myID)
				
				print "\t  Input Port Configuration:"
				for I in range(0, len(aDEVS.IPorts)):
					print "\t    %s: %s" % (aDEVS.IPorts[I], aDEVS.peek(aDEVS.IPorts[I]))
				print "\t  New State: %s" % (aDEVS.state)
				if aDEVS.myTimeAdvance == INFINITY:
					print "\t  Next scheduled internal transition at INFINITY"
				else:
					print "\t  Next scheduled internal transition at %f" % aDEVS.myTimeAdvance
			
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
	#__instance = None
 
	#def __new__(cls,*args,**kwargs):
	  #"""
	  #Override the instantiation of the object
	  #"""
	  #if not cls.__instance or type(cls.__instance)!=cls:
            #cls.__instance = object.__new__(cls,*args,**kwargs)
           
	  #return cls.__instance
 
 
	#def destroy(self):
	  #CoupledDEVS.__instance=None
	
	###
	def receive(self, cDEVS, msg):

		# For any received message, the time {\tt t} (time at which the message 
		# is sent) is the second item in the list {\tt msg}.
		t = msg[2]

		# $(*,\,t)$ message --- triggers internal transition and returns
		# $(y,\,t)$ message for parent coupled-DEVS:
		if msg[0] == 1:
			#if t != cDEVS.timeNext:
			  #Error("Bad synchronization...3", 1)
				
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
					print "\n\tCollision occured in %s, involving:" % (cDEVS.__class__.__name__)
					for I in cDEVS.immChildren:
						print "    \t   %s" % (I.__class__.__name__)
					print "\t  select chooses %s" % (dStar.__class__.__name__)
				
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
					
			#for d in cDEVS.componentSet:
				#cDEVS.myTimeAdvance = minEx(cDEVS.myTimeAdvance, d.myTimeAdvance)
			
			cDEVS.myTimeAdvance=min([c.myTimeAdvance for c in cDEVS.componentSet]+[cDEVS.myTimeAdvance])
			# Get all components which tied for the smallest time advance and append
			
			
			# each to the coupled DEVS' immChildren list
			cDEVS.immChildren = [d for d in cDEVS.componentSet if cDEVS.myTimeAdvance == d.myTimeAdvance]
	
			return cDEVS.myOutput
    
		# ${x,\,t)$ message --- triggers external transition, where $x$ is the
		# input dictionnary to the DEVS:
		elif type(msg[0]) == type({}):
			#if not(cDEVS.timeLast <= t <= cDEVS.timeNext):
			  #Error("Bad synchronization...4", 1)
			
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
			
			#cDEVS.myTimeAdvance=min([c.myTimeAdvance for c in cDEVS.componentSet]+[cDEVS.myTimeAdvance])
			#for c in cDEVS.componentSet:
				#cDEVS.myTimeAdvance = minEx(cDEVS.myTimeAdvance, c.myTimeAdvance)
			
			
			for d in cDEVS.componentSet:
				if cDEVS.myTimeAdvance > d.myTimeAdvance:
					setattr(cDEVS,'myTimeAdvance',d.myTimeAdvance)
					
			# Get all components which tied for the smallest time advance and append
			# each to the coupled DEVS' immChildren list
			#print "avant", cDEVS.immChildren
			cDEVS.immChildren = [d for d in cDEVS.componentSet if cDEVS.myTimeAdvance == d.myTimeAdvance]
			#print "apres",cDEVS.immChildren
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
      
class Simulator(Sender):
	"""Associates a hierarchical DEVS model with the simulation engine.
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
			
			# calculate how much time has passed so far
			if __CLOCK__: print "\n", "* " * 10, "CLOCK : %f" % clock
			
			self.send(self.model, (1, self.model.immChildren, clock))