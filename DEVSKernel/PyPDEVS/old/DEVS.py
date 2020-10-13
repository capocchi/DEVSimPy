# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DEVS.py --- Classes and Tools for DEVS Model Specification
#                     --------------------------------
#                            Copyright (c) 2013
#                          Jean-S�bastien  BOLDUC
#                             Hans  Vangheluwe
#                            Yentl Van Tendeloo
#                       McGill University (Montr�al)
#                     --------------------------------
# Version 1.0                                        last modified: 01/11/01
# Version 1.0.1                                      last modified: 04/04/05
#  - The default "AtomicDEVS.timeAdvance" method returns
#    the object "INFINITY" which stands for infinity
#  - Deal with DeprecationWarning
# Version 1.0.3                                      last modified: 16/11/05
#  - Use True/False instead of 1/0
#  - Cleanup of terminology
# Version 1.1                                        last modified: 21/11/12
#  - Various optimisations for increased simulation speed
# Version 2.0                                        last modified: 05/03/13
#  - Support distributed and parallel simulation
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# Atomic- and coupled-DEVS specifications adapted from:
#       B.P.Zeigler, H. Praehofer, and Tag Gon Kim,
#       ``Theory of modeling and simulation: Integrating
#       Discrete Event and Continuous Complex Dynamic Systems '',
#       Academic Press, 2000
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

##  GLOBAL VARIABLES AND FUNCTIONS
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from .logger import *
from .util import *
#cython from message cimport NetworkMessage, Message
from .message import NetworkMessage, Message #cython-remove

##  CLASS HIERARCHY
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

IDCounter = 0
PortCounter = 0

class BaseDEVS(object):
    """
    Abstract base class for AtomicDEVS and CoupledDEVS classes.

    This class provides basic DEVS attributes and query/set methods.
    """
    ###
    def __init__(self, name):
        """
        Constructor
        Args:
            name - the name of the DEVS model
        """

        # Prevent any attempt to instantiate this abstract class
        if self.__class__ == BaseDEVS:
            raise DEVSException ("Cannot instantiate abstract class '%s' ... "
                                 % (self.__class__.__name__))

        # The parent of the current model
        self.parent = None
        # The ID of the model
        self.myID   = None
        # The local name of the model
        self.name = name
        # List of all input ports
        self.IPorts  = []
        # List of all output ports
        self.OPorts   = []

        # Initialise the times
        self.timeLast = (0.0, 0)
        self.timeNext = (0.0, 1)

        self.location = None
        self.rootsim = None

        # Variables used for optimisations
        self.fullName = self.name
        self.myInput = {}
        self.myOutput = {}
        self.model_ids = {}

        global IDCounter
        self.model_id = IDCounter
        IDCounter += 1

        # The state queue, used for time warp
        self.oldStates = []

        # Remappers to map ports to numbers (and backwards)
        # needed to allow passing ports over the network
        self.remapNum2Port = {}
        self.remapPort2Num = {}

    def setGVT(self, GVT):
        """
        Set the GVT of this model, nothing should happen by default
        Args:
            GVT - the GVT that must be set
        """
        pass

    def announceSim(self):
        if getProxy(self.rootsim.controller_name).announceSim(
                    self.rootsim.name):
            #print("OK for " + str(self.rootsim.name))
            return None
        else:
            #print("Fail for " + str(self.rootsim.name))
            raise NestingException("A nested simulation at this level has " +
                                   "already been started, this exception " +
                                   "should not be catched in user-code but " +
                                   "should be passed back to the simulator.")

    def announceEnd(self):
        getProxy(self.rootsim.controller_name).announceEnd(self.rootsim.name)

    def setData(self):
        """
        Set the data of this model, nothing should happen by default
        """
        pass

    def setRootSim(self, rsim, name):
        """
        Set the rootsim and location of the current model
        Args:
            rsim - the rootsim of this model
            name - the name of the server at which this model is located
        """
        self.rootsim = rsim
        self.location = name

    def send(self, msg):
        """
        Send a message to this model
        Args:
            msg - the message to be sent
        """
        return self.rootsim.send(self.model_id, msg)

    def getModelIDs(self):
        """
        Get the ID of all models registered at this model
        """
        return self.model_ids

    def getVCDVariables(self):
        """
        Returns all the variables, suitable for VCD variable generation
        """
        varList = []
        for I in self.OPorts:
            varList.append([self.getModelFullName(), I.getPortName()])
        for I in self.IPorts:
            varList.append([self.getModelFullName(), I.getPortName()])
        return varList

    def getPortByName(self, name):
        for i in self.IPorts:
            if i.getPortName() == name:
                return i
        for i in self.OPorts:
            if i.getPortName() == name:
                return i

    def addInPort(self, name=None):
        """
        Add an input port to the DEVS model.

        addInPort and addOutPort are the only proper way to
        add I/O ports to DEVS. As for the CoupledDEVS.addSubModel method, calls
        to addInPort and addOutPort can appear in any DEVS'
        descriptive class constructor, or the methods can be used with an
        instantiated object.

        The methods add a reference to the new port in the DEVS' IPorts or
        OPorts attributes and set the port's hostDEVS attribute. The modeler
        should typically add the returned reference the local dictionary
        (to be able to refer to the port for peek/poke-ing later).
        Args:
            name - the name of the port, this name should be unique to the
                   model if None is provided, a unique ID will be generated
        """
        # Instantiate an input port:
        port = Port(isInput=True, name=name)

        self.IPorts.append(port)
        port.hostDEVS = self
        return port

    def addOutPort(self, name=None):
        """Add an output port to the DEVS model.

        See comments for addInPort above.
        Args:
            name - the name of the port, this name should be unique to the
                   model if None is provided, a unique ID will be generated
        """

        # Instantiate an output port:
        port = Port(isInput=False, name=name)

        self.OPorts.append(port)
        port.hostDEVS = self
        return port

    def getModelName(self):
        """
        Get the local model name
        """
        if self.name is None:
            return str(self.myID)
        else:
            return str(self.name)

    def getModelFullName(self):
        """
        Get the full model name, including the path from the root
        """
        return self.fullName

