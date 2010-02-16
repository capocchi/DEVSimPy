from copy import deepcopy

def Error(message = '', esc = 1):
  from sys import exit, stderr
  stderr.write("ERROR: %s\n" % message)
  if esc:
    exit(1)

__VERBOSE__ = True

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##  SIMULATOR CLASSES
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class AtomicSolver:

  ###
  def receive(self, aDEVS, msg, sdb):

    t = msg[1]

    # (i,t) message --- sets origin of time at t:
    if msg[0] == 0:
      aDEVS.timeLast = t - aDEVS.elapsed
      aDEVS.timeNext = aDEVS.timeLast + aDEVS.timeAdvance()

    # (*,t) message --- triggers internal transition and returns
    # (y,t) message for parent coupled-DEVS:
    elif msg[0] == 1:
      if t != aDEVS.timeNext:
        Error("Bad synchronization...", 1)

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
	print "\t  SDB = %s"%sdb

      # Return the DEVS' output to the parent coupled-DEVS (rather than
      # sending (y,t) message).

      return aDEVS.myOutput

    # ${x,\,t)$ message --- triggers external transition, where $x$ is the
    # input dictionnary to the DEVS:
    elif type(msg[0]) == type({}):
      if not(aDEVS.timeLast <= t <= aDEVS.timeNext):
        Error("Bad synchronization...", 1)

      aDEVS.myInput = msg[0]
      # update elapsed time. This is necessary for the call to the external
      # transition function, which is used to update the DEVS' state.
      aDEVS.elapsed = t - aDEVS.timeLast

      #############################
      # add for fault simulation
      # phd capocchi laurent
      # 15/10/03
      #############################
      print_fault = 0
      for msg in aDEVS.myInput.values():
		if msg.name[6:] != "FAULT":
      			aDEVS.state = aDEVS.extTransition()
			if self.sdb.FAULT_SIM:
				aDEVS.state = aDEVS.faultTransition()				# simulation saine + simulation de faute
				print_fault = 1
				break
		else:
			aDEVS.state = aDEVS.faultTransition()				# in this case, the faulty message is presente and the fault transition function is activate
			print_fault = 1
			break

      # end for modification
      # Udpate time variables:
      aDEVS.timeLast = t
      aDEVS.timeNext = aDEVS.timeLast + aDEVS.timeAdvance()
      aDEVS.elapsed = 0

      if __VERBOSE__:
      	if not print_fault:
        	print "\n\tEXTERNAL TRANSITION: %s (%s)" % (aDEVS.myID, aDEVS)
        	print "\t  Input Port Configuration:"
        	for I in range(0, len(aDEVS.IPorts) ):
          	#print "\t    %s %d: %s at %s" % (aDEVS.IPorts[I].type(),I, aDEVS.peek(aDEVS.IPorts[I]),\
           	#str(aDEVS.peek(aDEVS.IPorts[I])))
	   		print "\t    %s %d: %s " % (aDEVS.IPorts[I].type(),I, aDEVS.peek(aDEVS.IPorts[I]))
        	print "\t  New State: %s" % (aDEVS.state)
        	print "\t  Next scheduled internal transition at time %f \n" % aDEVS.timeNext
		print "\t  SDB = %s" %sdb
	else:
		print "\n\tFAULT TRANSITION: %s (%s)" % (aDEVS.myID, aDEVS)
        	print "\t  Input Port Configuration:"
        	for I in range(0, len(aDEVS.IPorts) ):
	   		print "\t    %s %d: %s " % (aDEVS.IPorts[I].type(),I, aDEVS.peek(aDEVS.IPorts[I]))
        	print "\t  New State: %s" % (aDEVS.state)
        	print "\t  Next scheduled internal transition at time %f \n" % aDEVS.timeNext
		print "\t  SDB = %s" %sdb

    else:
      Error("Unrecognized message", 1)

#    ===================================================================    #

class CoupledSolver:

  ###
  def receive(self, cDEVS, msg, sdb):

    t = msg[1]

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
    # $(y,\,t)$ message for parent coupled-DEVS:
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
        for p in d.IPorts:
          for pi in p.inLine:
            if pi in Y.keys():
              X[p] = deepcopy(Y[pi]) # only if atomic DEVS?
              break
#          if p.inLine in Y.keys():
#            X[p] = Y[p.inLine]
        if X != {}:
          self.send(d, [X, t])
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
    elif type(msg[0]) == type({}):
      if not(cDEVS.timeLast <= t <= cDEVS.timeNext):
        Error("Bad synchronization...", 1)

      cDEVS.myInput = msg[0]

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
          self.send(d, [X, t])
        cDEVS.eventList.append( [d.timeNext, d] )
        cDEVS.timeNext = min(cDEVS.timeNext, d.timeNext)

    else:
      Error("Unrecognized message", 1)

#    ===================================================================    #

class Simulator(AtomicSolver, CoupledSolver):
  """Associates a hierarchical DEVS model with the simulation engine.
  """

  ###
  def __init__(self, model, sdb):

    self.model = model
    self.augment(self.model)
    self.sdb = sdb

  ###
  def augment(self, d):
    """Recusively augment model {\tt d} with {\sl time variables\/}.
    """

    # {\tt timeLast} holds the simulation time when the last event occured
    # within the given DEVS, and (\tt timeNext} holds the scheduled time for
    # the next event.
    d.timeLast = d.timeNext = 0.
    if d.type() == 'COUPLED':
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

    if d.type() == 'COUPLED':
      return CoupledSolver.receive(self, d, msg, self.sdb)
    elif d.type() == 'ATOMIC':
      return AtomicSolver.receive(self, d, msg, self.sdb)

  ###
  def simulate(self, T=10000):
    """Simulate the model (Root-Coordinator).

    In this implementation, the simulation stops only when the simulation
    time (stored in {\tt clock}) reaches {\tt T} (starts at 0). Other means
    to stop the simulation ({\it e.g.}, when an atomic-DEVS enters a given
    state, or when a global variable reaches a predefined value) will be
    implemented.
    """

    # Initialize the model --- set the simulation clock to 0.
    self.send(self.model, (0, 0))
    clock = self.model.timeNext
    # Main loop repeatedly sends $(*,\,t)$ messages to the model's root
    # DEVS.
    while clock <= T:
      if __VERBOSE__:
        print "\x1B[1;31;40m\n", "* " * 10, "CLOCK: %f\x1B[0;37;40m" % clock, "\n"
      self.send(self.model, (1, clock))

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
