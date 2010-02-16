###############################################################################
# DEVS.py --- Classes and Tools for 'Classic' DEVS Model Specification
#                     --------------------------------
#                            Copyright (c) 2000
#                          Jean-Sébastien  BOLDUC
#                             Hans  Vangheluwe
#                       McGill University (Montréal)
#                     --------------------------------
# Version 1.0                                        last modified: 01/11/01
###############################################################################
#
# GENERAL NOTES AND REMARKS:
#
# Atomic- and coupled-DEVS specifications adapted from:
#       B.P.Zeigler, ''Theory of modeling and simulation: Integrating
#       Discrete Event and Continuous Complex Dynamic Systems '',
#       Academic Press, 2000
#
###############################################################################

###############################################################################
# RT_DEVS.py --- Classes and Tools for 'Classic' Real-Time DEVS Model Spec
#                     --------------------------------
#                            Copyright (c) 2003
#                             Spencer  Borland
#                             Hans  Vangheluwe
#                       McGill University (Montréal)
#                     --------------------------------
# Version 1.1                                        last modified: 17/02/03
###############################################################################
# NOTES:
# This implementation is based on Jean-Sebastien's 2000 DEVS.py code.  There 
# are only a few modifications in the Simulator code.  This code is easy
# to use with other modules such as a Tk GUI that wish to use DEVS as its
# real-time engine.
###############################################################################

# Necessary to send COPIES of messages.
from copy import deepcopy
from threading import Thread

###############################################################################
# GLOBAL VARIABLES AND FUNCTIONS
###############################################################################

# {\sl Verbose mode\/} set when {\tt __VERBOSE__} switch evaluates to true.
# Similar to {\tt #define _DEBUG_} convention in {\tt C++}.
__VERBOSE__ = 1

def Error(message = '', esc = 1):
  """Error-handling function: reports an error and exits interpreter if
  {\tt esc} evaluates to true.

  To be replaced later by exception-handling mechanism.
  """
  from sys import exit, stderr
  stderr.write("ERROR: %s\n" % message)
  if esc:
    exit(1)

INFINITY = "INFINITY"

###############################################################################
# Extended min/max functions.
# Are capable of dealing with INFINITY
###############################################################################
def minEx(val1, val2):
  if val2 == INFINITY:
    return val1
  elif val1 == INFINITY:
    return val2
  elif val1 > val2:
    return val2
  else:
    return val1

def maxEx(val1, val2):
  if val1 == INFINITY:
    return val1
  elif val2 == INFINITY:
    return val2
  elif val1 > val2:
    return val1
  else:
    return val2

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
  
  ###
  def receive(self, aDEVS, msg):
    
    # For any received message, the time {\tt t} (time at which the message
    # is sent) is the second item in the list {\tt msg}.
    t = msg[2]
  
    # $(i,\,t)$ message --- sets origin of time at {\tt t}:
    if msg[0] == 0:
      aDEVS.timeLast = t - aDEVS.elapsed
      aDEVS.myTimeAdvance = aDEVS.timeAdvance()
      if aDEVS.myTimeAdvance != INFINITY: aDEVS.myTimeAdvance += t
  
    # $(*,\,t)$ message --- triggers internal transition and returns
    # $(y,\,t)$ message for parent coupled-DEVS:
    elif msg[0] == 1:
      #if t != aDEVS.timeNext:
      #  Error("Bad synchronization...1", 1)

      # First call the output function, which (amongst other things) rebuilds
      # the output dictionnary {\tt myOutput}:
      aDEVS.myOutput = {}
      aDEVS.outputFnc()
                
      # Call the internal transition function to update the DEVS' state, and
      # update time variables:
      prevState = aDEVS.state
