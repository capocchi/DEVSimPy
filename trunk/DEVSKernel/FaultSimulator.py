# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# FaultSimulator.py --- modification of DEVS simulator for behavioral fault simulation
#                     --------------------------------
#                        Copyright (c) 2003
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 26/12/03
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#	Atomic- and coupled-DEVS specifications adapted from:
#       	B.P.Zeigler, ''Theory of modeling and simulation: Integrating
#       	Discrete Event and Continuous Complex Dynamic Systems '',
#       Academic Press, 2000
#
#  - simulateur de fautes. Message (f,t) ajout� au simulateur sain pour pouvoir
# 	avertir un mod�le de la pr�sence d'un message fautif sur ces ports
#	(voir doc "simulateur pour BFS-DEVS")
#  - Attention la sdb pass� en param rend la macro FAULT_SIM accessible
#	elle est indispensable pour faire la sim de fautes en meme temps que la sim saine
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##
##  GLOBAL VARIABLES AND FUNCTIONS:
##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from gc import *
from copy import deepcopy
import os,sys
from DEVS import CoupledDEVS

	  
def Error(message = '', esc = 1):
  """Error-handling function: reports an error and exits interpreter if
  {\tt esc} evaluates to true.

  To be replaced later by exception-handling mechanism.
  """
  from sys import exit, stderr
  stderr.write("ERROR: %s\n" % message)
  if esc:
    exit(1)

# {\sl Verbose mode\/} set when {\tt ____VERBOSE____} switch evaluates to true.

# -----------------------------------------------------------------------------------------------------------#
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

    # (i,t) message --- sets origin of time at t:
    if msg[0] == 0:
      aDEVS.timeLast = t - aDEVS.elapsed
      aDEVS.timeNext = aDEVS.timeLast + aDEVS.timeAdvance()

    # (*,t) message --- triggers internal transition and returns
    # (y,t) message for parent coupled-DEVS:
    elif msg[0] == 1:
      if t != aDEVS.timeNext:
        Error("Bad synchronization...", 1)

      # First call the output function, which (amongst other things) rebuilds
      # the output dictionnary {\tt myOutput}:
      aDEVS.myOutput = {}
      aDEVS.outputFnc()

      # Call the internal transition function to update the DEVS' state, and
      # update time variables:
      aDEVS.state = aDEVS.intTransition()
      aDEVS.timeLast = t
      aDEVS.timeNext = aDEVS.timeLast + aDEVS.timeAdvance()
      aDEVS.elapsed = 0.

      if __VERBOSE__:
        print "\n\tINTERNAL TRANSITION: %s (%s)" % (aDEVS.myID, aDEVS)
        print "\t  New State: %s" % (aDEVS.state)
        print "\t  Output Port Configuration:"
        for I in range(0, len(aDEVS.OPorts) ):
          if aDEVS.OPorts[I] in aDEVS.myOutput.keys():
            #print "\t    %s %d: %s at %s" % (aDEVS.OPorts[I].type(),I, aDEVS.myOutput[aDEVS.OPorts[I]], \
              #str(aDEVS.myOutput[aDEVS.OPorts[I]]))
	    print "\t    %s %d: %s " % (aDEVS.OPorts[I].type(),I, aDEVS.myOutput[aDEVS.OPorts[I]])
          else:
            print "\t    %s %d: None" % (aDEVS.OPorts[I].type(),I)
        print "\t  Next scheduled internal transition at time %f \n" % aDEVS.timeNext

      # Return the DEVS' output to the parent coupled-DEVS (rather than
      # sending (y,t) message).
      return aDEVS.myOutput

    # ${x,\,t)$ message --- triggers external transition, where $x$ is the
    # input dictionnary to the DEVS:
    elif msg[0] == 2:
      if not(aDEVS.timeLast <= t <= aDEVS.timeNext):
        Error("Bad synchronization...", 1)

      aDEVS.myInput = msg[1]
      # update elapsed time. This is necessary for the call to the external
      # transition function, which is used to update the DEVS' state.
      aDEVS.elapsed = t - aDEVS.timeLast
      aDEVS.state = aDEVS.extTransition()

      aDEVS.timeLast = t
      aDEVS.timeNext = aDEVS.timeLast + aDEVS.timeAdvance()
      aDEVS.elapsed = 0

      if __VERBOSE__:
        	print "\n\tEXTERNAL TRANSITION: %s (%s)" % (aDEVS.myID, aDEVS)
        	print "\t  Input Port Configuration:"
        	for I in range(0, len(aDEVS.IPorts) ):
	   		print "\t    %s %d: %s " % (aDEVS.IPorts[I].type(),I, aDEVS.peek(aDEVS.IPorts[I]))
        	print "\t  New State: %s" % (aDEVS.state)
        	print "\t  Next scheduled internal transition at time %f \n" % aDEVS.timeNext

    # ${f,\,t)$ message --- triggers external transition, where $xf$ is the
    # input dictionnary to the DEVS:
    elif msg[0] == 3:
      if not(aDEVS.timeLast <= t <= aDEVS.timeNext):
        Error("Bad synchronization...", 1)

      aDEVS.myInput = msg[1]
      # update elapsed time. This is necessary for the call to the external
      # transition function, which is used to update the DEVS' state.
      aDEVS.elapsed = t - aDEVS.timeLast
      aDEVS.state = aDEVS.faultTransition()				#simulation de fautes comportemtales

      aDEVS.timeLast = t
      aDEVS.timeNext = aDEVS.timeLast + aDEVS.timeAdvance()
      aDEVS.elapsed = 0

      if __VERBOSE__:
        	print "\n\tFAULT TRANSITION: %s (%s)" % (aDEVS.myID, aDEVS)
        	print "\t  Input Port Configuration:"
        	for I in range(0, len(aDEVS.IPorts) ):
	   		print "\t    %s %d: %s " % (aDEVS.IPorts[I].type(),I, aDEVS.peek(aDEVS.IPorts[I]))
        	print "\t  New State: %s" % (aDEVS.state)
        	print "\t  Next scheduled internal transition at time %f \n" % aDEVS.timeNext
    else:
      Error("Unrecognized message", 1)

