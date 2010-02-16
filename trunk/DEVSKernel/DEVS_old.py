# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DEVS.py --- Class and Tools for 'Classic' DEVS Model Specification
#                     --------------------------------
#                            Copyright (c) 2000
#                          Jean-Sébastien  BOLDUC
#                             Hans  Vangheluwe
#                       McGill University (Montréal)
#                     --------------------------------
# Version 1.0                                        last modified: 01/11/01
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# Atomic- and coupled-DEVS specifications adapted from:
#       B.P.Zeigler, ''Theory of modeling and simulation: Integrating
#       Discrete Event and Continuous Complex Dynamic Systems '',
#       Academic Press, 2000
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

##  GLOBAL VARIABLES AND FUNCTIONS
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

def Error(message = '', esc = 1):
  """	Error-handling function: reports an error and exits interpreter if
  		{\tt esc} evaluates to true.

  		To be replaced later by exception-handling mechanism.
  """
  from sys import exit, stderr
  stderr.write("ERROR: %s\n" % message)
  if esc:
    exit(1)

# {\sl Infinity macro\/} set when {\tt __INFINITY__} switch evaluates to true.
__INFINITY__ = 1000000

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##  CLASS HIERARCHY
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class BaseDEVS:
  """Virtual base class for {\tt AtomicDEVS} and {\tt CoupledDEVS} classes.

       This class provides basic DEVS attributes and information methods.
  """

  ###
  def __init__(self):
    ''' Constructor.
    '''
    # Following {\tt if}-clause prevents any attempt to instantiate this
    # class or one of its two direct subclasses.
    if self.__class__ in (BaseDEVS, AtomicDEVS, CoupledDEVS):
      Error ("Cannot instantiate '%s' class..." % (self.__class__.__name__), 1)

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
    return None

  ###
  def addInPort(self):
    """Add an {\sl input port\/} to the DEVS model.

    {\tt addInPort} and {\tt addOutPort} are the {\sl only\/} proper way to
    add I/O ports to DEVS. As for {\tt CoupledDEVS.addSubModel} method, calls
    to {\tt addInPort} and {\tt addOutPort} can appear in any DEVS'
    descriptive class constructor, or the methods can be used with an
    instantitated object.

    The methods add a reference to the new port in the DEVS {\tt IPorts} or
    {\tt OPorts} attributes and set the port's {\tt hostDEVS} attribute. The
    modeler should typically add the returned reference the local dictionnary.
    """
    port = Port(1)

    self.IPorts.append(port)
    port.hostDEVS = self

    return port

  ###
  def addOutPort(self):
    """Add an {\sl output port\/} to the DEVS model.

    See comments for {\tt addInPort} above.
    """

    port = Port(0)

    self.OPorts.append(port)
    port.hostDEVS = self
    return port
  
  ###
  def delOutPort(self, port):
    """Delete an {\sl output port\/} from the DEVS model.

    See comments for {\tt addInPort} above.
    """
	
    self.OPorts.remove(port)
	
  ###
  def delInPort(self, port):
    """Delete an {\sl input port\/} from the DEVS model.

    See comments for {\tt addInPort} above.
    """
	
    self.IPorts.remove(port)
	
  ###
  def delAllInPort(self):
    """Delete all {\sl input ports\/} from the DEVS model.

    See comments for {\tt addInPort} above.
    """
	
    self.IPorts=[]
  ###
  def delAllOutPort(self):
    """Delete all {\sl output ports\/} from the DEVS model.

    See comments for {\tt addInPort} above.
    """
	
    self.OPorts=[]