# SB: added the following line to provide the internal transition with the elapsed time
      aDEVS.elapsed = t - aDEVS.timeLast
      aDEVS.state = aDEVS.intTransition()
      aDEVS.timeLast = t
      aDEVS.myTimeAdvance = aDEVS.timeAdvance()
      if aDEVS.myTimeAdvance != INFINITY: aDEVS.myTimeAdvance += t
      aDEVS.elapsed = 0.
      
      if __VERBOSE__:
        print "\n\tINTERNAL TRANSITION: %s" % (aDEVS.__class__.__name__)
        print "\t  New State: %s" % (aDEVS.state)
        Q = ""
        for e in aDEVS.Q: Q += e.name+" "
        print "\t  Event Q:", Q
        print "\t  Output Port Configuration:"
        for I in range(0, len(aDEVS.OPorts) ):
          if aDEVS.OPorts[I][0] in aDEVS.myOutput.keys():
            print "\t    %s: %s" % (aDEVS.OPorts[I][1], aDEVS.myOutput[aDEVS.OPorts[I][0]])
          else:
            print "\t    %s: None" % (aDEVS.OPorts[I][1])
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
      #if not(aDEVS.timeLast <= t <= aDEVS.timeNext):
      #  Error("Bad synchronization...2", 1)
      
      aDEVS.myInput = msg[0]
      # update elapsed time. This is necessary for the call to the external
      # transition function, which is used to update the DEVS' state.
      aDEVS.elapsed = t - aDEVS.timeLast
      prevState = aDEVS.state
      aDEVS.state = aDEVS.extTransition()
      # Udpate time variables:
      aDEVS.timeLast = t
      aDEVS.myTimeAdvance = aDEVS.timeAdvance()
      if aDEVS.myTimeAdvance != INFINITY: aDEVS.myTimeAdvance += t
      aDEVS.elapsed = 0
      
      if __VERBOSE__:
        print "\n\tEXTERNAL TRANSITION: %s" % (aDEVS.__class__.__name__)
        Q = ""
        for e in aDEVS.Q: Q += e.name+" "
        print "\t  Event Q:", Q
        print "\t  Input Port Configuration:"
        for I in range(0, len(aDEVS.IPorts)):
          print "\t    %s: %s" % (aDEVS.IPorts[I][1], aDEVS.peek(aDEVS.IPorts[I][0]))
        print "\t  New State: %s" % (aDEVS.state)
        if aDEVS.myTimeAdvance == INFINITY:
          print "\t  Next scheduled internal transition at INFINITY"
        else:
          print "\t  Next scheduled internal transition at %f" % aDEVS.myTimeAdvance
      
    else:
      Error("Unrecognized message", 1)

