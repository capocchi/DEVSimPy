# Copyright 2014 Modelling, Simulation and Design Lab (MSDL) at 
# McGill University and the University of Antwerp (http://msdl.cs.mcgill.ca/)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Controller used as a specific simulation kernel
"""
from pypdevs.basesimulator import BaseSimulator
from pypdevs.logger import *
import threading
import pypdevs.accurate_time as time
import pypdevs.middleware as middleware
from pypdevs.DEVS import CoupledDEVS, AtomicDEVS
from pypdevs.util import DEVSException
from pypdevs.activityVisualisation import visualizeLocations
from pypdevs.realtime.threadingBackend import ThreadingBackend
from pypdevs.realtime.asynchronousComboGenerator import AsynchronousComboGenerator

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
        :param server: the server to make requests on
        """
        BaseSimulator.__init__(self, name, model, server)
        self.waiting_lock = threading.Lock()
        self.accumulator = {}
        self.no_finish_ring = threading.Lock()
        self.no_finish_ring.acquire()
        self.location_cell_view = False
        self.graph = None
        self.allocations = None
        self.running_irreversible = None
        self.initial_allocator = None
        self.prev_termination_time = 0.0

    def __setstate__(self, retdict):
        """
        For pickling

        :param retdict: dictionary containing attributes and their value
        """
        BaseSimulator.__setstate__(self, retdict)
        self.waiting_lock = threading.Lock()
        self.no_finish_ring = threading.Lock()
        self.no_finish_ring.acquire()

    def GVTdone(self):
        """
        Notify this simulation kernel that the GVT calculation is finished
        """
        self.wait_for_gvt.set()

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
        # It seems that we should be finished, so just ACK this with every simulation kernel before proceeding
        #   it might be possible that the kernel's 'notifyRun' command is still on the way, making the simulation
        #   stop too soon.
        self.no_finish_ring.acquire()
        msgcount = self.finishRing(0, 0, True)
        if msgcount == -1:
            # One of the nodes was still busy
            self.no_finish_ring.release()
            return False
        else:
            msgcount2 = self.finishRing(0, 0, True)
            # If they are equal, we are done
            ret = msgcount == msgcount2
            if not ret:
                self.no_finish_ring.release()
            else:
                self.waiting = 0
            return ret

    def waitFinish(self, running):
        """
        Wait until the specified number of kernels have all told that simulation
        finished.

        :param running: the number of kernels that is simulating
        """
        while 1:
            time.sleep(1)
            # Make sure that no relocations are running
            if self.isFinished(running):
                # All simulation kernels have told us that they are idle at the moment
                break
        self.run_gvt = False
        self.event_gvt.set()
        self.gvt_thread.join()

    def startGVTThread(self, gvt_interval):
        """
        Start the GVT thread

        :param gvt_interval: the interval between two successive GVT runs
        """
        # We seem to be the controller
        # Start up the GVT algorithm then
        self.event_gvt = threading.Event()
        self.run_gvt = True
        self.gvt_thread = threading.Thread(target=Controller.threadGVT,
                                          args=[self, gvt_interval])
        self.gvt_thread.daemon = True
        self.gvt_thread.start()

    def threadGVT(self, freq):
        """
        Run the GVT algorithm, this method should be called in its own thread,
        because it will block

        :param freq: the time to sleep between two GVT calculations
        """
        # Wait for the simulation to have done something useful before we start
        self.event_gvt.wait(freq)
        # Maybe simulation already finished...
        while self.run_gvt:
            self.receiveControl([float('inf'), 
                                 float('inf'), 
                                 self.accumulator, 
                                 {}], 
                                True)
            # Wait until the lock is released elsewhere
            print("Waiting for clear")
            self.wait_for_gvt.wait()
            self.wait_for_gvt.clear()
            # Limit the GVT algorithm, otherwise this will flood the ring
            print("Cleared")
            self.event_gvt.wait(freq)

    def getVCDVariables(self):
        """
        Generate a list of all variables that exist in the current scope

        :returns: list -- all VCD variables in the current scope
        """
        variables = []
        for d in self.total_model.component_set:
            variables.extend(d.getVCDVariables())
        return variables

    def simulate_sync(self):
        """
        Synchronous simulation call, identical to the normal call, with the exception that it will be a blocking call as only "simulate" is marked as oneway.
        """
        BaseSimulator.simulate_sync(self)
        self.no_finish_ring.acquire()

    def simulate(self):
        """
        Run the actual simulation on the controller. This will simply 'intercept' the call to the original simulate and perform location visualisation when necessary.
        """
        self.checkForTemporaryIrreversible()
        self.no_finish_ring.release()
        if self.location_cell_view:
            from pypdevs.activityVisualisation import visualizeLocations
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
            if self.initial_allocator is None:
                # No allocator was defined, or it has already issued its allocation code, which resulted into 'nothing'
                self.graph = None
                self.allocations = None
            else:
                from pypdevs.util import constructGraph, saveLocations
                self.graph = constructGraph(self.model)
                allocs = self.initialAllocator.allocate(self.model.component_set,
                                                        self.getEventGraph(),
                                                        self.kernels,
                                                        self.total_activities)
                self.allocations = allocs
                self.initial_allocator = None
                saveLocations("locationsave.txt", 
                              self.allocations, 
                              self.model_ids)
        return self.graph, self.allocations

    def setCellLocationTracer(self, x, y, location_cell_view):
        """
        Sets the Location tracer and all its configuration parameters

        :param x: the horizontal size of the grid
        :param y: the vertical size of the grid
        :param location_cell_view: whether or not to enable it
        """
        self.x_size = x
        self.y_size = y
        self.location_cell_view = location_cell_view

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
        self.activity_tracking = at

    def setClassicDEVS(self, classic_DEVS):
        """
        Sets the use of Classic DEVS instead of Parallel DEVS.

        :param classicDEVS: whether or not to use Classic DEVS
        """
        # Do this once, to prevent checks for the classic DEVS formalism
        if classic_DEVS:
            # Methods, so CamelCase
            self.coupledOutputGeneration = self.coupledOutputGenerationClassic

    def setAllocator(self, initial_allocator):
        """
        Sets the use of an initial relocator.

        :param initial_allocator: whether or not to use an initial allocator
        """
        self.initial_allocator = initial_allocator
        if initial_allocator is not None:
            # Methods, so CamelCase
            self.atomicOutputGeneration_backup = self.atomicOutputGeneration
            self.atomicOutputGeneration = self.atomicOutputGenerationEventTracing

    def setDSDEVS(self, dsdevs):
        """
        Whether or not to check for DSDEVS events

        :param dsdevs: dsdevs boolean
        """
        self.use_DSDEVS = dsdevs

    def setRealtime(self, input_references):
        """
        Sets the use of realtime simulation.

        :param input_references: dictionary containing the string to port mapping
        """
        self.realtime = True
        self.realtime_port_references = input_references

    def setTerminationCondition(self, termination_condition):
        """
        Sets the termination condition of this simulation kernel.
    
        As soon as the condition is valid, it willl signal all nodes that they have to stop simulation as soon as they have progressed up to this simulation time.

        :param termination_condition: a function that accepts two parameters: *time* and *model*. Function returns whether or not to halt simulation
        """
        self.termination_condition = termination_condition
        self.termination_time_check = False

    def findAndPerformRelocations(self, gvt, activities, horizon):
        """
        First requests the relocator for relocations to perform, and afterwards actually perform them.

        :param gvt: the current GVT
        :param activities: list containing all activities of all nodes
        :param horizon: the horizon used in this activity tracking
        """
        # Now start moving all models according to the provided relocation directives
        relocate = self.relocator.getRelocations(gvt, activities, horizon)
        #print("Filtered relocate: " + str(relocate))

        if relocate:
            self.performRelocationsInit(relocate)

    def performRelocationsInit(self, relocate):
        """
        Perform the relocations specified in the parameter. Split of from the 'findAndPerformRelocations', to make it possible for other parts of the code
        to perform relocations too.

        :param relocate: dictionary containing the model_id as key and the value is the node to send it to
        """
        relocate = {key: relocate[key] 
                for key in relocate 
                if self.model_ids[key].location != relocate[key] and 
                        self.model_ids[key].relocatable}
        if not relocate:
            return

        if self.running_irreversible is not None:
            self.getProxy(self.running_irreversible).unsetIrreversible()
            self.running_irreversible = None

        while not self.no_finish_ring.acquire(False):
            if not self.run_gvt:
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
                if (source in self.locked_kernels and 
                        destination in self.locked_kernels):
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
        if self.location_cell_view:
            visualizeLocations(self)

        # Possibly some node is now hosting all models, so allow this node to become irreversible for some time.
        self.checkForTemporaryIrreversible()

        # Allow the finishring algorithm again
        self.no_finish_ring.release()

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
        if isinstance(self.destinations[0], int):
            current_kernel = self.destinations[0]
        else:
            current_kernel = 0
        for kernel in self.destinations:
            if isinstance(kernel, int):
                loc = kernel
            else:
                loc = 0
            if loc != current_kernel:
                break
        else:
            # We didn't break, so one of the nodes runs all at once
            self.getProxy(current_kernel).setIrreversible()
            self.running_irreversible = current_kernel

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
        for iport in port.inline:
            iport.outline = [p for p in iport.outline if p != port]

        for oport in port.outline:
            oport.inline = [p for p in oport.inline if p != port]

        self.dc_altered.add(port)

    def dsDisconnectPorts(self, p1, p2):
        """
        Disconnect two ports

        :param p1: source port
        :param p2: target port
        """
        self.dc_altered.add(p1)

    def dsConnectPorts(self, p1, p2):
        """
        Connect two ports

        :param p1: source port
        :param p2: target port
        """
        self.dc_altered.add(p1)

    def dsUnscheduleModel(self, model):
        """
        Dynamic Structure change: remove an existing model

        :param model: the model to remove
        """
        if isinstance(model, CoupledDEVS):
            for m in model.component_set:
                self.dsUnscheduleModel(m, False)
            for port in model.IPorts:
                self.dsRemovePort(port)
            for port in model.OPorts:
                self.dsRemovePort(port)
        elif isinstance(model, AtomicDEVS):
            self.model.component_set.remove(model)
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
            raise DEVSException("Unknown model to schedule: %s" % model)

    def dsScheduleModel(self, model):
        """
        Dynamic Structure change: create a new model

        :param model: the model to add
        """
        if isinstance(model, CoupledDEVS):
            model.full_name = model.parent.full_name + "." + model.getModelName()
            for m in model.component_set:
                self.dsScheduleModel(m)
            for p in model.IPorts:
                self.dc_altered.add(p)
            for p in model.OPorts:
                self.dc_altered.add(p)
        elif isinstance(model, AtomicDEVS):
            model.model_id = len(self.model_ids)
            model.full_name = model.parent.full_name + "." + model.getModelName()
            model.location = self.name
            self.model_ids.append(model)
            self.destinations.append(model)
            self.model.component_set.append(model)
            self.model.models.append(model)
            self.model.local_model_ids.add(model.model_id)
            self.atomicInit(model, self.current_clock)
            p = model.parent
            model.select_hierarchy = [model]
            while p != None:
                model.select_hierarchy = [p] + model.select_hierarchy
                p = p.parent
            if model.time_next[0] == self.current_clock[0]:
                # If scheduled for 'now', update the age manually
                model.time_next = (model.time_next[0], self.current_clock[1])
            # It is a new model, so add it to the scheduler too
            self.model.scheduler.schedule(model)
            for p in model.IPorts:
                self.dc_altered.add(p)
            for p in model.OPorts:
                self.dc_altered.add(p)
        else:
            raise DEVSException("Unknown model to schedule: %s" % model)

    def setRealTime(self, subsystem, generator_file, ports, scale, listeners, args=[]):
        """
        Set the use of realtime simulation

        :param subsystem: defines the subsystem to use
        :param generator_file: filename to use for generating external inputs
        :param ports: input port references
        :param scale: the scale factor for realtime simulation
        :param listeners: the ports on which we should listen for output
        :param args: additional arguments for the realtime backend
        """
        self.realtime = True
        self.threading_backend = ThreadingBackend(subsystem, args)
        self.rt_zerotime = time.time()
        async = AsynchronousComboGenerator(generator_file, self.threading_backend)
        self.asynchronous_generator = async
        self.realtime_starttime = time.time()
        self.portmap = ports
        self.model.listeners = listeners
        self.realtime_scale = scale

    def gameLoop(self):
        """
        Perform all computations up to the current time. Only applicable for the game loop realtime backend.
        """
        self.threading_backend.step()

    def realtimeInterrupt(self, string):
        """
        Create an interrupt from other Python code instead of using stdin or the file

        :param string: the value to inject
        """
        self.threading_backend.interrupt(string)

    def stateChange(self, model_id, variable, value):
        """
        Notification function for when a variable's value is altered. It will notify the node that is responsible for simulation of this model AND also notify the tracers of the event.

        :param model_id: the model_id of the model whose variable was changed
        :param variable: the name of the variable that was changed (as a string)
        :param value: the new value of the variable
        """
        # Call the node that hosts this model and order it to recompute timeAdvance
        proxy = self.getProxy(self.model_ids[model_id].location)
        proxy.recomputeTA(model_id, self.prev_termination_time)
        self.tracers.tracesUser(self.prev_termination_time, 
                                self.model_ids[model_id], 
                                variable, 
                                value)
