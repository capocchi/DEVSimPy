# -*- coding: Latin-1 -*-
"""
Main simulator class to be used as an interface to the user
"""

from . import middleware

# Fetch the rank and size of this simulation run
# Don't get it ourself (e.g. from MPI), as we are possibly not using MPI
nested = False
wasMain = False
rank, size = middleware.startupMiddleware()

from .util import *
from .DEVS import *
from .basesimulator import *

from .server import *

from .logger import *

import threading
import time
import os

# Try loading cPickle as it is faster, though otherwise fall back to normal pickling
try:
    import pickle as pickle
except ImportError:
    import pickle

# For Python2 and Python3 compliance
try:
    import queue as Queue
except ImportError:
    import queue as Queue

def local(sim):
    """
    Test whether or not the simulation is done locally

    :param sim: the simulator with the locations
    :returns: bool -- whether or not the simulation is local
    """
    if len(sim.locations) == 0:
        raise DEVSException("There are no Atomic DEVS models present in your provided model")
    return sim.server.size == 1

def loadCheckpoint(name):
    """
    Load a previously created simulation from a saved checkpoint.

    :param name: the name of the model to provide some distinction between different simulation models
    :returns: either None if no recovery was possible, or the Simulator object after simulation
    """
    listdir = os.listdir('.')
    if str(name) + "_SIM.pdc" not in listdir:
        # Simulator object not even found, don't bother continueing
        #assert info("Not even a SIM file was found for the requested name, giving up already")
        return
    try:
        infile = open("%s_SIM.pdc" % (name), 'r')
        simulator = pickle.load(infile)
        infile.close()
    except:
        return
    # Use an rsplit, as it is possible that the user defined name contains _ too
    files = [f for f in listdir if (f.endswith(".pdc")) and not (f.endswith("SIM.pdc")) and (f.rsplit('_', 2)[0] == name)]
    if len(files) == 0:
        return
    #assert debug("Got matching files: " + str(files))
    maxGVT = 0
    nodes = middleware.COMM_WORLD.Get_size()
    noncomplete_checkpoint = True
    foundFiles = {}
    foundGVTs = []
    for f in files:
        gvt = float(f.split('_')[-2])
        if gvt in foundFiles:
            foundFiles[gvt].append(f)
        else:
            foundFiles[gvt] = [f]
            foundGVTs.append(gvt)
    foundGVTs.sort()
    gvt = 0
    # Construct a temporary server
    from .middleware import COMM_WORLD
    server = Server(middleware.COMM_WORLD.Get_rank(), middleware.COMM_WORLD.Get_size())
    while len(foundGVTs) > 0:
        gvt = foundGVTs[-1]
        if len(foundFiles[gvt]) < nodes:
            foundGVTs.pop()
            gvt = 0
        else:
            if gvt == 0:
                return None
            for rank in range(server.size):
                if not server.getProxy(rank).checkLoadCheckpoint(name, gvt):
                    # One of the proxies denied, try next
                    foundGVTs.pop()
                    gvt = 0
                    break
            if gvt != 0:
                # If we got here, we are done and can load it
                break
    if gvt == 0:
        #raise DEVSException("All currently present pdc files are unusable, please remove them all to force a fresh simulation run!")
        if COMM_WORLD.Get_size() > 1:
            # We need to shut down the already started MPI server...
            COMM_WORLD.isend(0, dest=0, tag=0)
        return None
    simulator.server = server

    for rank in range(server.size):
        server.getProxy(rank).loadCheckpoint(name, gvt)
    #assert info("Recovering from time " + str(gvt))
    simulator.loadCheckpoint()
    return simulator