###############################################################################

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
    
    # $(i,\,t)$ message --- sets origin of time at {\tt t}:
    if msg[0] == 0:
      # Rebuild event-list and update time variables, by sending the
      # initialization message to all the children of the coupled-DEVS. Note
      # that the event-list is not sorted here, but only when the list of
      # {\sl imminent children\/} is needed. Also note that {\tt None} is
      # defined as bigger than any number in Python (stands for $+\infty$).
      cDEVS.timeLast = 0.
      cDEVS.myTimeAdvance = INFINITY
      #cDEVS.eventList = []
      for d in cDEVS.componentSet:
        self.send(d, msg)
        cDEVS.myTimeAdvance = minEx(cDEVS.myTimeAdvance, d.myTimeAdvance)
        cDEVS.timeLast = maxEx(cDEVS.timeLast, d.timeLast)

      # Get all the components which have tied for the smallest time advance
      # and put them into the coupled DEVS' immChildren list
      cDEVS.immChildren = []
      for d in cDEVS.componentSet:
        if cDEVS.myTimeAdvance == d.myTimeAdvance:
          cDEVS.immChildren.append(d)

    # $(*,\,t)$ message --- triggers internal transition and returns
    # $(y,\,t)$ message for parent coupled-DEVS:
    elif msg[0] == 1:
      #if t != cDEVS.timeNext:
      #  Error("Bad synchronization...3", 1)
        
      # Build the list {\tt immChildren} of {\sl imminent children\/} based
      # on the sorted event-list, and select the active-child {\tt dStar}. If
      # there are more than one imminent child, the coupled-DEVS {\tt select}
      # function is used to decide the active-child.
      
      if len(cDEVS.immChildren) == 1:
        dStar = cDEVS.immChildren[0]
      else:
        dStar = cDEVS.select(cDEVS.immChildren)
        if __VERBOSE__:
          print "\n\tCollision occured in %s, involving:" % (cDEVS.__class__.__name__)
          for I in cDEVS.immChildren:
            print "    \t   %s" % (I.__class__.__name__)
          print "\t  select chooses %s" % (dStar.__class__.__name__)
        
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
      cDEVS.myTimeAdvance = INFINITY
      for d in cDEVS.componentSet:
        X = {}
        for p,pname in d.IPorts:
          for pi in p.inLine:
            if pi in Y.keys():
              X[p] = deepcopy(Y[pi]) # only if atomic DEVS?
              break
        if X != {}:
          self.send(d, [X, cDEVS.immChildren, t])
        cDEVS.myTimeAdvance = minEx(cDEVS.myTimeAdvance, d.myTimeAdvance)
      
      # Get all components which tied for the smallest time advance and append
      # each to the coupled DEVS' immChildren list
      cDEVS.immChildren = []
      for d in cDEVS.componentSet:
        if cDEVS.myTimeAdvance == d.myTimeAdvance:
          cDEVS.immChildren.append(d)
        
      # Use same pattern as above to update coupled-DEVS output dictionnary
      # (once again using ports' {\tt inLine} attributes rather than
      # coupled-DEVS' {\tt EOC}). The DEVS' output is then returned to its
      # parent coupled-DEVS (rather than being sent).
      cDEVS.myOutput = {}
      for p,pname in cDEVS.OPorts:
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
      #if not(cDEVS.timeLast <= t <= cDEVS.timeNext):
      #  Error("Bad synchronization...4", 1)
      
      cDEVS.myInput = msg[0]

      # Send $(x,\,t)$ messages to those sub-DEVS influenced by the coupled-
      # DEVS input ports (ref. {\tt EIC}). This is essentially the same code
      # as above that also updates the coupled-DEVS' time variables in
      # parallel.
      cDEVS.timeLast = t
      cDEVS.myTimeAdvance = INFINITY
      for d in cDEVS.componentSet:
        X = {}
        for p,pname in d.IPorts:
          for pi in p.inLine:
            if pi in cDEVS.myInput.keys():
              X[p] = cDEVS.myInput[pi]
              break
        if X != {}:
          self.send(d, [X, cDEVS.immChildren, t])
        cDEVS.myTimeAdvance = minEx(cDEVS.myTimeAdvance, d.myTimeAdvance)

      # Get all components which tied for the smallest time advance and append
      # each to the coupled DEVS' immChildren list
      cDEVS.immChildren = []
      for d in cDEVS.componentSet:
        if cDEVS.myTimeAdvance == d.myTimeAdvance:
          cDEVS.immChildren.append(d)

    else:
      Error("Unrecognized message", 1)

###############################################################################

class Executor(AtomicSolver, CoupledSolver, Thread):
  """Associates a hierarchical DEVS model with the simulation engine.
  """
  
  ###
  def __init__(self, model, sync=None):
    """Constructor.
  
    {\tt model} is an instance of a valid hierarchical DEVS model. The
    constructor stores a local reference to this model and augments it with
    {\sl time variables\/} required by the simulator.
    """
    Thread.__init__(self)  
    self.model = model
    self.augment(self.model)
    if sync == None:
      from threading import Event
      self.sync = Event()
    else:
      self.sync = sync
    self.done = 0
  
  ###
  def augment(self, d):
    """Recusively augment model {\tt d} with {\sl time variables\/}.
    """
   
    # {\tt timeLast} holds the simulation time when the last event occured
    # within the given DEVS, and (\tt myTimeAdvance} holds the amount of time until
    # the next event.
    d.timeLast = d.myTimeAdvance = 0.
    if d.type() == 'COUPLED':
      # {\tt eventList} is the list of pairs $(tn_d,\,d)$, where $d$ is a
      # reference to a sub-model of the coupled-DEVS and $tn_d$ is $d$'s
      # time of next event.
      #d.eventList = []
      d.immChildren = []
      for subd in d.componentSet:
        self.augment(subd)
        
  ###
  def send(self, d, msg):
    """Dispatch messages to the right method.
    """
  
    if d.type() == 'COUPLED':
      return CoupledSolver.receive(self, d, msg)
    elif d.type() == 'ATOMIC':
      return AtomicSolver.receive(self, d, msg)

  ###
  def shutdown(self):
    self.done = 1
    self.sync.set()

  ###
  def run(self):
    """Simulate the model (Root-Coordinator).
    
    In this implementation, the simulation stops only when the simulation
    time (stored in {\tt clock}) reaches {\tt T} (starts at 0). Other means
    to stop the simulation ({\it e.g.}, when an atomic-DEVS enters a given
    state, or when a global variable reaches a predefined value) will be
    implemented.
    """
  
    # Initialize the model --- set the simulation clock to 0.
    self.send(self.model, (0, [], 0))
    self.model.extEvents = {}

    from time import time
