# -*- coding: utf-8 -*-

from Domain.Myths.MythDomainBehavior import MythDomainBehavior
from Domain.Myths.Object import*
	 
class MythemADEVS(MythDomainBehavior):
	
	
	def __init__(self, a=None, x=None, name=None):
	
		MythDomainBehavior.__init__(self)
		
		# TOTAL STATE:
		#  Define 'state' attribute (initial sate):
		self.a = a
		self.x = x
		
		# ELAPSED TIME:
		#  Initialize 'elapsed time' attribute if required.
		#  (by default (if not set by user), self.elapsed is initialized to 0.0)
		self.elapsed = 0.0
		#  With elapsed time for example initially 1.1 and 
		#  this SampleADEVS initially in 
		#  a state which has a time advance of 60,
		#  there are 60-1.1 = 58.9 time-units remaining until the first 
		#  internal transition 
		
		# HV: check in simulator that elapsed can not be larger than
		# timeAdvance
		
		# PORTS:
		#  Declare as many input and output ports as desired
		#  (usually store returned references in local variables):
		#self.IN = self.addInPort()
		#self.OUT = self.addOutPort()
		#pickle.dump(self.IN,f)
		#pickle.dump(self.OUT,f)
		#print "faut-il sauver le ports??????????????"
		#listesauv.append(self.IN)
		#listesauv.append(self.OUT)
		#f.close()
	
	###
	def extTransition(self):
		"""External Transition Function."""
		
		# Compute and return the new state based (typically) on current
		# State, Elapsed time parameters and calls to 'self.peek(self.IN)'.
		# When extTransition gets invoked, input has arrived
		# on at least one of the input ports. Thus, peek() will
		# return a non-None value for at least one input port.
		
		evenemt= self.peek(self.IPorts[0])
		
		# state = self.state
		
		# Typical logic:
		
		# if input == some_input_1:
		#  if state == some_state_1:
		#  return SampleADEVSState(new state parameters)
		# if state in (some set of states):
		#  return SampleADEVSState(other new state parameters)
		# else:
		#  raise DEVSException(\
		#   "unknown state <%s> in SampelADEVS external transition function"\
		#  % state)
		
		# if input == some_input_2:
		#   ...
		
		# ...
		
		# raise DEVSException(\
		#  "unknown input <%s> in SampelADEVS external transition function"\
		# % input) 
		
		###
		# def intTransition(self):
		#  """Internal Transition Function.
		# """
		
		# Compute and return the new state  based (typically) on current State.
		# Remember that intTransition gets called after the outputFnc,
		# timeAdvance time after the current state was entered.
		
		#  state = self.state
		
		# Typical logic:
		
		#  if state == some_state_1:
		#    return SampleADEVSState(new state parameters)
		#  if state in (some set of states):
		#   return SampleADEVSState(other new state parameters)
		# ...
		# else:
		#  raise DEVSException(\
		#  "unknown state <%s> in SampelADEVS external transition function"\
		#  % state)
		
		###
		# def outputFnc(self):
		#  """Output Function.
		# """
		
		# Send events via a subset of the atomic-DEVS' 
		# output ports by means of the 'poke' method.
		# More than one port may be poke-d.
		# The content of the messages is based (typically) on the current State.
		# 
		# BEWARE: ouput is based on the CURRENT state
		# and is produced BEFORE making the internal transition.
		# Often, we want output based on the NEW state (which
		# the system will transition to by means of the internal 
		# transition. The solution is to keep the NEW state in mind
		# when poke-ing the output. 
		# This will only work if the internal transition function 
		# is deterministic !
		
		# state = self.state
		
		# if state == some_state_1:
		#    self.poke(self.OUT, SampleEvent(some params))
		#  elif state == some_state_2:
		#    self.poke(self.OUT, SampleEvent(some other params))
		# NOT self.poke(self.OBSERVED, "grey")
		# ...
		# else:
		#   raise DEVSException(\
		#     "unknown state <%s> in SampelADEVS external transition function"\
		#    % state)
		
		###
		# def timeAdvance(self):
		#   """Time-Advance Function.
		#  """
		
		# Compute 'ta', the time to the next scheduled internal transition,
		# based (typically) on the current State.
		
		# Note how it 
		#  state = self.state
		
		#  if state == some_state_1:
		#   return 20
		# elif state == some_state_2:
		#   return 10.123 
		#  ...
		# elif state == passive_state:
		#   return INFINITY 
		# else:
		#  raise DEVSException(\
		#    "unknown state <%s> in SampelADEVS time advance function"\
		#   % state)
		
		#return ta
	def __str__(self):
		return "MythemADEVS"