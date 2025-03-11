# -*- coding: Latin-1 -*-
"""
Classes and tools for DEVS model specification
"""

from .logger import debug, warn, info, error
from .util import *
import time
import importlib

class BaseDEVS(object):
    """
    Abstract base class for AtomicDEVS and CoupledDEVS classes.

    This class provides basic DEVS attributes and query/set methods.
    """
    def __init__(self, name):
        """
        Constructor

        :param name: the name of the DEVS model
        """

        # Prevent any attempt to instantiate this abstract class
        if self.__class__ == BaseDEVS:
            raise DEVSException ("Cannot instantiate abstract class '%s' ... "
                                 % (self.__class__.__name__))

        # The parent of the current model
        self.parent = None
        # The local name of the model
        self.name = name
        self.IPorts  = []
        self.OPorts   = []
        self.ports = []

        # Initialise the times
        self.timeLast = (0.0, 0)
        self.timeNext = (0.0, 1)

        self.location = None

        # Variables used for optimisations
        self.myInput = {}
        self.myOutput = {}

        # The state queue, used for time warp
        self.oldStates = []
        # List of all memoized states, only useful in distributed simulation
        #   with memoization enabled
        self.memo = []

    def simSettings(self, simulator):
        """
        Modifies the simulation settings from within the model.

        This function is called _before_ direct connection and distribution is performed, so the user can still access the complete hierarchy.

        .. note:: This function is *only* called on the root model of the simulation, thus the model passed to the constructor of the Simulator object.

        :param simulator: the simulator object on which settings can be configured
        """
        pass

    def modelTransition(self, state):
        """
        DEFAULT function for Dynamic Structure DEVS, always returning False (thus indicating that no structural change is needed)

        :param state: a dict that can be used to save some kind of state, this object is maintained by the kernel and will be passed each time
        :returns: bool -- whether or not a structural change is necessary
        """
        return False

    def getVCDVariables(self):
        """
        Fetch all the variables, suitable for VCD variable generation

        :returns: list -- all variables needed for VCD tracing
        """
        varList = []
        for I in self.ports:
            varList.append([self.getModelFullName(), I.getPortName()])
        return varList

    def removePort(self, port):
        """
        Remove a port (either input or output) from the model, disconnecting all of its connections.

        :param port: the port to remove
        """
        if not hasattr(self, "fullName"):
            raise DEVSException("removePort should only be called during a simulation")
        if port.isInput:
            self.IPorts.remove(port)
        else:
            self.OPorts.remove(port)
        self.ports.remove(port)

        # Also remove all connections to this port
        self.server.getSelfProxy().dsRemovePort(port)

    def addPort(self, name, isInput):
        """
        Utility function to create a new port and add it everywhere where it is necessary

        :param name: the name of the port
        :param isInput: whether or not this is an input port
        """
        name = name if name is not None else "port%s" % len(self.ports)
        port = Port(isInput=isInput, name=name)
        if isInput:
            self.IPorts.append(port)
        else:
            self.OPorts.append(port)
        port.port_id = len(self.ports)
        self.ports.append(port)
        port.hostDEVS = self
        return port

    def addInPort(self, name=None):
        """
        Add an input port to the DEVS model.

        addInPort is the only proper way to add input ports to a DEVS model.
        As for the CoupledDEVS.addSubModel method, calls
        to addInPort and addOutPort can appear in any DEVS'
        descriptive class constructor, or the methods can be used with an
        instantiated object.

        The methods add a reference to the new port in the DEVS' IPorts
        attributes and set the port's hostDEVS attribute. The modeler
        should typically save the returned reference somewhere.

        :param name: the name of the port. A unique ID will be generated in case None is passed
        :returns: port -- the generated port
        """
        return self.addPort(name, True)

    def addOutPort(self, name=None):
        """Add an output port to the DEVS model.

        addOutPort is the only proper way to
        add output ports to DEVS. As for the CoupledDEVS.addSubModel method, calls
        to addInPort and addOutPort can appear in any DEVS'
        descriptive class constructor, or the methods can be used with an
        instantiated object.

        The methods add a reference to the new port in the DEVS'
        OPorts attributes and set the port's hostDEVS attribute. The modeler
        should typically save the returned reference somewhere.

        :param name: the name of the port. A unique ID will be generated in case None is passed
        :returns: port -- the generated port
        """
        return self.addPort(name, False)

    def getModelName(self):
        """
        Get the local model name

        :returns: string -- the name of the model
        """
        if self.name is None:
            return str(self.model_id)
        else:
            return str(self.name)

    def getModelFullName(self):
        """
        Get the full model name, including the path from the root

        :returns: string -- the fully qualified name of the model
        """
        return self.fullName

