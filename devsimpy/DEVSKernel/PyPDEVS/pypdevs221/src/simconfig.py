"""
Module with the specific aim of creating a more simple configuration interface for the simulator.
"""
from . import middleware
from .util import DEVSException
from .DEVS import CoupledDEVS, AtomicDEVS

def local(sim):
    """
    Test whether or not the simulation is done locally

    :param sim: the simulator with the locations
    :returns: bool -- whether or not the simulation is local
    """
    if len(sim.locations) == 0:
        raise DEVSException("There are no Atomic DEVS models present in your provided model")
    return sim.server.size == 1

class SimulatorConfiguration(object):
    """
    All necessary simulator configuration options are provided. The necessary checks will be made and the simulator will be adapted accordingly.
    """
    def __init__(self, sim):
        """
        Constructor

        :param sim: the simulator to alter with actions on this configurator
        """
        self.simulator = sim

    def setClassicDEVS(self, classicDEVS=True):
        """
        Use Classic DEVS instead of Parallel DEVS. This option does not affect the use of Dynamic Structure DEVS or realtime simulation. Not usable with distributed simulation.

        :param classicDEVS: whether or not to use Classic DEVS
        """
        if not local(self.simulator) and classicDEVS:
            raise DEVSException("Classic DEVS simulations cannot be distributed!")
        self.simulator.classicDEVS = classicDEVS

    def setMemoization(self, memo=True):
        """
        Use memoization to prevent repeated int/ext/confTransition calls when revertion was performed.

        :param memo: enable or not
        """
        # Local simulation will never profit from memoization, so ignore it
        if not local(self.simulator):
            self.simulator.memoization = memo

    def setDSDEVS(self, dsdevs=True):
        """
        Whether or not to enable Dynamic Structure DEVS simulation. If this is set to True, the modelTransition method will be called on all transitioned models. 
        If this is False, the modelTransition method will not be called, even if one is defined! Enabling this incurs a (slight) slowdown in the simulation,
        due to the additional function calls and checks that have to be made. Currently only available in local simulation.

        :param dsdevs: enable or not
        """
        if local(self.simulator):
            self.simulator.dsdevs = dsdevs
        elif not dsdevs:
            raise DEVSException("Dynamic Structure DEVS is currently only available in local simulation!")

    def setAllowLocalReinit(self, allowed=True):
        """
        Allow a model to be reinitialized in local simulation.
        This is not the case by default, as it would be required to save a copy of the model in memory during setup. Generating such a copy can be time consuming and the additional memory consumption could be unacceptable.
        Distributed simulation is unaffected, since this always requires the creation of a copy.
        If this is False and reinitialisation is done in a local simulation, an exception will be thrown.

        .. warning:: The state that is accessible after the simulation will **NOT** be updated if this configuration parameter is used. If you want to have fully up to date states, you should also set the *setFetchAllAfterSimulation()* configuration parameter.

        :param allowed: whether or not to allow reinitialization
        """
        #TODO check whether or not simulation has already happened...
        self.simulator.allowLocalReinit = allowed

    def setManualRelocator(self):
        """
        Sets the use of the manual relocator (the default). This mode allows the user to add manual *relocation directives*.
        """
        self.setActivityRelocatorCustom("manualRelocator", "ManualRelocator")

    def setRelocationDirective(self, time, model, destination):
        """
        Creates a relocation directive, stating that a relocation of a certain model should happen at or after the specified time (depending on when the GVT progresses over this time).

        If multiple directives exist for the same model, the one with the highest time will be executed.

        :param time: time after which the relocation should happen
        :param model: the model to relocate at the specified time. Can either be its ID, or an AtomicDEVS or CoupledDEVS model. Note that providing a CoupledDEVS model is simply a shortcut for relocating the COMPLETE subtree elsewhere, as this does not stop at kernel boundaries.
        :param destination: the location to where the model should be moved
        """
        if not isinstance(destination, int) and not isinstance(destination, str):
            raise DEVSException("Relocation directive destination should be an integer or string")
        destination = int(destination)
        if destination not in list(range(self.simulator.server.size)):
            raise DEVSException("Relocation directive got an unknown destination, got: %s, expected one of %s" % (destination, list(range(self.simulator.server.size))))

        from .manualRelocator import ManualRelocator
        if not isinstance(self.simulator.activityRelocator, ManualRelocator):
            raise DEVSException("Relocation directives can only be set when using a manual relocator (the default)\nYou seem to have changed the relocator, so please revert it back by calling the 'setManualRelocator()' first!")

        if isinstance(model, int):
            self.simulator.activityRelocator.addDirective(time=time, model=model, destination=destination)
        elif isinstance(model, AtomicDEVS):
            self.simulator.activityRelocator.addDirective(time=time, model=model.model_id, destination=destination)
        elif isinstance(model, CoupledDEVS):
            for m in model.componentSet:
                self.simulator.setRelocationDirective(time, m, destination)

    def setRelocationDirectives(self, directives):
        """
        Sets multiple relocation directives simultaneously, easier for batch processing. Behaviour is equal to running setRelocationDirective on every element of the iterable.

        :param directives: an iterable containing all directives, in the form [time, model, destination]
        """
        for directive in directives:
            self.setRelocationDirective(directive[0], directive[1], directive[2])

    def setSchedulerCustom(self, filename, schedulerName, locations=None):
        """
        Use a custom scheduler

        :param filename: filename of the file containing the scheduler class
        :param schedulerName: class name of the scheduler contained in the file
        :param locations: if it is an iterable, the scheduler will only be applied to these locations. If it is None, all nodes will be affected.
        """
        if not isinstance(filename, str):
            raise DEVSException("Custom scheduler filename should be a string")
        if not isinstance(schedulerName, str):
            raise DEVSException("Custom scheduler classname should be a string")
        if locations is None:
            # Set global scheduler, so overwrite all previous configs
            self.simulator.schedulerType = (filename, schedulerName)
            self.simulator.schedulerLocations = {}
        else:
            # Only for a subset of models, but keep the default scheduler
            for location in locations:
                self.simulator.schedulerLocations[location] = (filename, schedulerName)

    def setSchedulerActivityHeap(self, locations=None):
        """
        Use the basic activity heap scheduler, this is the default.

        :param locations: if it is an iterable, the scheduler will only be applied to these locations. If it is None, all nodes will be affected.
        """
        self.setSchedulerCustom("schedulerAH", "SchedulerAH", locations)

    def setSchedulerPolymorphic(self, locations=None):
        """
        Use a polymorphic scheduler, which chooses at run time between the HeapSet scheduler or the Minimal List scheduler. Slight overhead due to indirection and statistics gathering.

        .. warning:: Still unstable, don't use!

        :param locations: if it is an iterable, the scheduler will only be applied to these locations. If it is None, all nodes will be affected.
        """
        self.setSchedulerCustom("schedulerAuto", "SchedulerAuto", locations)

    def setSchedulerDirtyHeap(self, locations=None):
        """
        Use the basic activity heap scheduler, but without periodic cleanup. The same scheduler as the one used in VLE.

        :param locations: if it is an iterable, the scheduler will only be applied to these locations. If it is None, all nodes will be affected.
        """
        self.setSchedulerCustom("schedulerDH", "SchedulerDH", locations)

    def setSchedulerDiscreteTime(self, locations=None):
        """
        Use a basic 'discrete time' style scheduler. If the model is scheduled, it has to be at the same time as all other scheduled models. It isn't really discrete time in the sense that it allows variable step sizes, only should ALL models agree on it.

        :param locations: if it is an iterable, the scheduler will only be applied to these locations. If it is None, all nodes will be affected.

        .. warning:: Only use in local simulation!
        """
        if not local(self):
            raise DEVSException("Do not use this scheduler for distributed simulation")
        self.setSchedulerCustom("schedulerDT", "SchedulerDT", locations)

    def setSchedulerSortedList(self, locations=None):
        """
        Use an extremely simple scheduler that simply sorts the list of all models. Useful if lots of invalidations happen and nearly all models are active.

        :param locations: if it is an iterable, the scheduler will only be applied to these locations. If it is None, all nodes will be affected.
        """
        self.setSchedulerCustom("schedulerSL", "SchedulerSL", locations)

    def setSchedulerMinimalList(self, locations=None):
        """
        Use a simple scheduler that keeps a list of all models and traverses it each time in search of the first one. Slight variation of the sorted list scheduler.

        :param locations: if it is an iterable, the scheduler will only be applied to these locations. If it is None, all nodes will be affected.
        """
        self.setSchedulerCustom("schedulerML", "SchedulerML", locations)

    def setSchedulerNoAge(self, locations=None):
        """
        .. warning:: do not use this scheduler if the time advance can be equal to 0. This scheduler strips of the age from every scheduled model, which means that ages do not influence the scheduling.

        Use a stripped scheduler that doesn't care about the age in a simulation. It is equivalent in design to the HeapSet scheduler,
        but uses basic floats instead of tuples.

        :param locations: if it is an iterable, the scheduler will only be applied to these locations. If it is None, all nodes will be affected.
        """
        self.setSchedulerCustom("schedulerNA", "SchedulerNA", locations)

    def setSchedulerHeapSet(self, locations=None):
        """
        Use a scheduler containing 3 different datastructures. It is still experimental, though can provide noticeable performance boosts.

        :param locations: if it is an iterable, the scheduler will only be applied to these locations. If it is None, all nodes will be affected.
        """
        self.setSchedulerCustom("schedulerHS", "SchedulerHS", locations)

    def setShowProgress(self, progress=True):
        """
        Shows progress in ASCII in case a termination_time is given

        :param progress: whether or not to show progress
        """
        self.simulator.progress = progress

    def setTerminationModel(self, model):
        """
        Marks a specific AtomicDEVS model as being used in a termination condition. This is never needed in case no termination_condition is used. It will _force_ the model to run at the controller, ignoring the location that was provided in the model itself. Furthermore, it will prevent the model from migrating elsewhere.

        :param model: an AtomicDEVS model that needs to run on the controller and shouldn't be allowed to migrate
        """
        if self.simulator.setup:
            raise DEVSException("Termination models cannot be changed after the first simulation was already ran!")
        if isinstance(model, AtomicDEVS):
            self.simulator.termination_models.add(model.model_id)
        elif isinstance(model, int):
            # A model_id in itself is passed, so just add this
            self.simulator.termination_models.add(model)
        else:
            raise DEVSException("Only AtomicDEVS models can be used in termination conditions!")

    def registerState(self, variable, model):
        """
        Registers the state of a certain model to an attribute of the simulator AFTER simulation has finished

        :param variable: name of the attribute to assign to
        :param model: the AtomicDEVS model or its model id to fetch the state from
        """
        if isinstance(model, AtomicDEVS):
            model = model.model_id
        self.simulator.callbacks.append((variable, model))

    def setDrawModel(self, drawModel=True, outputfile="model.dot", hideEdgeLabels=False):
        """
        Whether or not to draw the model and its distribution before simulation starts.

        :param drawModel: whether or not to draw the model
        :param hideEdgeLabels: whether or not to hide the labels of the connections, this speeds up the model drawing and allows for reasonably sized diagrams
        """
        if self.simulator.setup:
            raise DEVSException("Model can only be drawn at the first simulation run due to the model being optimized before simulation")
        self.simulator.drawModel = drawModel
        self.simulator.drawModelFile = outputfile
        self.simulator.hideEdgeLabels = hideEdgeLabels

    def setFetchAllAfterSimulation(self, fetch=True):
        """
        Update the complete model by fetching all states from all remote locations. This is different from 'registerState', as it will fetch everything and it will modify the original model instead of adding an attribute to the Simulator object

        :param fetch: whether or not to fetch all states from all models
        """
        self.simulator.fetchAll = fetch

    def setActivityTrackingVisualisation(self, visualize, x = 0, y = 0):
        """
        Set the simulation to visualize the results from activity tracking. An x and y parameter can be given to visualize it in a cell style.

        :param visualize: whether or not to visualize it
        :param x: the horizontal size of the grid (optional)
        :param y: the vertical size of the grid (optional)
        """
        if not isinstance(visualize, bool):
            raise DEVSException("Activity Tracking visualisation requires a boolean")
        if visualize and ((x > 0 and y <= 0) or (y > 0 and x <= 0)):
            raise DEVSException("Activity Tracking cell view requires both a positive x and y parameter for the maximal size of the grid")
        self.simulator.activityVisualisation = visualize
        self.simulator.activityTracking = visualize
        self.simulator.x_size = int(x)
        self.simulator.y_size = int(y)

    def setLocationCellMap(self, locationmap, x = 0, y = 0):
        """
        Set the simulation to produce a nice Cell DEVS like output file of the current location. This file will be regenerated as soon as some relocations are processed.

        :param locationmap: whether or not to generate this file
        :param x: the horizontal size of the grid
        :param y: the vertical size of the grid
        """
        if locationmap and (x <= 0 or y <= 0):
            raise DEVSException("Location cell view requires a positive x and y parameter for the maximal size of the grid")
        self.simulator.locationCellView = locationmap
        self.simulator.x_size = int(x)
        self.simulator.y_size = int(y)

    def setTerminationCondition(self, condition):
        """
        Sets the termination condition for the simulation. Setting this will remove a previous termination time and condition. This condition will be executed on the controller

        :param condition: a function to call that returns a boolean whether or not to halt simulation
        """
        self.simulator.termination_condition = condition
        self.simulator.termination_time = float('inf')

    def setTerminationTime(self, time):
        """
        Sets the termination time for the simulation. Setting this will remove a previous termination time and condition.

        :param time: time at which simulation should be halted
        """
        if not isinstance(time, float) and not isinstance(time, int):
            raise DEVSException("Simulation termination time should be either an integer or a float")
        if time < 0:
            raise DEVSException("Simulation termination time cannot be negative")
        self.simulator.termination_condition = None
        # Convert to float, as otherwise we would have to do this conversion implicitly at every iteration
        self.simulator.termination_time = float(time)

    def setVerbose(self, filename=None):
        """
        Sets the use of a verbose tracer.

        Calling this function multiple times will register a tracer for each of them (thus output to multiple files is possible, though more inefficient than simply (manually) copying the file at the end).

        :param filename: string representing the filename to write the trace to, None means stdout
        """
        if not isinstance(filename, str) and filename is not None:
            raise DEVSException("Verbose filename should either be None or a string")
        self.setCustomTracer("tracerVerbose", "TracerVerbose", [filename])

    def setRemoveTracers(self):
        """
        Removes all currently registered tracers, might be useful in reinitialised simulation.
        """
        self.simulator.tracers = []
        self.simulator.removeTracers()

    def setCell(self, x_size = None, y_size = None, cell_file = "celltrace", multifile = False):
        """
        Sets the cell tracing flag of the simulation

        :param cell: whether or not verbose output should be generated
        :param x_size: the horizontal length of the grid
        :param y_size: the vertical length of the grid
        :param cell_file: the file to save the generated trace to
        :param multifile: if True, each timestep will be save to a seperate file (nice for visualisations)
        """
        if x_size is None or y_size is None:
            raise DEVSException("Cell Tracing requires both an x and y size")
        if x_size < 1 or y_size < 1:
            raise DEVSException("Cell Tracing sizes should be positive")
        self.setCustomTracer("tracerCell", "TracerCell", [cell_file, int(x_size), int(y_size), multifile])

    def setXML(self, filename):
        """
        Sets the use of a XML tracer.

        Calling this function multiple times will register a tracer for each of them (thus output to multiple files is possible, though more inefficient than simply (manually) copying the file at the end).

        :param filename: string representing the filename to write the trace to
        """
        if not isinstance(filename, str):
            raise DEVSException("XML filename should be a string")
        self.setCustomTracer("tracerXML", "TracerXML", [filename])

    def setVCD(self, filename):
        """
        Sets the use of a VCD tracer.

        Calling this function multiple times will register a tracer for each of them (thus output to multiple files is possible, though more inefficient than simply (manually) copying the file at the end).

        :param filename: string representing the filename to write the trace to
        """
        if not isinstance(filename, str):
            raise DEVSException("VCD filename should be a string")
        self.setCustomTracer("tracerVCD", "TracerVCD", [filename])

    def setCustomTracer(self, tracerfile, tracerclass, args):
        """
        Sets the use of a custom tracer, loaded at run time.

        Calling this function multiple times will register a tracer for each of them (thus output to multiple files is possible, though more inefficient than simply (manually) copying the file at the end).

        :param tracerfile: the file containing the tracerclass
        :param tracerclass: the class to instantiate
        :param args: arguments to be passed to the tracerclass's constructor
        """
        self.simulator.tracers.append((tracerfile, tracerclass, args))

    def setLogging(self, destination, level):
        """
        Sets the logging destination for the syslog server.

        :param destination: A tuple/list containing an address, port pair defining the location of the syslog server. Set to None to prevent modification
        :param level: the level at which logging should happen. This can either be a logging level from the logging module, or it can be a string specifying this level. Accepted strings are: 'debug', 'info', 'warning', 'warn', 'error', 'critical'
        """
        if self.simulator.nested:
            raise DEVSException("Logging in nested simulation is not allowed, the logging settings of the parent are used!")
        if not isinstance(self.destination, tuple) and not isinstance(self.simulator.destination, list) and (destination is not None):
            raise DEVSException("Logging destination should be a tuple or a list containing an IP addres, followed by a port address")
        if isinstance(level, str):
            import logging
            # Convert to the correct location
            level = level.lower()
            loglevels = {"debug": logging.DEBUG, "info": logging.INFO, "warning": logging.WARN, "warn": logging.WARN, "error": logging.ERROR, "critical": logging.CRITICAL}
            try:
                level = loglevels[level]
            except IndexError:
                raise DEVSException("Logging level %s not recognized" % level)
        if destination is not None:
            self.simulator.address = destination
        self.simulator.loglevel = level

    def setGVTInterval(self, gvt_int):
        """
        Sets the interval in seconds between 2 GVT calculations. This is the time between the ending of the previous run and the start of the next run, to prevent overlapping calculations.

        .. note:: Parameter should be at least 1 to prevent an overload of GVT calculations

        :param gvt_int: interval in seconds (float or integer)
        """
        if not isinstance(gvt_int, float) and not isinstance(gvt_int, int):
            raise DEVSException("GVT interval should be an integer or a float")
        if gvt_int < 1:
            raise DEVSException("GVT interval should be larger than or equal to one")
        self.simulator.GVT_interval = gvt_int

    def setCheckpointing(self, name, chk_int):
        """
        .. warning:: name parameter will be used as a filename, so avoid special characters

        Sets the interval between 2 checkpoints in terms of GVT calculations. This option generates PDC files starting with 'name'. This is only possible when using MPI.

        :param name: name to prepend to each checkpoint file
        :param chk_int: number of GVT runs that are required to trigger a checkpoint. For example 3 means that a checkpoint will be created after each third GVT calculation
        """
        if not isinstance(chk_int, int):
            raise DEVSException("Checkpoint interval should be an integer")
        if not isinstance(name, str):
            raise DEVSException("Checkpoint name should be a string")
        if chk_int < 1:
            raise DEVSException("Checkpoint interval should be larger than or equal to one")
        if self.simulator.realtime:
            raise DEVSException("Checkpointing is not possible under realtime simulation")
        self.simulator.CHK_interval = chk_int
        self.simulator.CHK_name = name

    def setStateSaving(self, state_saving):
        """
        Sets the type of state saving to use, this will have a high impact on performance. It is made customizable as some more general techniques will be much slower, though necessary in certain models.

        :param state_saving: Either an ID of the option, or (recommended) a string specifying the method, see options below.

        .. glossary::

           deepcopy
                use the deepcopy module

           pickle0
                use the (c)pickle module with pickling protocol 0

           pickleH
                use the (c)pickle module with the highest available protocol

           pickle
                use the (c)pickle module

           copy
                use the copy module (only safe for flat states)

           assign
                simply assign states (only safe for primitive states)

           none
                equivalent to assign (only safe for primitive states)

           custom
                define a custom 'copy' function in every state and use this
        """
        if not isinstance(state_saving, int) and not isinstance(state_saving, str):
            raise DEVSException("State saving should be done using an integer or a string")
        if isinstance(state_saving, str):
            options = {"deepcopy": 0, "pickle0": 1, "pickleH": 2, "pickle": 2, "copy": 3, "assign": 4, "none": 4, "custom":5, "marshal": 6}
            try:
                state_saving = options[state_saving]
            except IndexError:
                raise DEVSException("State saving option %s not recognized" % state_saving)
        self.simulator.state_saving = state_saving

    def setMessageCopy(self, copy_method):
        """
        Sets the type of message copying to use, this will have an impact on performance. It is made customizable as some more general techniques will be much slower.

        :param copy_method: Either an ID of the option, or (recommended) a string specifying the method, see options below

        .. glossary::

           pickle
                use the (c)pickle module

           custom
                define a custom 'copy' function in every message and use this

           none
                don't use any copying at all, unsafe though most other DEVS simulators only supply this
        """
        if not isinstance(copy_method, int) and not isinstance(copy_method, str):
            raise DEVSException("Message copy method should be done using an integer or a string")
        if isinstance(copy_method, str):
            options = {"pickle": 0, "custom": 1, "none": 2}
            try:
                copy_method = options[copy_method]
            except IndexError:
                raise DEVSException("Message copy option %s not recognized" % copy_method)
        self.simulator.msgCopy = copy_method

    def setRealTime(self, realtime = True, scale=1.0):
        """
        Sets the use of realtime instead of 'as fast as possible'.

        :param realtime: whether or not to use realtime simulation
        :param scale: the scale for scaled real time, every delay will be multiplied with this number
        """
        if not local(self.simulator):
            raise DEVSException("Real time simulation is only possible in local simulation!")
        self.simulator.realtime = realtime
        self.simulator.realtimeScale = scale

    def setRealTimeInputFile(self, generatorfile):
        """
        Sets the realtime input file to use. If realtime is not yet set, this will auto-enable it.

        :param generatorfile: the file to use, should be a string, NOT a file handle. None is acceptable if no file should be used.
        """
        if not self.simulator.realtime:
            self.setRealTime(True)
        if not isinstance(generatorfile, str) and generatorfile is not None:
            raise DEVSException("Realtime generator should be a string or None")
        self.simulator.generatorfile = generatorfile

    def setRealTimePlatformThreads(self):
        """
        Sets the realtime platform to Python Threads. If realtime is not yet set, this will auto-enable it.
        """
        if not self.simulator.realtime:
            self.setRealTime(True)
        self.simulator.subsystem = "python"
        self.simulator.realtime_extra = []

    def setRealTimePlatformTk(self, tk):
        """
        .. note:: this clearly requires Tk to be present.

        Sets the realtime platform to Tk events. If realtime is not yet set, this will auto-enable it.
        """
        if not self.simulator.realtime:
            self.setRealTime(True)
        self.simulator.subsystem = "tkinter"
        self.simulator.realtime_extra = [tk]

    def setRealTimePlatformGameLoop(self):
        """
        Sets the realtime platform to Game Loop. If realtime is not yet set, this will auto-enable it.

        :param fps: the number of times the game loop call should be made per second
        """
        if not self.simulator.realtime:
            self.setRealTime(True)
        self.simulator.subsystem = "loop"
        self.simulator.realtime_extra = []

    def setRealTimePorts(self, ports):
        """
        Sets the dictionary of ports that can be used to put input on. If realtime is not yet set, this will auto-enable it.

        :param ports: dictionary with strings as keys, ports as values
        """
        if not self.simulator.realtime:
            self.setRealTime(True)
        if not isinstance(ports, dict):
            raise DEVSException("Realtime input port references should be a dictionary")
        self.simulator.realTimeInputPortReferences = ports

    def setModelState(self, model, newState):
        """
        Reinitialize the state of a certain model

        :param model: model whose state to change
        :param newState: state to assign to the model
        """
        if not isinstance(model, int):
            model = model.model_id
        self.simulator.modifyState(model, newState)

    def setModelStateAttr(self, model, attr, value):
        """
        Reinitialize an attribute of the state of a certain model

        :param model: model whose state to change
        :param attr: string representation of the attribute to change
        :param value: value to assign
        """
        if not isinstance(model, int):
            model = model.model_id
        self.simulator.modifyStateAttr(model, attr, value)

    def setModelAttribute(self, model, attr, value):
        """
        Reinitialize an attribute of the model itself

        :param model: model whose attribute to set
        :param attr: string representation of the attribute to change
        :param value: value to assign
        """
        if not isinstance(model, int):
            model = model.model_id
        self.simulator.modifyAttributes(model, attr, value)

    def setActivityRelocatorCustom(self, filename, classname, *args):
        """
        Sets the use of a custom relocator

        :param filename: filename containing the relocator
        :param classname: classname of the relocator
        :param args: all other args are passed to the constructor
        """
        import importlib
        tv = importlib.import_module("DEVSKernel.PyPDEVS.pypdevs221.src.%s"%filename)
        
        #exec("from %s import %s" % (filename, classname))
        self.simulator.activityRelocator = eval("tv.%s(*args)" % classname)

    def setActivityRelocatorBasicBoundary(self, swappiness):
        """
        Sets the use of the *activity* relocator called *'Basic Boundary'*.

        :param swappiness: how big the deviation from the average should be before scheduling relocations
        """
        if swappiness < 1.0:
            raise DEVSException("Basic Boundary Activity Relocator should have a swappiness >= 1.0")
        self.setActivityRelocatorCustom("basicBoundaryRelocator", "BasicBoundaryRelocator", swappiness)

    def setGreedyAllocator(self):
        """
        Sets the use of the greedy allocator that is contained in the standard PyPDEVS distribution.
        """
        from .greedyAllocator import GreedyAllocator
        self.setInitialAllocator(GreedyAllocator())

    def setAutoAllocator(self):
        """
        Sets the use of an initial allocator that simply distributes the root models.
        This is a static allocator, meaning that no event activity will be generated.
        """
        from .autoAllocator import AutoAllocator
        self.setInitialAllocator(AutoAllocator())

    def setInitialAllocator(self, allocator):
        """
        Sets the use of an initial allocator instead of the manual allocation. Can be set to None to use manual allocation (default).

        :param allocator: the allocator to use for assigning the initial locations
        """
        self.simulator.allocator = allocator