#    ===================================================================    #

class CoupledSolver:
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

    # (i,t) message --- sets origin of time at t:
    if msg[0] == 0:

      cDEVS.timeLast = 0.
      cDEVS.timeNext = 100000
      cDEVS.eventList = []
      for d in cDEVS.componentSet:
        self.send(d, msg)
        cDEVS.eventList.append( [d.timeNext, d] )
        cDEVS.timeNext = min(cDEVS.timeNext, d.timeNext)
        cDEVS.timeLast = max(cDEVS.timeLast, d.timeLast)

    # $(*,\,t)$ message --- triggers internal transition and returns
    # $(y,\,t)$ message for parent coupled-DEVS and (f,t) message for the faulty simulation:
    elif msg[0] == 1:
      if t != cDEVS.timeNext:
        Error("Bad synchronization...", 1)

      # Build the list {\tt immChildren} of {\sl imminent children\/} based
      # on the sorted event-list, and select the active-child {\tt dStar}. If
      # there are more than one imminent child, the coupled-DEVS {\tt select}
      # function is used to decide the active-child.
      cDEVS.eventList.sort()
      immChildren = []
      for I in cDEVS.eventList:
        if I[0] == t:
          immChildren.append(I[1])
        else:
          break
      if len(immChildren) == 1:
        dStar = immChildren[0]
      else:
        dStar = cDEVS.select(immChildren)
        if __VERBOSE__:
          print "\n\tCollision occured in %s : %s, involving:" % (cDEVS.myID, cDEVS)
          for I in immChildren:
            print "    \t   %s : %s" % (I.myID,I)
          print "\t  select chooses %s" % (dStar)

      # Send $(*,\,t)$ message to active children, which returns (or sends
      # back) message $(y,\,t)$. In the present implementation, just the
      # sub-DEVS output dictionnary $y$ is returned and stored in {\tt Y}:
      Y = self.send(dStar, msg)

      # Scan the list of sub-DEVS to find those influenced by (connected to)
      # the active child. To these sub-DEVS a message $(x,\,t)$ is sent. The
      # generation of the input dictionnary {\tt X} relies on ports'
      # {\tt inLine} attributes rather than on coupled-DEVS' {\tt IC}. The
      # coupled-DEVS time variables are also updated in parallel. This piece
      # of code, although functionnal, could be far more elegant
      # and efficient\dots
      cDEVS.timeLast = t
      cDEVS.timeNext = 100000
      cDEVS.eventList = []
      for d in cDEVS.componentSet:
        X = {}
        Xf= {}
        for p in d.IPorts:
          for pi in p.inLine:
            if pi in Y.keys():
             if Y[pi] is not None:
 				
               if 'FAULT' not in Y[pi].name.split('_'):
              		X[p] = deepcopy(Y[pi]) # only if atomic DEVS?
               else:
              		Xf[p] = deepcopy(Y[pi]) # only if faulty atomic DEVS?
              		break