class AtomicDEVS(BaseDEVS):
    """
    Abstract base class for all atomic-DEVS descriptive classes.
    """

    def __init__(self, name=None):
        """
        Constructor for an AtomicDEVS model

        :param name: name of the model, can be None to have an automatically generated name
        """
        # Prevent any attempt to instantiate this abstract class
        if self.__class__ == AtomicDEVS:
            raise DEVSException("Cannot instantiate abstract class '%s' ... "
                                % (self.__class__.__name__))

        # The minimal constructor shall first call the superclass
        # (i.e., BaseDEVS) constructor.
        BaseDEVS.__init__(self, name)

        self.elapsed = 0.0
        self.state = None
        self.relocatable = True
        self.lastReadTime = (0, 0)

    def setLocation(self, location, force=False):
        """
        Sets the location of the atomic DEVS model if it was not already set

        :param location: the location to set
        :param force: whether or not to force this location, even if another is already defined
        """
        if self.location is None or force:
            self.location = location

    def fetchActivity(self, time, activities):
        """
        Fetch the activity of the model up to a certain time

        :param time: the time up to which the activity should be calculated
        :param activities: dictionary containing all activities for the models
        """
        activities[self.model_id] = sum(
                [state.activity for state in self.oldStates if state.timeLast[0] < time])

    def setGVT(self, GVT, activities, lastStateOnly):
        """
        Set the GVT of the model, cleaning up the states vector as required
        for the time warp algorithm

        :param GVT: the new value of the GVT
        :param activities: dictionary containing all activities for the models
        """
        copy = None
        activity = 0
        for i in range(len(self.oldStates)):
            state = self.oldStates[i]
            if state.timeLast[0] >= GVT:
                # Possible that all elements should be kept,
                # in which case it will return -1 and only keep the last element
                # So the copy element should be AT LEAST 0
                copy = max(0, i-1)
                break
            elif not lastStateOnly:
                activity += state.activity
        if self.oldStates == []:
            raise DEVSException("Model has no memory of the past!")
        elif copy is None:
            self.oldStates = [self.oldStates[-1]]
        else:
            self.oldStates = self.oldStates[copy:]
        if lastStateOnly:
            activity = self.oldStates[0].activity
        activities[self.model_id] = activity

    def revert(self, time, memorize):
        """
        Revert the model to the specified time. All necessary cleanup for this
        model will be done (fossil collection).

        :param time: the time up to which should be reverted
        :param memorize: whether or not the saved states should still be kept for memoization
        """
        newstate = len(self.oldStates) - 1
        for state in reversed(self.oldStates[1:]):
            if state.timeLast < time:
                break
            newstate -= 1

        state = self.oldStates[newstate]
        self.timeLast = state.timeLast
        self.timeNext = state.timeNext

        self.state = state.loadState()
        if memorize:
            # Reverse it too
            self.memo = self.oldStates[:-len(self.oldStates)+newstate-1:-1]
        self.oldStates = self.oldStates[:newstate+1]

        # Check if one of the reverted states was ever read for the termination condition
        if self.lastReadTime > time:
            # It seems it was, so notify the main revertion algorithm of this
            self.lastReadTime = (0, 0)
            return True
        else:
            return False

        # NOTE clearing the myInput happens in the parent

    def getState(self, requestTime, firstCall=True):
        """
        For the distributed termination condition: fetch the state of the model at a certain time

        :param time: the time (including age!) for which the state should be fetched
        :returns: state -- the state at that time
        """
        if self.location != MPIRedirect.local.name:
            return getProxy(self.location).getStateAtTime(self.model_id, requestTime)
        elif firstCall:
            # Shortcut if the call is local
            return self.state
        self.lastReadTime = requestTime
        while 1:
            for state in self.oldStates:
                if state.timeLast > requestTime:
                    return state.loadState()
            # State not yet available... wait some time before trying again...
            time.sleep(0.01)

    def extTransition(self, inputs):
        """
        DEFAULT External Transition Function.

        Accesses state and elapsed attributes, as well as inputs
        through the passed dictionary. Returns the new state.

        .. note:: Should only write to the *state* attribute.

        :param inputs: dictionary containing all ports and their corresponding outputs
        :returns: state -- the new state of the model
        """
        return self.state

    def intTransition(self):
        """
        DEFAULT Internal Transition Function.

        .. note:: Should only write to the *state* attribute.

        :returns: state -- the new state of the model

        .. versionchanged:: 2.1 The *elapsed* attribute is no longer guaranteed to be correct as this isn't required by the DEVS formalism.

        """
        return self.state

    def confTransition(self, inputs):
        """
        DEFAULT Confluent Transition Function.

        Accesses state and elapsed attributes, as well as inputs
        through the passed dictionary. Returns the new state.

        .. note:: Should only write to the *state* attribute.

        :param inputs: dictionary containing all ports and their corresponding outputs
        :returns: state -- the new state of the model
        """
        self.state = self.intTransition()
        self.state = self.extTransition(inputs)
        return self.state

    def outputFnc(self):
        """
        DEFAULT Output Function.

        Accesses only state attribute. Returns the output on the different ports as a dictionary.

        .. note:: Should **not** write to any attribute.

        :returns: dictionary containing output ports as keys and lists of output on that port as value

        .. versionchanged:: 2.1 The *elapsed* attribute is no longer guaranteed to be correct as this isn't required by the DEVS formalism.

        """
        return {}

    def timeAdvance(self):
        """
        DEFAULT Time Advance Function.

        .. note:: Should ideally be deterministic, though this is not mandatory for simulation.

        :returns: the time advance of the model

        .. versionchanged:: 2.1 The *elapsed* attribute is no longer guaranteed to be correct as this isn't required by the DEVS formalism.

        """
        # By default, return infinity
        return float('inf')

    def preActivityCalculation(self):
        """
        DEFAULT pre-transition activity fetcher. The returned value is passed to the *postActivityCalculation* function

        :returns: something -- passed to the *postActivityCalculation*
        """
        return time.time()

    def postActivityCalculation(self, prevalue):
        """
        DEFAULT post-transition activity fetcher. The returned value will be passed on to the relocator and MUST be an addable (e.g. integer, float, ...)

        :param prevalue: the value returned from the *preActivityCalculation* method
        :returns: addable (float, integer, ...) -- passed to the relocator
        """
        return time.time() - prevalue

    def flattenConnections(self):
        """
        Flattens the pickling graph, by removing backreference from the ports.
        """
        # It doesn't really matter what gets written in these hostDEVS attributes,
        # as it will never be used. Though for readability, the model_id will be used
        # to make it possible to do some debugging when necessary.
        for port in self.IPorts:
            port.hostDEVS = self.model_id
        for port in self.OPorts:
            port.hostDEVS = self.model_id

    def unflattenConnections(self):
        """
        Unflattens the picking graph, by reconstructing backreferences from the ports.
        """
        for port in self.IPorts:
            port.hostDEVS = self
        for port in self.OPorts:
            port.hostDEVS = self

    def finalize(self, name, model_counter, model_ids, locations, selectHierarchy):
        """
        Finalize the model hierarchy by doing all pre-simulation configuration

        .. note:: Parameters *model_ids* and *locations* are updated by reference.

        :param name: the name of the hierarchy above
        :param model_counter: the model ID counter
        :param model_ids: a list with all model_ids and their model
        :param locations: dictionary of locations and where every model runs
        :param selectHierarchy: hierarchy to perform selections in Classic DEVS

        :returns: int -- the new model ID counter
        """
        # Give a name
        self.fullName = name + str(self.getModelName())

        # Give a unique ID to the model itself
        self.model_id = model_counter
        self.selectHierarchy = selectHierarchy + [self]

        # Add the element to its designated place in the model_ids list
        model_ids.append(self)

        # Do a quick check, since this is vital to correct operation
        if model_ids[self.model_id] != self:
            raise DEVSException("Something went wrong while initializing models: IDs don't match")

        locations[self.location].append(self.model_id)

        # Return the unique ID counter, incremented so it stays unique
        return model_counter + 1

    def getModelLoad(self, lst):
        """
        Add this atomic model to the load of its location

        :param lst: list containing all locations and their current load
        :returns: int -- number of children in this subtree
        """
        lst[self.location] += 1
        self.nChildren = 1
        return self.nChildren