#    initialRT = time()
    clockRT = 0.0

    # Main loop repeatedly sends $(*,\,t)$ messages to the model's root DEVS.
    while 1:
      # if the smallest time advance is infinity, wait forever
      # if the smallest time advance is x, then wait(x)
      # don't wait at all if the smallest time advance is 0
      ta = self.model.myTimeAdvance
      if ta == INFINITY:
        initial = time()
        self.sync.wait()
        elapsed = time() - initial
      elif ta-clockRT > 0:
        initial = time()
        self.sync.wait(ta - clockRT)
        elapsed = time() - initial
      else: elapsed = 0.0

      if ta == INFINITY or ta-clockRT > 0.0:
        if self.sync.isSet(): clockRT += elapsed # INTERRUPT
        else: clockRT += (ta-clockRT) # TIMEOUT

      self.sync.clear()
      if self.done:
        return

      # calculate how much time has passed so far
      if __VERBOSE__:
        print "\n", "* " * 10, "CLOCK (RT): %f" % clockRT

      # pass incoming external events to their respective ports from the GUI
      # if there are no external events then we must do an internal transition
      immChildren = self.model.immChildren
      external = 0
      for inport,inport_name in self.model.IPorts:
        for sourceport in inport.inLine:
          if len(sourceport.host.myOutput) != 0:
            external = 1
            for e in sourceport.host.myOutput.values():
              self.send(self.model, [{inport:e}, immChildren, clockRT])
            sourceport.host.myOutput.clear()
      if not external:
        self.send(self.model, (1, immChildren, clockRT))
      
###############################################################################
# EVENT/STATE FRAMEWORK
#
# These classes represent Events and States as parameterizable entities.
# Both DEVSState and DEVSEvent have a param attribute which is a dictionary
# and is used to parameterize the state or event.
###############################################################################

class Parameterizable:
	def __init__(self, name, params):
		self.name = name
		self.params = {}
		for name,value in params:
			self.params[name] = value
	def __str__(self):
		return self.name
	def __cmp__(self, other):
		return self.name != other
	def get_param(self, name):
		try:
			value = self.params[name]
		except:
			value = None
		return value
	def set_param(self, name, value):
		self.params[name] = value

class DEVSstate(Parameterizable):
	def __init__(self, name, params=[]):
		Parameterizable.__init__(self, name, params)

class DEVSevent(Parameterizable):
	def __init__(self, name, params=[]):
		Parameterizable.__init__(self, name, params)

class EVENT(DEVSevent): pass
class STATE(DEVSstate): pass

###############################################################################
# Pluggable class
#
# Defines an interface for ports so that other objects
# can plug into it to send and receive events.
###############################################################################
class Pluggable:
	def __init__(self):
		self.IPorts = []
		self.OPorts = []
		self.myOutput = {}
		self.myInput = {}

	def addInPort(self, name=None):
		port = Port(1)
		port.host = self
		self.IPorts.append((port,name))
		return port

	def recv(self, event):
		pass

	def send(self, event):
		self.recv(event)

	def addOutPort(self, name=None):
		port = Port(0)
		port.host = self
		self.OPorts.append((port,name))
		return port

	def poke(self, p, v):
		if p.type() != 'OUTPORT':
			Error("Not an output port", 0)
		elif p in self.myOutput.keys():
			Error("There is already a value on this port", 0)
		else:
			if isinstance(v, DEVSevent):
				event = v
				event.set_param("address", [])
			else: event = DEVSevent(str(v), [("address", [])])
			event.set_param("broadcast", "TRUE")
			self.myOutput[p] = v