#          if p.inLine in Y.keys():
#            X[p] = Y[p.inLine]
        if X != {}:
          if Xf != {}:
            # si la listes des messages sains et fautif n'est pas vide (dans le cas d'un multi process), il faut generer en sortie du model tout les signaux: fautif et sain
            X.update(Xf)
          self.send(d, [2, X, t])
          if FAULT_SIM: # dans le cas ou il y simulation de fautes il faut generer un message du type fautif pour activer la delta fault
			self.send(d, [3, X, t])
        elif Xf != {}: # le cas ou je le modele ne genere que des mesages fautifs (il se trouve sur un chemin fautif)
          self.send(d, [3, Xf, t])

        cDEVS.eventList.append( [d.timeNext, d] )
        cDEVS.timeNext = min(cDEVS.timeNext, d.timeNext)

      # Use same pattern as above to update coupled-DEVS output dictionnary
      # (once again using ports' {\tt inLine} attributes rather than
      # coupled-DEVS' {\tt EOC}). The DEVS' output is then returned to its
      # parent coupled-DEVS (rather than being sent).
      cDEVS.myOutput = {}
      for p in cDEVS.OPorts:
        for pi in p.inLine:
         if pi in Y.keys():
           cDEVS.myOutput[p] = Y[pi]
           break
#        if p.inLine in Y.keys():
#          cDEVS.myOutput[p] = Y[p.inLine]

      return cDEVS.myOutput

    # ${x,\,t)$ message --- triggers external transition, where $x$ is the
    # input dictionnary to the DEVS:
    elif msg[0] == 2:
      if not(cDEVS.timeLast <= t <= cDEVS.timeNext):
        Error("Bad synchronization...", 1)

      cDEVS.myInput = msg[1]

      # Send $(x,\,t)$ messages to those sub-DEVS influenced by the coupled-
      # DEVS input ports (ref. {\tt EIC}). This is essentially the same code
      # as above that also updates the coupled-DEVS' time variables in
      # parallel.
      cDEVS.timeLast = t
      cDEVS.timeNext = 100000
      cDEVS.eventList = []

      for d in cDEVS.componentSet:
        X = {}
        for p in d.IPorts:
          for pi in p.inLine:
	      if pi in cDEVS.myInput.keys():
              	X[p] = cDEVS.myInput[pi]
              	break