class AtomicDEVS(BaseDEVS):
    """
    Abstract base class for all atomic-DEVS descriptive classes.
    """

    def __init__(self, name=None):
        """Constructor.
        """
        # Prevent any attempt to instantiate this abstract class
        if self.__class__ == AtomicDEVS:
            raise DEVSException("Cannot instantiate abstract class '%s' ... "
                                % (self.__class__.__name__))

        # The minimal constructor shall first call the superclass
        # (i.e., BaseDEVS) constructor.
        BaseDEVS.__init__(self, name)

        # Increment AtomicIDCounter and setup instance's myID
        # attribute.
        self.myID = "A%d" % self.model_id

        self.elapsed = 0.0
        self.state = None

        # Used for optimisations
        self.peek_ok = {}
        self.statesavecounter = 0

    ###
    def getLocationList(self, cset):
        cset.add(self.rootsim.name)
        return cset

    def fixHierarchy(self, location, parentname):
        """
        Fix the hierarchy of the current model
        Args:
            location - the location of the current model
        """
        if parentname != "":
            print(parentname, self.name)
            self.fullName = parentname + "." + self.name
        else:
            self.fullName = self.name
        if self.parent is not None:
            self.parent.name = parentname
        self.location = location

    def setGVT(self, GVT):
        """
        Set the GVT of the model, cleaning up the states vector as required
        for the time warp algorithm
        Args:
            GVT - the new value of the GVT
        """
        copy = None
        for i in range(len(self.oldStates)):
            state = self.oldStates[i]
            if state[0][0] >= GVT:
                copy = i-1
                break
        if self.oldStates == []:
            pass
        elif copy is None:
            self.oldStates = [self.oldStates[-1]]
        else:
            self.oldStates = self.oldStates[copy:]

    def printModel(self, indent=0):
        print(('\t'*indent + "Atomic " + str(self.getModelFullName())))
        for i in self.OPorts:
            print(('\t'*(indent+1) + "OPort " + str(i.getPortFullName())))
            for j in i.outLine:
                print(('\t'*(indent+2) + str(j.hostDEVS.getModelFullName())))

    def revert(self, time):
        """
        Revert the model to the specified time. All necessary cleanup for this
        model will be done (fossil collection).
        Args:
            time - the time up to which should be reverted
        """
        if self.rootsim.GVT > time[0]:
            raise DEVSException("Reverting to time (%f) before the GVT (%f)!"
                                % (time, self.rootsim.GVT))
        counter = 0
        newstate = None
        #NOTE maybe we can use binary search, though the changes are higher that the last states are required
        for memindex in range(len(self.oldStates) - 1, -1, -1):
            mem = self.oldStates[memindex]
            timelast = mem[0]
            if timelast < time:
                newstate = memindex
                counter = newstate + 1
                break

        if newstate is None:
            # TODO this situation should never happen, though it is sometimes possible for a message to
            #  lag during processing, this is just a temporary (and not 100% correct) fix
            newstate = 0

        if newstate is not None:
            self.timeLast = self.oldStates[newstate][0]
            self.timeNext = self.oldStates[newstate][1]

            self.state = self.rootsim.loadstate(self.oldStates[newstate][2])
            self.oldStates = self.oldStates[:counter]

            if self.parent is not None:
                self.rootsim.model.childRevert(self)
        # NOTE clearing the myInput happens in the parent

    def extTransition(self, inputs): # pragma: no cover
        """
        DEFAULT External Transition Function.

        Accesses state and elapsed attributes, as well as inputs
        through peek method. Returns the new state.
        """
        return self.state

    def intTransition(self): # pragma: no cover
        """
        DEFAULT Internal Transition Function.

        Accesses only state attribute. Returns the new state.
        """
        return self.state

    def confTransition(self, inputs): # pragma: no cover
        """
        DEFAULT Confluent Transition Function.

        Accesses state and elapsed attributes, as well as inputs
        through peek method. Returns the new state.
        """
        self.state = self.intTransition()
        self.state = self.extTransition(inputs)
        return self.state

    def outputFnc(self): # pragma: no cover
        """
        DEFAULT Output Function.

        Accesses only state attribute.
        Returns the output on the different ports.
        """
        return {}

    def timeAdvance(self): # pragma: no cover
        """
        DEFAULT Time Advance Function.

        Accesses only the state attribute. Returns a real number in
        [0, INFINITY].
        """
        # By default, return infinity
        return float('inf')