#    ===================================================================    #

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
    AtomicDEVS.AtomicIDCounter += 1
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
      Error("Not an output port", 1)
    elif p in self.myOutput.keys():
      Error("There is already a value on this port "+p.hostDEVS.myID+ ' ' + str(v) + '\n' + `str(p)`, 1)
    elif p.hostDEVS != self:
      Error("Port doesn't belong to this DEVS", 1)
    else:
      self.myOutput[p] = v

  ###
  def peek(self, p):
    """Retrives message from input port {\tt p}.
    """

    v = None
    if p.type() != 'INPORT':
      Error("Not an input port", 1)
	# The following is a redundant check (in {\tt peek}'s case only):
    elif p.hostDEVS != self:
      Error("Port doesn't belong to this DEVS", 1)
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
    # 100000. stands for infinity (to be replaced by ``NaN'' if possible)
    return __INFINITY__

  ###
  def __str__(self):
  	return self.myID

#    ===================================================================    #

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
    CoupledDEVS.CoupledIDCounter += 1
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
    if ((p1.hostDEVS.parent == self and p2.hostDEVS.parent == self) and (p1.type() is 'OUTPORT' and p2.type() is 'INPORT')):
      if p1.hostDEVS == p2.hostDEVS:
        Error('Direct feedback coupling not allowed', 1)
      else:
        self.IC.append( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
        p1.outLine.append(p2)
        p2.inLine.append(p1)

    # {\sl external input couplings\/}:
    elif ((p1.hostDEVS == self and p2.hostDEVS.parent == self) and (p1.type() == p2.type() == 'INPORT')):
        self.EIC.append( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
        p1.outLine.append(p2)
        p2.inLine.append(p1)

    # {\sl external output couplings\/}:
    elif ((p1.hostDEVS.parent == self and p2.hostDEVS == self) and (p1.type() == p2.type() == 'OUTPORT')):
        self.EOC.append( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
        p1.outLine.append(p2)
        p2.inLine.append(p1)

#     elif not __WITH_COORDINATOR__ and \
#        	((p1.hostDEVS.parent != self or p2.hostDEVS.parent != self) and (p1.type() is 'OUTPORT' and p2.type() is 'INPORT')):
#         if p2.hostDEVS.type() is 'COUPLED':
#            for p in p2.outLine:
#               self.IC.append( ( (p1.hostDEVS, p1), (p.hostDEVS, p) ) )
#                p1.outLine.append(p)
#                p.inLine.append(p1)
#         else:
#            for p in p1.inLine:
#               self.IC.append( ( (p.hostDEVS, p), (p2.hostDEVS, p2) ) )
#               p.outLine.append(p2)
#               p2.inLine.append(p)
    # Other cases (illegal coupling):
    else:
        print str(p1), str(p2), self.__str__()
        Error("Illegal coupling!", 1)

  ####
  #def disconnectPorts(self, p1, p2):
    ##p1.outLine.remove(p2)
    ##p2.inLine.remove(p1)
    
    #if ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) in self.IC:
        #self.IC.remove(( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ))
    #elif ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) in self.EOC:
        #self.EOC.remove(( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ))
    #elif ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) in self.EIC:
        #self.EIC.remove(( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ))

  ###
  def select(self, immList):
    """DEFAULT Select Function.

    Take as a parameter a list of imminent children (DEVS) lexicographically
    sorted according to their {\tt myID} attribute. Returns an item from that
    list.
    """
    return immList[0]

  ##
  def __str__(self):
  	''' Printer fonction
	'''
  	return self.myID

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##  PORT CLASS
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

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
    # * {\tt hostDEVS} (to be completed);

    self.inLine = []; self.outLine = []
    self.hostDEVS = None

    # Increment {\tt InCounter\/} or {\tt OutCounter\/} depending on type of
    # port desired, and setup instance's {\tt myID\/} attribute:
    if t:
      Port.InCounter +=  1
      self.myID = "IN%d" % Port.InCounter
    else:
	  Port.OutCounter += 1
	  self.myID = "OUT%d" % Port.OutCounter

  ###
  def type(self):
    """Returns the 'type' of the object: {\tt 'INPORT'} or {\tt 'OUTPORT'}.
    """
    if self.myID[:2] == 'IN':
      return 'INPORT'
    elif self.myID[:3] == 'OUT':
      return 'OUTPORT'

    return None

  ###
  def __str__(self):
  	''' Printer function
	'''
  	return self.myID