class CoupledDEVS(BaseDEVS):
    """
    Abstract base class for all coupled-DEVS descriptive classes.
    """

    def __init__(self, name=None):
        """
        Constructor.

        :param name: the name of the coupled model, can be None for an automatically generated name
        """
        # Prevent any attempt to instantiate this abstract class
        if self.__class__ == CoupledDEVS:
            raise DEVSException("Cannot instantiate abstract class '%s' ... "
                                % (self.__class__.__name__))
        # The minimal constructor shall first call the superclass
        # (i.e., BaseDEVS) constructor.
        BaseDEVS.__init__(self, name)

        # All components of this coupled model (the submodels)
        self.componentSet = []

    def forceSequential(self):
        """
        TODO
        """
        self.setLocation(0, force=True)

    def select(self, immChildren):
        """
        DEFAULT select function, only used when using Classic DEVS simulation

        :param immChildren: list of all children that want to transition
        :returns: child -- a single child that is allowed to transition
        """
        return immChildren[0]

    def getModelLoad(self, lst):
        """
        Fetch the number of atomic models at this model

        :param lst: list containing all locations and their current load
        :returns: number of atomic models in this subtree, including non-local ones
        """
        children = 0
        for i in self.componentSet:
            children += i.getModelLoad(lst)
        self.nChildren = children
        return self.nChildren

    def finalize(self, name, model_counter, model_ids, locations, selectHierarchy):
        """
        Finalize the model hierarchy by doing all pre-simulation configuration

        .. note:: Parameters *model_ids* and *locations* are updated by reference.

        :param name: the name of the hierarchy above
        :param model_counter: the model ID counter
        :param model_ids: a list with all model_ids and their model
        :param locations: dictionary of locations and where every model runs
        :param selectHierarchy: hierarchy to perform selections in Classic DEVS

        :returns: int -- the new model ID counter
        """
        # Set name, even though it will never be requested
        self.fullName = name + str(self.getModelName())
        for i in self.componentSet:
            model_counter = i.finalize(self.fullName + ".", model_counter,
                    model_ids, locations, selectHierarchy + [self])
        return model_counter

    def flattenConnections(self):
        """
        Flattens the pickling graph, by removing backreference from the ports.
        """
        for i in self.componentSet:
            i.flattenConnections()

    def unflattenConnections(self):
        """
        Unflattens the pickling graph, by reconstructing backreference from the ports.
        """
        for i in self.componentSet:
            i.unflattenConnections()

    def addSubModel(self, model, location = None):
        """
        Adds a specified model to the current coupled model as its child. This
        is the function that must be used to make distributed simulation
        possible.

        :param model: the model to be added as a child
        :param location: the location at which the child must run
        :returns: model -- the model that was created as a child

        .. versionchanged:: 2.1.3
           model can no longer be a string, this was previously a lot more efficient in partial distribution, though this functionality was removed together with the partial distribution functionality.
        """
        model.parent = self
        if location is not None:
            location = int(location)
        model.location = location if location is not None else self.location
        if model.location is not None and isinstance(model, CoupledDEVS):
            # Set the location of all children
            for i in model.componentSet:
                i.setLocation(model.location)
        self.componentSet.append(model)
        if hasattr(self, "fullName"):
            # Full Name is only created when starting the simulation, so we are currently in a running simulation
            # Dynamic Structure change
            self.server.getSelfProxy().dsScheduleModel(model)
        return model

    def removeSubModel(self, model):
        """
        Remove a specified model from the current coupled model, only callable while in a simulation.

        :param model: the model to remove as a child
        """
        if not hasattr(self, "fullName"):
            raise DEVSException("removeSubModel can only be called _during_ a simulation run")
        self.server.getSelfProxy().dsUnscheduleModel(model)

    def disconnectPorts(self, p1, p2):
        """
        Disconnect two ports

        .. note:: If these ports are connected multiple times, **only one** of them will be removed.

        :param p1: the port at the start of the connection
        :param p2: the port at the end of the connection
        """
        ncon = []
        found = False
        for p in p1.outLine:
            if p == p2 and not found:
                found = True
            else:
                ncon.append(p)
        p1.outLine = ncon
        ncon = []
        found = False
        for p in p2.inLine:
            if p == p1 and not found:
                found = True
            else:
                ncon.append(p)
        p2.inLine = ncon

    def connectPorts(self, p1, p2, z = None):
        """
        Connects two ports together. The coupling is to begin at p1 and
        to end at p2.

        :param p1: the port at the start of the new connection
        :param p2: the port at the end of the new connection
        :param z: the translation function for the events
                  either input-to-input, output-to-input or output-to-output.
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
                raise DEVSException(("In coupled model '%s', connecting ports" +
                                    " '%s' and '%s' belong to the same model" +
                                    " '%s'. " +
                                    " Direct feedback coupling not allowed") % (
                                    self.getModelFullName(),
                                    p1.getPortFullName(),
                                    p2.getPortFullName(),
                                    p1.hostDEVS.getModelFullName()))
            else:
                p1.outLine.append(p2)
                p2.inLine.append(p1)

        # External input couplings:
        elif ((p1.hostDEVS == self and p2.hostDEVS.parent == self) and
              (p1.type() == p2.type() == 'INPORT')):
            p1.outLine.append(p2)
            p2.inLine.append(p1)

        # Eternal output couplings:
        elif ((p1.hostDEVS.parent == self and p2.hostDEVS == self) and
              (p1.type() == p2.type() == 'OUTPORT')):
            p1.outLine.append(p2)
            p2.inLine.append(p1)

        # Other cases (illegal coupling):
        else:
            raise DEVSException(("Illegal coupling in coupled model '%s' " +
                                "between ports '%s' and '%s'") % (
                                self.getModelName(), p1.getPortName(),
                                p2.getPortName()))

        p1.zFunctions[p2] = z

    def setLocation(self, location, force=False):
        """
        Sets the location of this coupled model and its submodels if they don't have their own preference.

        :param location: the location to set
        :param force: whether or not to force this location, even if another is already defined
        """
        if self.location is None or force:
            self.location = location
            for child in self.componentSet:
                child.setLocation(location, force)

class RootDEVS(BaseDEVS):
    """
    The artificial RootDEVS model is the only 'coupled' model in the simulation after direct connection is performed.
    """
    def __init__(self, components, models, schedulerType):
        """
        Basic constructor.

        :param components: the atomic DEVS models that are the cildren, only those that are ran locally should be mentioned
        :param models: all models that have to be passed to the scheduler, thus all models, even non-local ones
        :param schedulerType: type of scheduler to use (string representation)
        """
        BaseDEVS.__init__(self, "ROOT model")
        self.componentSet = components
        self.timeNext = (float('inf'), 1)
        self.local_model_ids = set()
        for i in self.componentSet:
            self.local_model_ids.add(i.model_id)
        self.models = models
        self.schedulerType = schedulerType
        self.directConnected = True

    def undoDirectConnect(self):
        """
        TODO
        """
        # Just mark
        self.directConnected = False

    def directConnect(self):
        """
        Perform direct connection on the models again
        """
        if self.directConnected:
            # Were already direct connected, so nothing to do
            return
        directConnect(self.models, True)
        self.directConnected = True

    def setScheduler(self, schedulerType):
        """
        Set the scheduler to the desired type. Will overwite the previously present scheduler.

        :param schedulerType: type of scheduler to use (string representation)
        """
        if isinstance(schedulerType, tuple):

            ###Py 3.x
            tv = importlib.import_module("DEVSKernel.PyPDEVS.pypdevs221.src.%s"%schedulerType[0])
            #exec("from %s import %s" % schedulerType)

            nrmodels = len(self.models)
            self.scheduler = eval("tv.%s(self.componentSet, EPSILON, nrmodels)" % schedulerType[1])
        else:
            raise DEVSException("Unknown Scheduler: " + str(schedulerType))

    def setGVT(self, GVT, activities, lastStateOnly):
        """
        Sets the GVT of this coupled model

        :param GVT: the time to which the GVT should be set
        :param activities: dictionary containing all activities for the models
        """
        for i in self.componentSet:
            i.setGVT(GVT, activities, lastStateOnly)

    def fetchActivity(self, time, activities):
        """
        Fetch the activity of the model up to a certain time

        :param time: the time up to which the activity should be calculated
        :param activities: dictionary containing all activities for the models
        """
        for i in self.componentSet:
            i.fetchActivity(time, activities)

    def revert(self, time, memorize):
        """
        Revert the coupled model to the specified time, all submodels will also
        be reverted.

        :param time: the time up to which revertion should happen
        :param memorize: whether or not the saved states should still be kept for memoization
        """
        reschedules = set()
        controllerRevert = False
        for child in self.componentSet:
            if child.timeLast >= time:
                controllerRevert |= child.revert(time, memorize)
                # Was reverted, so reschedule
                reschedules.add(child)
            # Always clear the inputs, as it is possible that there are only
            # partial results, which doesn't get found in the timeLast >= time
            child.myInput = {}
        self.scheduler.massReschedule(reschedules)
        self.setTimeNext()
        return controllerRevert

    def setTimeNext(self):
        """
        Reset the timeNext
        """
        try:
            self.timeNext = self.scheduler.readFirst()
        except IndexError:
            # No element found in the scheduler, so put it to INFINITY
            self.timeNext = (float('inf'), 1)

class Port(object):
    """
    Class for DEVS model ports (both input and output). This class provides basic port attributes and query methods.
    """
    def __init__(self, isInput, name=None):
        """
        Constructor. Creates an input port if isInput evaluates to True, and
        an output port otherwise.

        :param isInput: whether or not this is an input port
        :param name: the name of the port. If None is provided, a unique ID is generated
        """
        self.inLine = []
        self.outLine = []
        self.hostDEVS = None
        self.msgcount = 0

        # The name of the port
        self.name = name
        self.isInput = isInput
        self.zFunctions = defaultdict(None)

    def getPortName(self):
        """
        Returns the name of the port

        :returns: local name of the port
        """
        return self.name

    def getPortFullName(self):
        """
        Returns the complete name of the port

        :returns: fully qualified name of the port
        """
        return "%s.%s" % (self.hostDEVS.getModelFullName(), self.getPortName())

    def type(self):
        """
        Returns the 'type' of the object

        :returns: either 'INPORT' or 'OUTPORT'
        """
        if self.isInput:
            return 'INPORT'
        else:
            return 'OUTPORT'

def appendZ(first_z, new_z):
    if first_z is None:
        return new_z
    elif new_z is None:
        return first_z
    else:
        return lambda x: new_z(first_z(x))

def directConnect(componentSet, local):
    """
    Perform direct connection on this CoupledDEVS model

    :param componentSet: the iterable to direct connect
    :param local: whether or not simulation is local; if it is, dynamic structure code will be prepared
    :returns: the direct connected componentSet
    """
    newlist = []
    for i in componentSet:
        if isinstance(i, CoupledDEVS):
            componentSet.extend(i.componentSet)
        else:
            # Found an atomic model
            newlist.append(i)
    componentSet = newlist

    # All and only all atomic models are now direct children of this model
    for i in componentSet:
        # Remap the output ports
        for outport in i.OPorts:
            # The new contents of the line
            outport.routingOutLine = []
            worklist = [(p, outport.zFunctions.get(p, None)) for p in outport.outLine]
            for outline, z in worklist:
                # If it is a coupled model, we must expand this model
                if isinstance(outline.hostDEVS, CoupledDEVS):
                    for inline in outline.outLine:
                        # Add it to the current iterating list, so we can just continue
                        worklist.append((inline, appendZ(z, outline.zFunctions[inline])))
                        # If it is a Coupled model, we should just continue
                        # expanding it and not add it to the finished line
                        if not isinstance(inline.hostDEVS, CoupledDEVS):
                            outport.routingOutLine.append((inline, appendZ(z, outline.zFunctions[inline])))
                else:
                    for ol, z in outport.routingOutLine:
                        if ol == outline:
                            break
                    else:
                        # Add to the new line if it isn't already there
                        # Note that it isn't really mandatory to check for this,
                        # it is a lot cleaner to do so.
                        # This will greatly increase the complexity of the connector though
                        outport.routingOutLine.append((outline, z))
        # Remap the input ports: identical to the output ports, only in the reverse direction
        for inport in i.IPorts:
            inport.routingInLine = []
            for inline in inport.inLine:
                if isinstance(inline.hostDEVS, CoupledDEVS):
                    for outline in inline.inLine:
                        inport.inLine.append(outline)
                        if not isinstance(outline.hostDEVS, CoupledDEVS):
                            inport.routingInLine.append(outline)
                elif inline not in inport.routingInLine:
                    inport.routingInLine.append(inline)
    return componentSet