class CoupledDEVS(BaseDEVS):
    """
    Abstract base class for all coupled-DEVS descriptive classes.
    """

    def __init__(self, name=None):
        """
        Constructor.
        Args:
            name - the name of the coupled model
        """

        # Prevent any attempt to instantiate this abstract class
        if self.__class__ == CoupledDEVS:
            raise DEVSException("Cannot instantiate abstract class '%s' ... "
                                % (self.__class__.__name__))
        # The minimal constructor shall first call the superclass
        # (i.e., BaseDEVS) constructor.
        BaseDEVS.__init__(self, name)

        # Increment CoupledIDCounter and setup instance's myID
        # attribute.
        self.myID = "C%d" % self.model_id

        # All components of this coupled model (the submodels)
        self.componentSet = []

        # IC, EIC and EOC describe the couplings at the
        # coupled-DEVS level (respectively, internal couplings,
        # external input couplings and external output couplings).
        # Note that although consistent with Zeigler's definition, these sets
        # are not used by the simulator, which relies on ports' inLine and
        # outLine attributes to detect couplings.
        self.IC  = []
        self.EIC = []
        self.EOC = []

    def revert(self, time):
        """
        Revert the coupled model to the specified time, all submodels will also
        be reverted.
        Args:
            time - the time up to which revertion should happen
        """
        for child in self.componentSet:
            if child.timeLast >= time:
                child.revert(time)
            # Always clear the inputs, as it is possible that there are only
            # partial results, which doesn't get found in the timeLast >= time
            child.myInput = {}
        self.myInput = {}
        self.setTimeNext()
        if self.parent is not None:
            self.rootsim.model.childRevert(self)

    def setTimeNext(self):
        """
        Reset the timeNext of this model, useful if a deep model was updated
        """
        try:
            self.timeNext = self.scheduler.readFirst()[0]
        except IndexError:
            # No element found in the scheduler, so put it to INFINITY
            self.timeNext = (float('inf'), 1)

    def childRevert(self, child):
        """
        Notify this model that the child was reverted
        Args:
            child - the child that was reverted
        """
        self.scheduler.unschedule(child)
        self.scheduler.schedule(child)
        oldTimeNext = self.timeNext
        try:
            self.timeNext = self.scheduler.readFirst()[0]
            self.timeLast = self.scheduler.readFirst()[3].timeLast
        except IndexError:
            self.timeNext = (float('inf'), 0)
        if self.timeNext != oldTimeNext and self.parent is not None:
            self.parent.childRevert(self)

    def addSubModel(self, model, location = None, imports = None):
        """
        Adds a specified model to the current coupled model as its child. This
        is the function that must be used to make distributed simulation
        possible.
        Args:
            model - the model to be added as a child
                    either a child of BaseDEVS
                    or a string specifying a call to the constructor.
                    If the location is different from None, this model
                    must be a string which gets executed on the location
           location - the location at which the child must run
        """
        self.model_ids[self.model_id] = self

        # Check whether or not the model should be ran on a remote server
        if location is None:
            # Seems to run locally
            if isinstance(model, str):
                if imports is not None:
                    exec(imports)
                model = eval(model)
            entry = model
            model.parent = self
            model.setRootSim(self.rootsim, self.location)
            self.model_ids[model.model_id] = model
        else:
            # Seems to run elsewhere
            # OK, we can ask this server to instantiate the specified model
            remote = getProxy(location)
            Port.counter = remote.setCoupledModel(model, self.location,
                                                  self.model_id, imports)
            # Provide an interface for this remote model
            entry = RemoteCDEVS(location)
            entry.parent = self
            entry.setRootSim(self.rootsim, self.location)
            entry.setData()
            self.model_ids[entry.model_id] = entry

        self.model_ids.update(entry.getModelIDs())
        self.componentSet.append(entry)
        return entry

    def getLocationList(self, cset):
        cset.add(self.rootsim.name)
        for i in self.componentSet:
            retval = i.getLocationList(cset)
            for j in retval:
                cset.add(j)
        return cset

    def fixHierarchy(self, location, parentname):
        """
        Fixes the hierarchy of the coupled model
        Args:
            location - the location of the coupled model
        """
        self.location = location
        if parentname != "":
            self.fullName = parentname + "." + self.name
        else:
            self.fullName = self.name
        if self.parent is not None:
            self.parent.name = parentname
        for i in self.componentSet:
            i.fixHierarchy(location, str(self.fullName))

    def setRootSim(self, rsim, name):
        """
        Set the root simulator of this coupled model
        Args:
            rsim - the root simulator
            name - the name of the current location
        """
        self.rootsim = rsim
        self.location = name
        for comp in self.componentSet:
            comp.setRootSim(rsim, name)

    ###
    def connectPorts(self, p1, p2):
        """
        Connects two ports together. The coupling is to begin at p1 and
        to end at p2.
        """
        # For a coupling to be valid, two requirements must be met:
        # 1- at least one of the DEVS the ports belong to is a child of the
        #    coupled-DEVS (i.e., self), while the other is either the
        #    coupled-DEVS itself or another of its children. The DEVS'
        #    'parenthood relationship' uniquely determine the type of coupling;
        # 2- the types of the ports are consistent with the 'parenthood' of the
        #    associated DEVS. This validates the coupling determined above.

        # Internal Coupling:
        if ((p1.hostDEVS.parent == self and p2.hostDEVS.parent == self) and
                (p1.type() == 'OUTPORT' and p2.type() == 'INPORT')):
            if p1.hostDEVS is p2.hostDEVS:
                raise DEVSException("In coupled model '%s', connecting ports" +
                                    " '%s' and '%s' belong to the same model" +
                                    " '%s'. " +
                                    " Direct feedback coupling not allowed" % (
                                    self.getModelFullName(),
                                    p1.getPortFullName(),
                                    p2.getPortFullName(),
                                    p1.hostDEVS.getModelFullName()))
            else:
                self.IC.append( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
                p1.outLine.append(p2)
                p2.inLine.append(p1)

        # External input couplings:
        elif ((p1.hostDEVS == self and p2.hostDEVS.parent == self) and
              (p1.type() == p2.type() == 'INPORT')):
            self.EIC.append( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
            p1.outLine.append(p2)
            p2.inLine.append(p1)

        # Eternal output couplings:
        elif ((p1.hostDEVS.parent == self and p2.hostDEVS == self) and
              (p1.type() == p2.type() == 'OUTPORT')):
            self.EOC.append( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
            p1.outLine.append(p2)
            p2.inLine.append(p1)

        # Other cases (illegal coupling):
        else:
            raise DEVSException("Illegal coupling in coupled model '%s' " +
                                "between ports '%s' and '%s'" % (
                                self.getModelFullName(), p1.getPortFullName(),
                                p2.getPortFullName()))

    def setGVT(self, GVT):
        """
        Sets the GVT of this coupled model
        Args:
            GVT - the time to which the GVT should be set
        """
        BaseDEVS.setGVT(self, GVT)
        for i in self.componentSet:
            i.setGVT(GVT)

    def printModel(self, indent=0):
        print(('\t'*indent + "Coupled " + str(self.getModelFullName())))
        for i in self.OPorts:
            print(('\t'*(indent+1) + "OPort " + str(i.getPortFullName())))
            for j in i.outLine:
                print(('\t'*(indent+2) + str(j.hostDEVS.getModelFullName())))
        for i in self.componentSet:
            i.printModel(indent+1)

##  PORT CLASS
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class Port(object):
    """
    Class for DEVS model ports (both input and output).

    This class provides basic port attributes and query methods.
    """

    ###
    def __init__(self, isInput = True, name=None):
        """
        Constructor. Creates an input port if isInput evaluates to True, and
        an output port otherwise.
        Args:
            isInput - is this an input port?
            name - the name of the port, should be UNIQUE. If None is provided
                   a unique ID is used
        """

        # Port Attributes:
        # * inLine and outLine represent an alternate way to
        #   describe couplings (and the one actually used by the simulator).
        #   The former is a list of references to the (possibly many) ports
        #   from which this port receives its messages, while the latter is a
        #   list of references to the (possibly many) ports which receive
        #   messages from this port. (Note that no more than one message
        #   can be received at one time: to be completed). While an atomic-DEVS
        #   output port (input port) would only need to declare outLine
        #   (inLine), the dual nature of coupled-DEVS ports require both
        #   attributes;
        # * myID;
        # * hostDEVS: the DEVS model that hosts this port;
        self.inLine = []
        self.outLine = []
        self.hostDEVS = None

        # The name of the port
        self.name = name

        # Increment InCounter or OutCounter depending on type of
        # port desired, and setup instance's myID attribute:
        global PortCounter
        PortCounter += 1
        if isInput:
            self.myID = "InPort_%d" % PortCounter
        else:
            self.myID = "OutPort_%d" % PortCounter

    def getPortName(self):
        """
        Returns the name of the port
        """
        if self.name is None:
            self.name = "port%s" % self.myID
            if self.hostDEVS is not None:
                attr_name = self.hostDEVS.getPortName(self)
                if attr_name is not None:
                    self.name = attr_name
        return self.name

    def getPortFullName(self):
        """
        Returns the complete name of the port
        """
        base = ""
        if self.hostDEVS is not None:
            base = str(self.hostDEVS.getModelFullName())
        return base + "." + self.getPortName()

    def type(self):
        """
        Returns the 'type' of the object: 'INPORT' or 'OUTPORT'.
        """
        if self.myID[:2] == 'In':
            return 'INPORT'
        elif self.myID[:3] == 'Out':
            return 'OUTPORT'

class RemoteCDEVS(BaseDEVS):
    """
    An RemoteCDEVS is an interface for a model that is remotely located
    It provides the most important functions, which are redirected to the
    real model, located elsewhere. It is also a coupled model, as only
    coupled models can be remote.
    """
    def __init__(self, location, name = None):
        """
        Constructor
        Args:
            location - the location of the remote model
        """
        BaseDEVS.__init__(self, name)
        self.remote_location = location
        self.proxy = getProxy(self.remote_location)
        self.remote_modelname = name

    def setData(self):
        """
        Set all data for this model correctly
        """
        if self.IPorts or self.OPorts:
            # Already configured this port once
            return
        ports = self.proxy.getInOut(self.remote_modelname)
        for data in ports:
            name = data[0]
            porttype = data[1]
            counter = data[2]
            if porttype == 'INPORT':
                setattr(self, name, self.addInPort(data[0]))
            elif porttype == 'OUTPORT':
                setattr(self, name, self.addOutPort(data[0]))
            self.remapPort2Num[getattr(self, name)] = counter
            self.remapNum2Port[counter] = getattr(self, name)
        if not isinstance(self.remote_modelname, list):
            self.remote_modelid = self.proxy.getModelidByName(self.remote_modelname)

    def getLocationList(self, cset):
        if self.remote_location not in cset:
            cset = self.proxy.getLocationList(cset)
        return cset

    def printModel(self, indent=0):
        print(('\t'*indent + "Remote to %s (%s)" % (self.remote_location,
                                                  self.remote_modelname)))
        for i in self.OPorts:
            print(('\t'*(indent+1) + "OPort %s" % i.getPortFullName()))
            for j in i.outLine:
                print(('\t'*(indent+2) + str(j.hostDEVS.getModelFullName())))

    def send(self, msg):
        """
        Send a message to this model, it will actually be redirected to the
        remote model in a way that is transparent to the invoker of the send
        method.
        Args:
            msg - the message that must be sent
        """
        assert logger.debug("Sending message " + str(msg) + " to " + str(self.remote_location))
        #print("Sending " + str(msg))
        if msg.messagetype != 3:
            # Only forward real messages, the rest (control messages) are
            # provided locally at the remote model
            assert logger.debug("message != 3 sent")
            return
        if self.rootsim.blockOutgoing and (self.rootsim.procTransition) and (not self.rootsim.checkpoint_restored):
        #if self.rootsim.reverted and (self.rootsim.procTransition):
            # If the model was just reverted, we don't need to sent out these
            # messages because they are already in the receivers queues.
            assert logger.debug("Not sending message for reason (" + str(self.rootsim.reverted) + ", " + str(self.rootsim.procTransition)+ ", " + str(self.rootsim.checkpoint_restored) + "): " + str(msg))
            return
        self.rootsim.checkpoint_restored = False
        # Convert the message's keys (the ports), as they are unknown at the
        # receiving side and cause problems in Pyro
        modmsg = {}
        for entry in msg.content:
            # Use the remapping function that was 'negotiated' between
            # the different representations
            modmsg[self.remapPort2Num[entry]] = msg.content[entry]
        msg.content = modmsg
        msg = NetworkMessage(Message(msg.timestamp, 3, msg.content), False, self.rootsim.genUUID(), self.rootsim.color, self.remote_location)
        # Make a copy for the outputQueue, this MUST be a copy, as
        # otherwise we modify the original message.
        # UNLESS we are irreversible, as this means we will never need
        # these again, so we can save some space and time, when setting GVT
        # Data to know how to route the message in case of invalidation
        self.rootsim.outputQueue.append(msg)

        self.rootsim.notifySend(self.remote_location, msg.timestamp[0], msg.color)
        remote = getProxy(self.remote_location)
        # Make it a oneway call, otherwise our simulator would be synchronous
        makeOneway(remote, "send")
        if isinstance(self.remote_modelname, list):
            remote.send(None, msg, external=True)
        else:
            remote.send(self.remote_modelid, msg, external=True)

    def revert(self, time):
        """
        Revert the model. Since this is a remote model, revertions will
        NOT propagate. Revertion is the responsibility of the model's root
        simulator and should not be decided remotely.
        Args:
            time - the time to which revertion must take place
        """
        # Don't revert the remote kernel, it will do so itself if necessary
        pass

    def childRevert(self, child):
        """
        Notify that a child was reverted. Since this is a remote model, it is
        only possible that this gets called if it is outside of the root
        simulator, so there is no need to do anything.
        Args:
            child - the child that was reverted
        """
        # Not interested as parent doesn't have a timeNext value
        pass

    def fixHierarchy(self, parentLocation, parentname):
        """
        Fix the hierarchy of this model
        Args:
            parentLocation - the location of the parent
        """
        self.proxy = getProxy(self.remote_location)
        if self.parent is not None:
            self.parent.name = parentname
        if self.remote_modelname is None:
            self.fullName = parentname + "." + self.proxy.getModelName()
        else:
            self.fullName = self.remote_modelname
        self.proxy.fixHierarchy(parentLocation, parentname)

    def getTargets(self, modelname, portname):
        """
        Forwards the getTargets to the remote simulator
        """
        return self.proxy.getTargets(modelname, portname)