###############################################################################
# DEVS_GUI_APP class
#
# Basically a connectPorts method which allows the programmer to pass
# messages along ports from the GUI to the DEVS engine.
###############################################################################
#class DEVS_GUI_APP:

def connectPorts(p1, p2):
  if p1.type() == 'OUTPORT' and p2.type() == 'INPORT':
    p1.outLine.append(p2)
    p2.inLine.append(p1)
  elif p1.type() == 'INPORT' and p2.type() == 'OUTPORT':
    p1.inLine.append(p2)
    p2.outLine.append(p1)
  else:
    Error("Illegal coupling!", 0)

###############################################################################
# DEVS_GUI class
#
# This class defines an interface which allows a GUI application to communicate
# with a RT_DEVS engine.
###############################################################################
from Tkinter import Frame
class DEVS_GUI(Pluggable, Frame, Thread):
	def __init__(self, sync, master=None):
		Frame.__init__(self, master)
		Thread.__init__(self)
		Pluggable.__init__(self)
		self.sync = sync
		self.parent = None

	def run(self):
		self.mainloop()

	def poke(self, p, v):
		Pluggable.poke(self, p, v)
		self.sync.set()


###
class Generator(Thread):
	def __init__(self, sync):
		Thread.__init__(self)
		self.sync = sync
		self.IPorts = []
		self.OPorts = []
		self.myOutput = {}
		self.myInput = {}

	def addOutPort(self, name=None):
		port = Port(0)
		port.host = self
		self.OPorts.append((port,name))
		return port

	def addInPort(self, name=None):
		port = Port(1)
		port.host = self
		self.IPorts.append((port,name))
		return port

	def recv(self, event): # OVERRIDE
		pass

	def send(self, event):
		self.recv(event)

	def poke(self, p, v):
		if p.type() != 'OUTPORT':
			Error("Not an output port", 0)
		elif p in self.myOutput.keys():
			Error("There is already a value on this port", 0)
		else:
			if isinstance(v, DEVSevent):
				event = v
				event.set_param("address", [])
			else: event = DEVSevent(str(v), [("address", [])])
			event.set_param("broadcast", "TRUE")
			self.myOutput[p] = v
		self.sync.set()

###############################################################################
# CLASS HIERARCHY
###############################################################################

