"""
Controller used as a specific simulation kernel
"""
from .basesimulator import BaseSimulator
from .logger import *
import threading
import time
from . import middleware
from .DEVS import CoupledDEVS, AtomicDEVS

class Controller(BaseSimulator):
    """
    The controller class, which is a special kind of normal simulation kernel. This should always run on the node labeled 0.
    It contains some functions that are only required to be ran on a single node, such as GVT initiation
    """
    def __init__(self, name, model, server):
        """
        Constructor

        :param name: name of the controller
        :param model: model to host at the kernel
        """
        BaseSimulator.__init__(self, name, model, server)
        self.waitingLock = threading.Lock()
        self.noFinishRing = threading.Lock()
        self.noFinishRing.acquire()
        self.locationCellView = False
        self.graph = None
        self.allocations = None
        self.runningIrreversible = None
        self.initialAllocator = None
        self.prev_termination_time = 0.0

    def __setstate__(self, retdict):
        """
        For pickling

        :param retdict: dictionary containing attributes and their value
        """
        BaseSimulator.__setstate__(self, retdict)
        self.waitingLock = threading.Lock()
        self.noFinishRing = threading.Lock()
        self.noFinishRing.acquire()

    def GVTdone(self):
        """
        Notify this simulation kernel that the GVT calculation is finished
        """
        self.waitForGVT.set()

    def notifyWait(self):
        """
        Notify the controller that a simulation kernel is waiting.
        """
        with self.waitingLock:
            self.waiting += 1
            self.finishCheck.set()

    def notifyRun(self):
        """
        Notify the controller that a simulation kernel has started running again.
        """
        with self.waitingLock:
            self.waiting -= 1

    def isFinished(self, running):
        """
        Checks if all kernels have indicated that they have finished simulation.
        If each kernel has indicated this, a final (expensive) check happens to 
        prevent premature termination.

        :param running: the number of kernels that is simulating
        :returns: bool -- whether or not simulation is already finished
        """
        # NOTE make sure that GVT algorithm is not running at the moment, otherwise we deadlock!
        # it might be possible that the GVT algorithm starts immediately after the wait(), causing deadlock again
        # Now we are sure that the GVT algorithm is not running when we start this
        if self.waiting == running:
            # It seems that we should be finished, so just ACK this with every simulation kernel before proceeding
            #   it might be possible that the kernel's 'notifyRun' command is still on the way, making the simulation
            #   stop too soon.
            self.noFinishRing.acquire()
            msgcount = self.finishRing(0, 0, True)
            if msgcount == -1:
                # One of the nodes was still busy
                self.noFinishRing.release()
                return False
            else:
                msgcount2 = self.finishRing(0, 0, True)
                # If they are equal, we are done
                ret = msgcount == msgcount2
                if not ret:
                    self.noFinishRing.release()
                else:
                    self.waiting = 0
                return ret
        else:
            return False

    def waitFinish(self, running):
        """
        Wait until the specified number of kernels have all told that simulation
        finished.

        :param running: the number of kernels that is simulating
        """
        while 1:
            # Force a check after each second
            self.finishCheck.wait(1)
            self.finishCheck.clear()
            # Make sure that no relocations are running
            if self.isFinished(running):
                # All simulation kernels have told us that they are idle at the moment
                break
        self.runGVT = False
        self.eventGVT.set()
        self.gvtthread.join()

    def startGVTThread(self, GVT_interval):
        """
        Start the GVT thread

        :param GVT_interval: the interval between two successive GVT runs
        """
        # We seem to be the controller
        # Start up the GVT algorithm then
        self.eventGVT = threading.Event()
        self.runGVT = True
        self.gvtthread = threading.Thread(target=Controller.threadGVT, args=[self, GVT_interval])
        self.gvtthread.daemon = True
        self.gvtthread.start()

    def threadGVT(self, freq):
        """
        Run the GVT algorithm, this method should be called in its own thread,
        because it will block

        :param freq: the time to sleep between two GVT calculations
        """
        # Wait for the simulation to have done something useful before we start
        self.eventGVT.wait(freq)
        # Maybe simulation already finished...
        while self.runGVT:
            self.receiveControl([float('inf'), float('inf'), {}], True)
            # Wait until the lock is released elsewhere
            self.waitForGVT.wait()
            self.waitForGVT.clear()
            # Limit the GVT algorithm, otherwise this will flood the ring
            self.eventGVT.wait(freq)

    def getVCDVariables(self):
        """
        Generate a list of all variables that exist in the current scope

        :returns: list -- all VCD variables in the current scope
        """
        variables = []
        for d in self.total_model.componentSet:
            variables.extend(d.getVCDVariables())
        return variables

    def simulate_sync(self):
        """
        TODO
        """
        BaseSimulator.simulate_sync(self)
        self.noFinishRing.acquire()

    def simulate(self):
        """
        Run the actual simulation on the controller. This will simply 'intercept' the call to the original simulate and perform location visualisation when necessary.
        """
        self.checkForTemporaryIrreversible()
        self.noFinishRing.release()
        if self.locationCellView:
            from .activityVisualisation import visualizeLocations
            visualizeLocations(self)
        # Call superclass (the actual simulation)
        BaseSimulator.simulate(self)
        self.prev_termination_time = self.termination_time[0]

    def getEventGraph(self):
        """
        Fetch a graph containing all connections and the number of events between the nodes. This is only useful when an initial allocator is chosen.

        :returns: dict -- containing source and destination, it will return the amount of events passed between them
        """
        return self.runAllocator()[0]

    def getInitialAllocations(self):
        """
        Get a list of all initial allocations. Will call the allocator to get the result.

        :returns: list -- containing all nodes and the models they host
        """
        return self.runAllocator()[1]

    def runAllocator(self):
        """
        Actually extract the graph of exchanged messages and run the allocator with this information. 
        
        Results are cached.

        :returns: tuple -- the event graph and the allocations
        """
        # Only run this code once
        if self.graph is None and self.allocations is None:
            # It seems this is the first time
            if self.initialAllocator is None:
                # No allocator was defined, or it has already issued its allocation code, which resulted into 'nothing'
                self.graph = None
                self.allocations = None
            else:
                from .util import constructGraph, saveLocations
                self.graph = constructGraph(self.model)
                self.allocations = self.initialAllocator.allocate(self.model.componentSet, self.getEventGraph(), self.kernels, self.totalActivities)
                self.initialAllocator = None
                saveLocations("locationsave.txt", self.allocations, self.model_ids)
        return self.graph, self.allocations

    def setCellLocationTracer(self, x, y, locationCellView):
        """
        Sets the Location tracer and all its configuration parameters

        :param x: the horizontal size of the grid
        :param y: the vertical size of the grid
        :param locationCellView: whether or not to enable it
        """
        self.x_size = x
        self.y_size = y
        self.locationCellView = locationCellView

    def setRelocator(self, relocator):
        """
        Sets the relocator to the one provided by the user

        :param relocator: the relocator to use
        """
        self.relocator = relocator

        # Perform run-time configuration
        try:
            self.relocator.setController(self)
        except AttributeError:
            pass

    def setActivityTracking(self, at):
        """
        Sets the use of activity tracking, which will simply output the activity of all models at the end of the simulation

        :param at: whether or not to enable activity tracking
        """
        self.activityTracking = at

    def setClassicDEVS(self, classicDEVS):
        """
        Sets the use of Classic DEVS instead of Parallel DEVS.

        :param classicDEVS: whether or not to use Classic DEVS
        """
        # Do this once, to prevent checks for the classic DEVS formalism
        if classicDEVS:
            self.coupledOutputGeneration = self.coupledOutputGenerationClassic

    def setAllocator(self, initialAllocator):
        """
        Sets the use of an initial relocator.

        :param initialAllocator: whether or not to use an initial allocator
        """
        self.initialAllocator = initialAllocator
        if initialAllocator is not None:
            self.atomicOutputGeneration_backup = self.atomicOutputGeneration
            self.atomicOutputGeneration = self.atomicOutputGenerationEventTracing

    def setDSDEVS(self, dsdevs):
        """
        Whether or not to check for DSDEVS events

        :param dsdevs: dsdevs boolean
        """
        self.useDSDEVS = dsdevs

    def setRealtime(self, inputReferences):
        """
        Sets the use of realtime simulation.

        :param inputReferences: dictionary containing the string to port mapping
        """
        self.realtime = True
        self.realTimeInputPortReferences = inputReferences

    def setTerminationCondition(self, termination_condition):
        """
        Sets the termination condition of this simulation kernel.
    
        As soon as the condition is valid, it willl signal all nodes that they have to stop simulation as soon as they have progressed up to this simulation time.

        :param termination_condition: a function that accepts two parameters: *time* and *model*. Function returns whether or not to halt simulation
        """
        self.termination_condition = termination_condition
        self.termination_time_check = False

    def findAndPerformRelocations(self, GVT, activities, horizon):
        """
        First requests the relocator for relocations to perform, and afterwards actually perform them.

        :param GVT: the current GVT
        :param activities: list containing all activities of all nodes
        :param horizon: the horizon used in this activity tracking
        """
        # Now start moving all models according to the provided relocation directives
        relocate = self.relocator.getRelocations(GVT, activities, horizon)

        if relocate:
            self.performRelocationsInit(relocate)

    def performRelocationsInit(self, relocate):
        """
        Perform the relocations specified in the parameter. Split of from the 'findAndPerformRelocations', to make it possible for other parts of the code
        to perform relocations too.

        :param relocate: dictionary containing the model_id as key and the value is the node to send it to
        """
        relocate = {key: relocate[key] for key in relocate if self.model_ids[key].location != relocate[key] and self.model_ids[key].relocatable}
        if not relocate:
            return

        if self.runningIrreversible is not None:
            self.getProxy(self.runningIrreversible).unsetIrreversible()
            self.runningIrreversible = None

        while not self.noFinishRing.acquire(False):
            if not self.runGVT:
                self.GVTdone()
                return
            time.sleep(0)

        kernels = {}
        self.locked_kernels = set()
        relocation_rules = {}
        for model_id in relocate:
            source = self.model_ids[model_id].location
            destination = relocate[model_id]
            if source == destination:
                continue
            kernels[source] = kernels.get(source, 0) + 1
            kernels[destination] = kernels.get(destination, 0) + 1
            if kernels[source] == 1:
                # We are the first to lock it, so actually send the lock
                self.getProxy(source).requestMigrationLock()
            if kernels[destination] == 1:
                # We are the first to lock it, so actually send the lock
                self.getProxy(destination).requestMigrationLock()
            relocation_rules.setdefault((source, destination), set()).add(model_id)
        while relocation_rules:
            # Busy loop until everything is done
            # Don't use an iterator, as we will change the list
            for source, destination in list(relocation_rules.keys()):
                if source in self.locked_kernels and destination in self.locked_kernels:
                    models = relocation_rules[(source, destination)]
                    self.getProxy(source).migrateTo(destination, models)
                    del relocation_rules[(source, destination)]
                    kernels[source] -= len(models)
                    kernels[destination] -= len(models)
                    if kernels[source] == 0:
                        self.getProxy(source).migrationUnlock()
                    if kernels[destination] == 0:
                        self.getProxy(destination).migrationUnlock()
        # OK, now check whether we need to visualize all locations or not
        if self.locationCellView:
            visualizeLocations(self)

        # Possibly some node is now hosting all models, so allow this node to become irreversible for some time.
        self.checkForTemporaryIrreversible()

        # Allow the finishring algorithm again
        self.noFinishRing.release()

    def checkForTemporaryIrreversible(self):
        """
        Checks if one node is hosting all the models. If this is the case, this node will gain 'temporary irreversibility',
        allowing it to skip state saving and thus avoiding the main overhead associated with time warp.
        """
        # Check whether or not everything is located at a single node now
        if self.relocator.useLastStateOnly():
            # If this is the case, we will be unable to know which state to save the activity for
            # So disable it for now
            # This does offer a slight negative impact, though it isn't really worth fixing for the time being
            return
        currentKernel = self.destinations[0] if isinstance(self.destinations[0], int) else 0
        for kernel in self.destinations:
            if isinstance(kernel, int):
                loc = kernel
            else:
                loc = 0
            if loc != currentKernel:
                break
        else:
            # We did'nt break, so one of the nodes runs all at once
            self.getProxy(currentKernel).setIrreversible()
            self.runningIrreversible = currentKernel

    def notifyLocked(self, remote):
        """
        Notify this kernel that the model is locked

        :param remote: the node that is locked
        """
        self.locked_kernels.add(remote)

    def dsRemovePort(self, port):
        """
        Remove a port from the simulation

        :param port: the port to remove
        """
        self.model.undoDirectConnect()
        for iport in port.inLine:
            iport.outLine = [p for p in iport.outLine if p != port]
        for oport in port.outLine:
            oport.outLine = [p for p in oport.inLine if p != port]

    def dsUnscheduleModel(self, model):
        """
        Dynamic Structure change: remove an existing model

        :param model: the model to remove
        """
        self.model.undoDirectConnect()
        if isinstance(model, CoupledDEVS):
            for m in model.componentSet:
                self.dsUnscheduleModel(m, False)
            for port in model.IPorts:
                self.dsRemovePort(port)
            for port in model.OPorts:
                self.dsRemovePort(port)
        elif isinstance(model, AtomicDEVS):
            self.model.componentSet.remove(model)
            self.model.models.remove(model)
            # The model is removed, so remove it from the scheduler
            self.model.scheduler.unschedule(model)
            self.model_ids[model.model_id] = None
            self.destinations[model.model_id] = None
            self.model.local_model_ids.remove(model.model_id)
            for port in model.IPorts:
                self.dsRemovePort(port)
            for port in model.OPorts:
                self.dsRemovePort(port)
        else:
            raise DEVSException("Unknown model to schedule: " + str(model))

    def dsScheduleModel(self, model):
        """
        Dynamic Structure change: create a new model

        :param model: the model to add
        """
        self.model.undoDirectConnect()
        if isinstance(model, CoupledDEVS):
            model.fullName = model.parent.fullName + "." + model.getModelName()
            for m in model.componentSet:
                self.dsScheduleModel(m)
        elif isinstance(model, AtomicDEVS):
            model.model_id = len(self.model_ids)
            model.fullName = model.parent.fullName + "." + model.getModelName()
            model.location = self.name
            self.model_ids.append(model)
            self.destinations.append(model)
            self.model.componentSet.append(model)
            self.model.models.append(model)
            self.model.local_model_ids.add(model.model_id)
            model.elapsed = self.currentclock[0]
            self.atomicInit(model)
            p = model.parent
            model.selectHierarchy = [model]
            while p != None:
                model.selectHierarchy = [p] + model.selectHierarchy
                p = p.parent
            if model.timeNext[0] == self.currentclock[0]:
                # If scheduled for 'now', update the age manually
                model.timeNext = (model.timeNext[0], self.currentclock[1])
            # It is a new model, so add it to the scheduler too
            self.model.scheduler.schedule(model)
        else:
            raise DEVSException("Unknown model to schedule: " + str(model))

    def setRealTime(self, subsystem, generatorfile, ports, scale, args=[]):
        """
        Set the use of realtime simulation

        :param subsystem: defines the subsystem to use
        :param generatorfile: filename to use for generating external inputs
        :param ports: input port references
        :param scale: the scale factor for realtime simulation
        :param args: additional arguments for the realtime backend
        """
        self.realtime = True
        from .threadingBackend import ThreadingBackend
        self.threadingBackend = ThreadingBackend(subsystem, args)
        from .asynchronousComboGenerator import AsynchronousComboGenerator
        self.asynchronousGenerator = AsynchronousComboGenerator(generatorfile, self.threadingBackend, scale)
        self.realtime_starttime = time.time()
        self.portmap = ports
        self.realtimeScale = scale

    def gameLoop(self):
        """
        Perform all computations up to the current time. Only applicable for the game loop realtime backend.
        """
        self.threadingBackend.step()

    def realtimeInterrupt(self, string):
        """
        Create an interrupt from other Python code instead of using stdin or the file

        :param string: the value to inject
        """
        self.threadingBackend.interrupt(string)

    def stateChange(self, model_id, variable, value):
        """
        TODO
        """
        self.tracers.tracesUser(self.prev_termination_time, self.model_ids[model_id], variable, value)