#          if p.inLine in cDEVS.myInput.keys():
#            X[p] = cDEVS.myInput[p.inLine]
        if X != {}:
          self.send(d, [2, X, t])

        cDEVS.eventList.append( [d.timeNext, d] )
        cDEVS.timeNext = min(cDEVS.timeNext, d.timeNext)

    ############################################################
    #  add for fault simulation
    ############################################################
    # ${xf,\,t)$ message --- triggers external transition, where $xf$ is the
    # input dictionnary to the DEVS:
    elif msg[0] == 3:
      if not(cDEVS.timeLast <= t <= cDEVS.timeNext):
        Error("Bad synchronization...", 1)

      cDEVS.myInput = msg[1]

      # Send $(f,\,t)$ messages to those sub-DEVS influenced by the coupled-
      # DEVS input ports (ref. {\tt EIC}). This is essentially the same code
      # as above that also updates the coupled-DEVS' time variables in
      # parallel.
      cDEVS.timeLast = t
      cDEVS.timeNext = 100000
      cDEVS.eventList = []
      for d in cDEVS.componentSet:
        Xf = {}
        for p in d.IPorts:
          for pi in p.inLine:
            if (pi in cDEVS.myInput.keys()):
              Xf[p] = cDEVS.myInput[pi]
              break
#          if p.inLine in cDEVS.myInput.keys():
#            X[p] = cDEVS.myInput[p.inLine]
        if Xf != {}:
          self.send(d, [3,Xf, t])

        cDEVS.eventList.append( [d.timeNext, d] )
        cDEVS.timeNext = min(cDEVS.timeNext, d.timeNext)

    else:
      Error("Unrecognized message", 1)

#    ===================================================================    #

class Simulator(AtomicSolver, CoupledSolver):
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

  ####
  #def __call__(self,a):
    #print "call with ",a
			
  ###
  def augment(self, d):
    """Recusively augment model {\tt d} with {\sl time variables\/}.
    """

    # {\tt timeLast} holds the simulation time when the last event occured
    # within the given DEVS, and (\tt timeNext} holds the scheduled time for
    # the next event.
    d.timeLast = d.timeNext = 0.
    if isinstance(d, CoupledDEVS):
      # {\tt eventList} is the list of pairs $(tn_d,\,d)$, where $d$ is a
      # reference to a sub-model of the coupled-DEVS and $tn_d$ is $d$'s
      # time of next event.
      d.eventList = []
      for subd in d.componentSet:
        self.augment(subd)

  ###
  def send(self, d, msg):
    """Dispatch messages to the right method.
    """

    if isinstance(d, CoupledDEVS):
      return CoupledSolver.receive(self, d, msg)
    else:
      return AtomicSolver.receive(self, d, msg)
  
  ###
  def simulate(self, T=10000):
    """Simulate the model (Root-Coordinator).

    In this implementation, the simulation stops only when the simulation
    time (stored in {\tt clock}) reaches {\tt T} (starts at 0). Other means
    to stop the simulation ({\it e.g.}, when an atomic-DEVS enters a given
    state, or when a global variable reaches a predefined value) will be
    implemented.
    """

	#      # effacement du terminal
	#     if sys.platform is not 'win32':
	#       os.system('clear')
	
	# Initialize the model --- set the simulation clock to 0.
    self.send(self.model, (0, {} ,0))
    clock = self.model.timeNext
    
	# Main loop repeatedly sends $(*,\,t)$ messages to the model's root
    # DEVS.
    while clock <= T:
      if __VERBOSE__:
        print "\x1B[1;31;40m\n", "* " * 10, "CLOCK: %f\x1B[0;37;40m" % clock, "\n"

      self.send(self.model, (1, {}, clock))

      if __VERBOSE__:
        print "\n\tROOT DEVS' OUTPUT PORT CONFIGURATION:"
        for I in range(0, len(self.model.OPorts) ):
          if self.model.OPorts[I] in self.model.myOutput.keys():
            print "\t    %s %d: %s at %s" % (self.model.OPorts[I].type(),I, \
              self.model.myOutput[self.model.OPorts[I]], \
              str(self.model.myOutput[self.model.OPorts[I]]))
          else:
            print "\t    %s %d: None" % (self.model.OPorts[I].type(),I)
            
		
      clock = self.model.timeNext