class BaseDEVS:
  """Virtual base class for {\tt AtomicDEVS} and {\tt CoupledDEVS} classes.
  
  This class provides basic DEVS attributes and information methods.
  """
  
  ###
  def __init__(self):
    """Constructor.
    """
    
    # Following {\tt if}-clause prevents any attempt to instantiate this
    # class or one of its two direct subclasses.
    if self.__class__ in (BaseDEVS, AtomicDEVS, CoupledDEVS):
      Error ("Cannot instantiate '%s' class..." % (self.__class__.__name__), 0)
    
    # {\sl General DEVS Attributes\/} --- related to atomic- and coupled-DEVS'
    # implementation:
    #
    # * {\tt __doc__} is the (optional) {\sl standard documentation string},
    #   whose content is left to the modeler's hand (undeclared here, as
    #   it is a default class attribute in Python);
    # * {\tt parent} is a {\sl reference to the parent coupled-DEVS\/} in the
    #   hierarchical representation of the model. Declared here only for
    #   reference, as the default value gets overwritten when a DEVS is being
    #   added to a model using {\tt CoupledDEVS}'s {\tt addSubModel} method
    #   (remains {\tt None} for a root-DEVS);
    # * {\tt myID} is a {\sl unique identification string\/}, which consists
    #   of the 'type' letter '{\tt A}' or '{\tt C}' (Atomic or Coupled DEVS),
    #   followed by the 'index' of the object (the number of objects {\sl of
    #   the same type\/} that will have been instantiated after the present
    #   one, {\it i.e.}, $\hbox{index}\in [1,\,+\infty[$\/). Once again
    #   declared only for reference, as the default value gets overwritten
    #   when a descriptive class is being instantiated;
    # * {\tt condFlag} is the {\sl condition flag\/}, indicating whether the
    #   DEVS is {\sl active\/} (by default) or {\sl idle\/} --- 1 or 0,
    #   respectively (for future use).
    self.parent = None
    self.myID   = None
    self.condFlag = 1
    
    # {\sl Specific Attributes\/} --- related to atomic- and coupled-DEVS'
    # specification:
    # * {\tt IPorts} and {\tt OPorts} are lists of references to the DEVS'
    #   input and output ports;
    # * {\tt myInput} and {\tt myOutput} are the input and output dictionnaries,
    #   each of the form $\{${\sl port_reference : message_on_port\/}$\}$.
    #   Messages are sent/retrieved using the {\tt poke} and {\tt peek} methods,
    #   and the actual message 'delivery' from a DEVS to another is left to the
    #   simulator (why? the actual port configuration depends on time - ref.
    #   idle ports. To be completed);
    self.IPorts  = [];  self.OPorts   = []
    self.myInput = {};  self.myOutput = {}
    
  ###
  def type(self):
    """Returns the 'type' of the object: {\tt 'ATOMIC'} or {\tt 'COUPLED'}.
    """
    if self.myID[0] == 'A':
      return 'ATOMIC'
    elif self.myID[0] == 'C':
      return 'COUPLED'
    # Else, invalid type:
    return None
      
  ###
  def addInPort(self, name=None):
    """Add an {\sl input port\/} to the DEVS model.
    
    {\tt addInPort} and {\tt addOutPort} are the {\sl only\/} proper way to
    add I/O ports to DEVS. As for {\tt CoupledDEVS.addSubModel} method, calls
    to {\tt addInPort} and {\tt addOutPort} can appear in any DEVS'
    descriptive class constructor, or the methods can be used with an
    instantitated object.
    
    The methods add a reference to the new port in the DEVS {\tt IPorts} or
    {\tt OPorts} attributes and set the port's {\tt host} attribute. The
    modeler should typically add the returned reference the local dictionnary.    
    """

    # Instantiate an input port:
    port = Port(1) 
    
    self.IPorts.append((port,name))
    port.host = self
    return port
      
  ###
  def addOutPort(self, name=None):
    """Add an {\sl output port\/} to the DEVS model.
    
    See comments for {\tt addInPort} above.
    """

    # Instantiate an output port:
    port = Port(0)
        
    self.OPorts.append((port,name))
    port.host = self        
    return port  
    
###############################################################################

class AtomicDEVS(BaseDEVS):
  """Virtual base class for all atomic-DEVS descriptive classes.
    
  An atomic-DEVS is described as a structure... (to be completed)
  """
  
  # {\tt AtomicIDCounter} is a static counter used for the 'index' part of
  # atomic-DEVS' {\tt myID} attribute. Incremented with every instantiation
  # of an atomic-DEVS' descriptive class, unaffected by the deletion of those
  # classes.
  AtomicIDCounter = 0
  
  ###  
  def __init__(self):
    """Constructor.
    """

    # The minimal constructor shall {\sl first\/} call the superclass
    # ({\it i.e.}, {\tt BaseDEVS}') constructor.
    BaseDEVS.__init__(self)
    
    # Increment {\tt AtomicIDCounter\/} and setup instance's {\tt myID\/}
    # attribute.
    AtomicDEVS.AtomicIDCounter = AtomicDEVS.AtomicIDCounter + 1
    self.myID = "A%d" % AtomicDEVS.AtomicIDCounter
    
    # {\sl Specific Attributes\/} --- related to atomic-DEVS' specification:
    # (to be completed)
    self.elapsed = 0.
    self.state = None

  ###
  def poke(self, p, v):
    """Outputs message {\tt v} to output port {\tt p}.
    
    This merely amounts to adding a new entry into dictionnary
    {\tt myOutput}. Note that the dictionnary must be cleared before poking
    any port. This is the simulator's responsability.
    """

    if p.type() != 'OUTPORT':
      Error("Not an output port", 0)
    elif p in self.myOutput.keys():
      Error("There is already a value on this port", 0)
    elif p.host != self:
      Error("Port doesn't belong to this DEVS", 0)    
    else:
      self.myOutput[p] = v
    
  ###
  def peek(self, p):
    """Retrives message from input port {\tt p}.
    """
    
    v = None
    if p.type() != 'INPORT':
      Error("Not an input port", 0)
    # The following is a redundant check (in {\tt peek}'s case only):
    elif p.host != self:
      Error("Port doesn't belong to this DEVS", 0)    
    elif p in self.myInput.keys():
      v = self.myInput[p]
      
    return v
  
  ###    
  def extTransition(self):
    """DEFAULT External Transition Function.
  
    Accesses {\tt state} and {\tt elapsed} attributes, as well as inputs
    through {\tt peek} method. Returns the new state.
    """
    return self.state
    
  ###    
  def intTransition(self):
    """DEFAULT Internal Transition Function.
  
    Accesses only {\tt state} attribute. Returns the new state.
    """
    return self.state
  
  ###    
  def outputFnc(self):
    """DEFAULT Output Function.
  
    Accesses only {\tt state} attribute. Modify the output ports by means of
    the {\tt poke} method. Returns Nothing.
    """
    pass
  
  ###    
  def timeAdvance(self):
    """DEFAULT Time Advance Function.
  
    Accesses only {\tt state} attribute. Returns a real number in
    $[0, +\infty]$.
    """
    # 1000. stands for infinity (to be replaced by ``NaN'' if possible)
    return 10000.
    