class Simulator(object):
    """
    Associates a hierarchical DEVS model with the simulation engine.
    """
    def __init__(self, model):
        """
        Constructor of the simulator.

        :param model: a valid model (created with the provided functions)
        """
        from .simconfig import SimulatorConfiguration
        self.config = SimulatorConfiguration(self)

        from .middleware import COMM_WORLD
        # Simulator is always started at the controller
        self.server = Server(0, size)

        self.model = model

        global nested
        global wasMain
        if nested:
            wasMain = False
        else:
            nested = True
            wasMain = True
        # Initialize all options
        self.initDone = False
        self.runGVT = True
        self.callbacks = []
        self.termination_models = set()
        self.fetchAll = False
        self.tracers = []
        self.cell = False
        self.x_size = None
        self.y_size = None
        self.cell_file = "celldevstrace.txt"
        self.cell_multifile = False
        self.termination_time = float('inf')
        self.termination_condition = None
        self.address = ('localhost', 514)
        import logging
        self.loglevel = logging.DEBUG
        self.CHK_interval = -1
        self.CHK_name = "(none)"
        self.GVT_interval = 1
        self.state_saving = 2
        self.msgCopy = 0
        self.realtime = False
        self.realTimeInputPortReferences = {}
        self.subsystem = "python"
        self.generatorfile = None
        self.relocations = []
        self.progress = False
        self.drawModel = False
        self.hideEdgeLabels = False
        self.setup = False
        self.allowLocalReinit = False
        self.modifyValues = {}
        self.modifyStateValues = {}
        self.activityTracking = False
        self.activityVisualisation = False
        self.locationCellView = False
        self.sortOnActivity = False
        from .manualRelocator import ManualRelocator
        self.activityRelocator = ManualRelocator()
        self.dsdevs = False
        self.memoization = False
        self.classicDEVS = False
        self.setSchedulerActivityHeap()
        self.locationsFile = None
        self.allocator = None
        self.realtime_extra = []

        self.model_ids = []
        self.locations = defaultdict(list)
        self.model.finalize(name="", model_counter=0, model_ids=self.model_ids, locations=self.locations, selectHierarchy=[])

        # Allow the model to provide some of its own configuration
        self.model.simSettings(self)

    def __getattr__(self, func):
        """
        Get the specified attribute, all setters/registers will be redirected to the configuration code.

        :param func: function that is called
        :returns: requested attribute
        """
        if func.startswith("set") or func.startswith("register"):
            # Redirect to configuration backend
            return getattr(self.config, func)
        else:
            # Just an unknown attribute
            raise AttributeError()

    def runStartup(self):
        """
        Perform startup of the simulator right before simulation
        """
        self.startAllocator()

        # Controller is the main simulation server
        # Remap every mandatory model to the controller
        for model_id in self.termination_models:
            model = self.model_ids[model_id]
            self.locations[model.location].remove(model_id)
            self.locations[0].append(model_id)
            model.location = 0
            model.relocatable = False

        # Code without location goes to the controller
        # Delay this code as auto allocation could be possible
        for model_id in self.locations[None]:
            # All these models are not yet initialized, so set them to the default
            self.model_ids[model_id].location = 0
        self.locations[0].extend(self.locations[None])
        del self.locations[None]

        self.controller = self.server.getProxy(0)

        if self.drawModel:
            #assert info("Drawing model hierarchy")
            out = open(self.drawModelFile, 'w')
            out.write("digraph G {\n")
            self.drawModelHierarchy(out, self.model)

        if isinstance(self.model, CoupledDEVS):
            self.model.componentSet = directConnect(self.model.componentSet, local(self))
        elif isinstance(self.model, AtomicDEVS):
            for p in self.model.IPorts:
                p.routingInLine = []
                p.routingOutLine = []
            for p in self.model.OPorts:
                p.routingInLine = []
                p.routingOutLine = []
        else:
            raise DEVSException("Unkown model being simulated")

        if self.allocator is not None and self.allocator.getTerminationTime() == 0.0:
            # It is a static allocator, so this can be done right now!
            allocs = self.allocator.allocate(self.model.componentSet, None, self.server.size, None)
            for model_id, location in list(allocs.items()):
                self.model_ids[model_id].location = location
            saveLocations("locationsave.txt", allocs, self.model_ids)
            self.allocator = None

        if self.drawModel and self.allocator is None:
            out = open(self.drawModelFile, 'a')
            self.drawModelConnections(out, self.model, None)
            out.write("}")
            self.drawModel = False

        nodes = len(list(self.locations.keys()))
        if None in self.locations:
            nodes -= 1
        if nodes < self.server.size:
            # Less locations used than there exist
            #assert warn("Not all initialized MPI nodes are being used in the model setup! Auto allocation could fix this.")
            pass
        elif nodes > self.server.size:
            raise DEVSException("Not enough MPI nodes started for the distribution given in the model! Models requested at location %i, max node = %i" % (max(self.locations.keys()), self.server.size - 1))

    def drawModelHierarchy(self, outfile, model):
        """
        Draws the hierarchy by creating a Graphviz Dot file. This merely creates the first part: the hierarchy of all models

        :param outfile: a file handle to write text to
        :param model: the model to draw
        """
        from .colors import colors
        if isinstance(model, CoupledDEVS):
            outfile.write('  subgraph "cluster%s" {\n' % (model.getModelFullName()))
            outfile.write('  label = "%s"\n' % model.getModelName())
            outfile.write('  color=black\n')
            for m in model.componentSet:
                self.drawModelHierarchy(outfile, m)
            outfile.write('  }\n')
        elif isinstance(model, AtomicDEVS):
            if model.location >= len(colors):
                #assert warn("Not enough colors supplied in colors.py for this number of nodes! Defaulting to white")
                color = "white"
            else:
                color = colors[model.location]
            outfile.write('  "%s" [\n    label = "%s\\nState: %s"\n    color="%s"\n    style=filled\n]\n' % (model.getModelFullName(), model.getModelName(), model.state, color))

    def drawModelConnections(self, outfile, model, colors=None):
        """
        Draws all necessary connections between the model

        :param outfile: the file to output to
        :param model: a CoupledDEVS model whose children should be drawn
        :param colors: the colors to draw on the connections. Only used when an initial allocator is used.
        """
        if colors is not None:
            maxEvents = 0
            for i in colors:
                for j in colors[i]:
                    if colors[i][j] > maxEvents:
                        maxEvents = colors[i][j]
        for source in model.componentSet:
            for sourcePort in source.OPorts:
                for destinationPort, _ in sourcePort.routingOutLine:
                    destination = destinationPort.hostDEVS
                    if colors is not None:
                        #TODO color is not yet perfect
                        try:
                            absoluteColor = colors[source][destination]
                            relativeColor = '"%s 1 1"' % (1/(absoluteColor / float(3*maxEvents)))
                        except KeyError:
                            # Simply no message transfer
                            absoluteColor = 0
                            relativeColor = '"1 1 1"'
                    outfile.write('  "%s" -> "%s" ' % (source.getModelFullName(), destination.getModelFullName()))
                    if self.hideEdgeLabels and colors is None:
                        outfile.write(';\n')
                    elif self.hideEdgeLabels and colors is not None:
                        outfile.write('[label="%s",color=%s];\n' % (absoluteColor, relativeColor))
                    elif not self.hideEdgeLabels and colors is None:
                        outfile.write('[label="%s -> %s"];\n' % (sourcePort.getPortName(), destinationPort.getPortName()))
                    elif not self.hideEdgeLabels and colors is not None:
                        outfile.write('[label="%s -> %s (%s)",color=%s];\n' % (sourcePort.getPortName(), destinationPort.getPortName(), absoluteColor, relativeColor))

    def checkpoint(self):
        """
        Create a checkpoint of this object
        """
        outfile = open(str(self.CHK_name) + "_SIM.pdc", 'w')
        if self.flattened:
            self.model.flattenConnections()
        pickle.dump(self, outfile)
        if self.flattened:
            self.model.unflattenConnections()

    def loadCheckpoint(self):
        """
        Alert the Simulator that it was restored from a checkpoint and thus can take some shortcuts
        """
        self.controller = self.server.getProxy(0)
        self.real_simulate()

    def startAllocator(self):
        """
        Set the use of an allocator if required, thus forcing all models to run at the controller
        """
        if self.allocator is not None:
            self.activityTracking = True
            # Make simulation local for event capturing
            for model in self.model.componentSet:
                model.setLocation(0, force=True)

    def loadLocationsFromFile(self, filename):
        """
        Try to load a file containing the allocation of the nodes. If such a (valid) file is found, True is returned. Otherwise False is returned.

        This can thus easily be used in a simulator experiment file as a condition for setting an allocator (e.g. check for an allocation file and if
        none is found, create one by running the allocator first).

        A partially valid file will not be used; a file does not need to specify an allocation for all models, those that aren't mentioned are simply
        skipped and their default allocation is used (as specified in the model itself).

        :param filename: the name of the file to use
        :returns: bool -- success of the operation
        """
        try:
            f = open(filename, 'r')
            locs = {}
            for line in f:
                model_id, location, modelname = line.split(" ", 2)
                model_id, location, modelname = int(model_id), int(location), modelname[:-1]
                # Check for compliance first, otherwise the locations are loaded partially
                if self.model_ids[model_id].getModelFullName() != modelname:
                    return False
                else:
                    locs[model_id] = location
            f.close()

            # Everything seems to be fine, so do the actual allocations now
            for model_id in locs:
                self.model_ids[model_id].location = locs[model_id]
            return True
        except:
            return False

    def reinit(self):
        """
        TODO
        """
        loclist = list(range(self.server.size))
        proxylist = [self.server.getProxy(location) for location in loclist]
        # Send to very model to clear the simulation memory
        if not self.allowLocalReinit and len(proxylist) == 1:
            raise DEVSException("Reinitialisation for local simulation is disabled by default, please enable it with the configuration method 'setAllowLocalReinit()'")
        for i, proxy in enumerate(proxylist):
            proxy.resetSimulation(self.schedulerLocations[i])

    def modifyState(self, model_id, state):
        """
        TODO
        """
        self.server.getProxy(self.model_ids[model_id].location).setAttr(model_id, "state", state)
        self.controller.stateChange(model_id, "model.state", state)

    def modifyStateAttr(self, model_id, attr, value):
        """
        TODO
        """
        self.server.getProxy(self.model_ids[model_id].location).setStateAttr(model_id, attr, value)
        self.controller.stateChange(model_id, "model.state.%s" % attr, value)

    def modifyAttributes(self, model_id, attr, value):
        """
        TODO
        """
        for dst in range(self.server.size):
            self.server.getProxy(dst).setAttr(model_id, attr, value)
        self.controller.stateChange(model_id, "model.%s" % attr, value)

    def simulate(self):
        """
        Start simulation with the previously set options. Can be reran afterwards to reinitialize the model and run it again,
        possibly after altering some aspects of the model with the provided methods.
        """
        loclist = list(range(self.server.size))
        proxylist = [self.server.getProxy(location) for location in loclist]

        if not self.setup:
            self.runStartup()
            self.relocations.sort()

            for directive in self.relocations:
                if directive[1] in self.termination_models:
                    raise DEVSException("Termination model was found as a relocation directive!")

            # self.locations is now untrusted, as it is possible for migration to happen!
            del self.locations

            # Broadcast the model, do this slightly more intelligent than by iterating over the list by using provided functions and exploiting maximal parallellism
            self.flattened = False
            # Fill in all schedulers
            for location in loclist:
                if location not in self.schedulerLocations:
                    self.schedulerLocations[location] = self.schedulerType
            try:
                # Try broadcasting as-is
                broadcastModel((self.model, self.model_ids, self.flattened), proxylist, self.allowLocalReinit, self.schedulerLocations)
                self.flattened = False
            except RuntimeError:
                # Something went wrong, probably exceeded the maximum recursion depth while pickling
                #assert warn("Normal sending not possible due to big recursion, trying auto flattening")
                try:
                    # Try decoupling the ports from the actual models to limit recursion that our simulation framework induced
                    self.model.flattenConnections()
                    # Broadcast again, but now mention that the ports were altered
                    self.flattened = True
                    broadcastModel((self.model, self.model_ids, self.flattened), proxylist, self.allowLocalReinit, self.schedulerLocations)
                except RuntimeError as e:
                    # Even that didn't solve it, user error!
                    # Stop the nodes from waiting for a broadcast
                    broadcastCancel()
                    import sys
                    raise DEVSException("Could not send model to remote destination due to pickling error: " + str(e))
            # Prevent further setups
            self.setup = True

        for proxy in proxylist:
            proxy.setGlobals(
                             tracers=self.tracers,
                             address=self.address,
                             loglevel=self.loglevel,
                             checkpointfrequency=self.CHK_interval,
                             checkpointname = self.CHK_name,
                             kernels=len(loclist),
                             statesaver=self.state_saving,
                             memoization=self.memoization,
                             msgCopy=self.msgCopy)

        # Set the verbosity on the controller only, otherwise each kernel
        # would open the file itself, causing problems. Furthermore, all
        # verbose output will be sent to the controller
        self.controller.setAllocator(self.allocator)
        self.controller.setRelocator(self.activityRelocator)
        self.controller.setDSDEVS(self.dsdevs)
        self.controller.setActivityTracking(self.activityTracking)
        self.controller.setClassicDEVS(self.classicDEVS)
        self.controller.setCellLocationTracer(self.x_size, self.y_size, self.locationCellView)
        # Clear this up as we would reregister them otherwise
        self.tracers = []

        if self.realtime:
            if len(loclist) > 1:
                raise DEVSException("Real time simulation only possible locally")
            if self.subsystem == "tkinter":
                # Register a queue processing method
                tk = self.realtime_extra[0]
                import collections
                queue = collections.deque()
                from . import threadingTkInter
                tk.after(10, threadingTkInter.tkMainThreadPoller, tk, queue)
                self.realtime_extra = [queue]
                seperate_thread = True
            elif self.subsystem == "loop":
                seperate_thread = True
            else:
                seperate_thread = False
            self.controller.setRealTime(self.subsystem, self.generatorfile, self.realTimeInputPortReferences, self.realtimeScale, self.realtime_extra)
        else:
            seperate_thread = False

        # Check whether global or local termination should be used
        if self.termination_condition is not None:
            # Only set the condition on the controller
            self.server.getProxy(0).setTerminationCondition(self.termination_condition)
        else:
            # Global termination time
            for proxy in proxylist:
                proxy.setTerminationTime((self.termination_time, float('inf')))

        if self.CHK_interval > 0:
            self.checkpoint()

        if seperate_thread:

            thrd = threading.Thread(target=self.server.getProxy(0).simulate_sync)
            # Make it a daemon, as otherwise killing the main thread wouldn't kill us
            thrd.daemon = False
            thrd.start()
        else:
            self.real_simulate()

    def removeTracers(self):
        """
        TODO
        """
        loclist = list(range(self.server.size))
        proxylist = [self.server.getProxy(location) for location in loclist]
        for proxy in proxylist:
            proxy.removeTracers()

    def realtime_loop_call(self):
        """
        Perform a single iteration in the loop for real time simulation
        """
        self.controller.gameLoop()

    def realtime_interrupt(self, string):
        """
        Generate an interrupt for the realtime backend using a method call.

        :param string: the value to interrupt with, should be of the form "port value"
        """
        self.controller.realtimeInterrupt(string)

    def showProgress(self, locations):
        """
        Shows the progress of the simulation by polling all locations that are passed. Should run on a seperate thread as this blocks!

        :param locations: list of all locations to access
        """
        # 80 is somewhat default...
        consolewidth = 80
        # Delete 4 for the prefix, 5 for the suffix
        barwidth = consolewidth - 4 - 5
        finishtime = self.termination_time
        first = True
        # Local simulation is always 'committed'
        self.fillchar = "=" if len(locations) > 1 else "#"
        gvt = 0.0
        while 1:
            # Several dirty checks for whether or not the simulation is done, if it is finished no more calls should be needed
            # Keep doing this until the main thread exits, this should be a thread!
            if self.CHK_interval > -1:
                # Don't use an event while checkpointing, as this is unpicklable
                time.sleep(1)
            else:
                self.progress_event.wait(1)
            if not first:
                for _ in locations:
                    sys.stdout.write("\033[F")
            first = False
            if self.progress_finished and self.fillchar != "E":
                gvt = finishtime
            elif self.progress_finished and self.fillchar == "E":
                # Don't update the GVT variable
                if len(locations) == 1:
                    # The gvt is actually kind of the node time
                    gvt = nodetime
            else:
                gvt = max(self.controller.getGVT(), 0)
            gvtpercentage = int(gvt / finishtime * 100)
            gvtlength = min(barwidth, gvtpercentage * barwidth / 100)
            for node in locations:
                if self.progress_finished:
                    nodetime = float('inf')
                else:
                    nodetime = self.controller.getProxy(node).getTime()
                if nodetime == float('inf'):
                    nodetime = finishtime
                s = "%2d" % node
                s += " |"
                percentage = int(nodetime / finishtime * 100)
                s += "#" * gvtlength
                length = min(barwidth, percentage * barwidth / 100) - gvtlength
                s += self.fillchar * length
                s += " " * (barwidth - gvtlength - length)
                if percentage == 100 and self.fillchar != "E":
                    s += "|DONE"
                elif percentage == 100 and self.fillchar == "E":
                    s += "|FAIL"
                else:
                    s += "| %2d" % percentage + "%"
                print(s)
            if self.progress_finished:
                return

    def real_simulate(self):
        """
        The actual simulation part, this is identical for the 'start from scratch' and 'start from checkpoint' algorithm, thus it was split up
        """
        locations = list(range(self.server.size))
        try:
            ## Progress visualisation code
            if self.progress:
                if self.termination_time == float('inf'):
                    #assert warning("Progress visualisation is only possible if a termination time is used instead of a termination condition")
                    self.progress = False
                #elif self.verbose and self.verbose_file is None:
                #    #assert warning("Progress visualisation is not allowed when printing verbose output")
                #    pass
                #    self.progress = False
                else:
                    self.progress_finished = False
                    thread = threading.Thread(target=self.showProgress, args=[locations])
                    if self.CHK_interval < 0:
                        self.progress_event = threading.Event()
                    thread.start()

            # Local simulation can take a shortcut
            if len(locations) == 1:
                if self.CHK_interval > 0:
                    # If we use checkpointing, we will need a GVT thread running
                    self.controller.startGVTThread(self.GVT_interval)
                # Simply do a blocking call, thus preventing the finish ring algorithm
                self.controller.getProxy(locations[0]).simulate_sync()
            else:
                self.controller.startGVTThread(self.GVT_interval)
                for location in locations:
                    # Don't run all of these on a seperate thread, as it returns no result
                    self.controller.getProxy(location).simulate()
                # Here, the simulation is running and we wait for it to end...
                self.controller.waitFinish(len(locations))
                # It seems that all nodes have finished!
            #assert debug("Finished waiting for all processors")
        except DEVSException as e:
            print(e)
            # Should also exit on a DEVSException since this isn't really meant to happen
            import sys
            # Return an errorcode, as we ended abruptly
            sys.exit(1)
        except:
            # Try to stop the progress bar thread if this exists, otherwise we hang forever
            if self.progress:
                self.fillchar = "E"
                self.progress_finished = True
                if self.CHK_interval > -1:
                    # With checkpointing running, we need to do this the hard way...
                    self.progress_event.set()
                # Wait for it to end
                thread.join()
            # Reraise the initial exception, this code was only here to stop the progress bar :)
            raise

        # Perform all pending operations
        #assert debug("Performing all delayed actions")
        self.controller.performActions()

        # Stop all running tracers
        #assert debug("Stopping all tracers")
        self.controller.stopTracers()

        # Now the state is stable, fetch all registered states before shutting down
        #assert debug("Fetching all requested states")
        if len(self.callbacks) > 0:
            for variable, model_id in self.callbacks:
                # Ask the controller on which node this model currently runs, calls to the controller
                # are very fast, as this runs locally. Otherwise a complete location dictionary would
                # have to be pickled and unpickled, but also filtered for local models, begin O(n) instead
                # of the current O(1), at the cost of more function calls
                state = self.controller.getProxy(self.controller.getLocation(model_id)).getState(model_id)
                #assert debug("Setting state for " + str(variable))
                setattr(self, variable, state)

        if self.fetchAll:
            #assert info("Downloading model from locations")
            # We must download the state from each and every model
            for model in self.model.componentSet:
                model.state = self.controller.getProxy(self.controller.getLocation(model.model_id)).getState(model.model_id)

        # Shut down every location
        #assert debug("Shutting down servers")
        for loc in locations:
            proxy = self.controller.getProxy(loc)
            # If this is oneway, we will stop the simulation even before the finish was called everywhere
            proxy.finish()

        self.progress_finished = True
        # A progress bar was running without checkpointing: set the event to finish it
        if self.progress and self.CHK_interval <= 0:
            self.progress_event.set()

        # Activity tracking is enabled, so visualize it in whatever way was configured
        if self.activityVisualisation:
            visualizeActivity(self)

        # Check if the model was to be visualized
        if self.drawModel:
            # Possibly include event count visualisation
            #colors = self.controller.runAllocator()
            colors = self.controller.getEventGraph()
            #assert info("Drawing model distribution")
            out = open(self.drawModelFile, 'a')
            self.drawModelConnections(out, self.model, colors)
            out.write("}")

        global wasMain
        if wasMain:
            global nested
            nested = False