###############################################################################

class CoupledDEVS(BaseDEVS):
  """Virtual base class for all coupled-DEVS descriptive classes.
    
  A coupled-DEVS is described as a structure... (to be completed. Note that
  {\tt self} in coupled-DEVS definition not to be mistaken with Python's
  {\tt self})
  """
  
  # {\tt CoupledIDCounter}: See comment for {\tt AtomicIDCounter} above.
  CoupledIDCounter = 0
  
  ###  
  def __init__(self):
    """Constructor.
    """

    # The minimal constructor shall {\sl first\/} call the superclass
    # ({\it i.e.}, {\tt BaseDEVS}') constructor.
    BaseDEVS.__init__(self)
    
    # Increment {\tt CoupledIDCounter\/} and setup instance's {\tt myID\/}
    # attribute.
    CoupledDEVS.CoupledIDCounter = CoupledDEVS.CoupledIDCounter + 1
    self.myID = "C%d" % CoupledDEVS.CoupledIDCounter

    # {\sl Specific Attributes\/} --- related to coupled-DEVS'
    # specification: (to be completed)
    self.componentSet = []
    
    # {\tt IC}, {\tt EIC} and {\tt EOC} describe the couplings at the
    # coupled-DEVS level (respectively, {\sl internal couplings}, {\sl
    # external input couplings\/} and {\sl external output couplings\/}).
    # Each coupling in the sets are pairs of pairs referencing the component
    # and the port the coupling is beginning and the component and the port
    # the coupling is ending.
    # Note that although consistent with Zeigler's definition, these sets
    # are not used by the simulator, which relies on ports' {\tt inLine} and
    # {\tt outLine} attributes to detect couplings.
    self.IC  = []
    self.EIC = []
    self.EOC = []

  ###      
  def addSubModel(self, model):
    """Make {\tt model} a child of the coupled-DEVS (in the hierarchical
    representation of the model).
    
    This is the {\sl only\/} proper way to build a hierarchical model. Calls
    to {\tt addSubModel} can appear in coupled-DEVS' descriptive classes'
    constructors, or the method can be used later to modify an existing
    object. {\tt model} is an instance of an atomic- or coupled-DEVS'
    descriptive class.
    
    (to be completed: already instantiated in global space [can then be
    a whole model---one should then be careful multiple occurences of the
    same object] or instantiated when method is called [can then lead to
    recursion---one should be careful to avoid recursive definitions] )
    
    The method adds a reference to the sub-model in its parent's {\sl
    components set} $\{M_d\,\mid\,d\in{\cal D}\}$ and sets the sub-model's
    {\tt parent} attribute. The set of {\sl component references\/} $\cal D$
    is implicitly defined provided the modeler adds the returned reference
    the local dictionnary.
    """
    self.componentSet.append(model)    
    model.parent = self
    return model
    
  ###
  def connectPorts(self, p1, p2):
    """Connects two ports together. The coupling is to begin at {\tt p1} and
    to end at {\tt p2}.
    
    NOTE: connections should eventually be implemented as objects, which
    would allow to specify an input-output transformation.
    """

    # For a coupling to be valid, two requirements must be met:
    # 1- at least one of the DEVS the ports belong to is a child of the
    #    coupled-DEVS ({\it i.e.}, {\tt self}), while the other is either the
    #    coupled-DEVS itself or {\sl another\/} of its children. The DEVS'
    #   'parenthood relationship' uniquely determine the type of coupling;
    # 2- the types of the ports are consistent with the 'parenthood' of the
    #    associated DEVS. This validates the coupling determined above.
    
    # {\sl Internal Coupling\/}:
    if ((p1.host.parent == self and p2.host.parent == self) and
        (p1.type() == 'OUTPORT' and p2.type() == 'INPORT')):
      if p1.host == p2.host:
        Error('Direct feedback coupling not allowed', 0)
      else:
        self.IC.append( ( (p1.host, p1), (p2.host, p2) ) )
        p1.outLine.append(p2)
        p2.inLine.append(p1)
    
    # {\sl external input couplings\/}:
    elif ((p1.host == self and p2.host.parent == self) and
	    (p1.type() == p2.type() == 'INPORT')):
        self.EIC.append( ( (p1.host, p1), (p2.host, p2) ) )
        p1.outLine.append(p2)
        p2.inLine.append(p1)
    
    # {\sl external output couplings\/}:
    elif ((p1.host.parent == self and p2.host == self) and
	        (p1.type() == p2.type() == 'OUTPORT')):
        self.EOC.append( ( (p1.host, p1), (p2.host, p2) ) )
        p1.outLine.append(p2)
        p2.inLine.append(p1)

    # Other cases (illegal coupling):
    else:
      Error("Illegal coupling (3)! " + str(p1) + " " + str(p2), 0)
      
  ###    
  def select(self, immList):
    """DEFAULT Select Function.
  
    Take as a parameter a list of imminent children (DEVS) lexicographically
    sorted according to their {\tt myID} attribute. Returns an item from that
    list.
    """
    return immList[0]

###############################################################################
# PORT CLASS
###############################################################################

class Port:
  """Class for ports, both inputs and outputs.
  
  This class provides basic ports attributes and information methods.
  """

  # {\tt InCounter} and {\tt OutCounter} are static counters used for the
  # 'index' part of input and output ports {\tt myID} attribute. Incremented
  # with every instantiation of input or output port, unaffected by the
  # deletion of those ports (deletion not implemented yet).
  InCounter = 0; OutCounter = 0

  ###
  def __init__(self, t):
    """Constructor. Creates an input port if {\tt t} evaluates to true, and
    an output port otherwise.
    """
    
    # {\sl Port Attributes\/} (to be completed):
    # * {\tt inLine} and {\tt outLine} represent an alternative way to
    #   describe couplings (and the one actually used by the simulator). The
    #   former is a list of references to the (possibly many) ports from
    #   which {\sl this\/} port receives its messages, while the latter is a
    #   list of references to the (possibly many) ports which receive
    #   messages from {\sl this\/} port. (Note that no more than one message
    #   received at a time: to be completed) While an atomic-DEVS output
    #   port (input port) would only need to declare {\tt outLine}
    #   ({\tt inLine}), the dual nature of coupled-DEVS ports require both
    #   attributes;
    # * {\tt myID} (set below);
    # * {\tt host} (to be completed);
    self.inLine = []; self.outLine = []
    self.host = None 
    
    # Increment {\tt InCounter\/} or {\tt OutCounter\/} depending on type of
    # port desired, and setup instance's {\tt myID\/} attribute:
    if t:
      Port.InCounter = Port.InCounter + 1
      self.myID = "IN%d" % Port.InCounter
    else:
	  Port.OutCounter = Port.OutCounter + 1
	  self.myID = "OUT%d" % Port.OutCounter
        
  ###  
  def type(self):
    """Returns the 'type' of the object: {\tt 'INPORT'} or {\tt 'OUTPORT'}.
    """
    if self.myID[:2] == 'IN':
      return 'INPORT'
    elif self.myID[:3] == 'OUT':
      return 'OUTPORT'
    # Else, invalid type:
    return None
