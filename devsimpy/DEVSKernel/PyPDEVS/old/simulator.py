# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# simulator.py --- 'Plain' DEVS Model Simulator
#                     --------------------------------
#                            Copyright (c) 2013
#                          Jean-Sastien  BOLDUC
#                             Hans  Vangheluwe
#                            Yentl Van Tendeloo
#                       McGill University (Montréal)
#                     --------------------------------
# Version 1.0                                        last modified: 01/11/01
# Version 1.0.1                                      last modified: 04/04/05
#  - Deals with DeprecationWarning
# Version 1.0.2                                      last modified: 06/06/05
#  - Added code to display atomic DEVS' initial conditions
# Version 1.1                                        last modified: 09/09/12
#  - A lot of optimizations, especially for atomic models
# Version 2.0                                        last modified: 30/01/13
#  - Allow distributed and parallel simulation
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
# Description of message passing mechanism (to be completed)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


##  IMPORTS
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

# Import for uniform random number generators
import random
import logging
from heapq import *

#from tracers import Tracers

import sys

from .DEVS import *

from .basesimulator import *

#cython from server cimport Server
from .server import * #cython-remove

from .logger import *
from . import middleware

import threading
import time
from .util import *

try:
    import pickle as pickle
except ImportError:
    import pickle

##  GLOBAL VARIABLES AND FUNCTIONS
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

# {\tt __VERBOSE__} switch allows to enter\dots well, ''verbose mode'' when set
# to true. Useful for debugging (similar to {\tt #define _DEBUG_} convention in
# {\tt C++}).
# Now a global variable set by an argument passed to the simulator

##  SIMULATOR CLASSES
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

if middleware.USE_MPI:
    if COMM_WORLD.Get_size() == 1:
        # Possibly we need to start the server ourselves...
        # but first check if it is already started or not
        if MPIRedirect.local == None:
            # It seems it wasn't, do it ourselves
            global server
            server = Server(0)
            #server.bootMPI()

class Simulator(object):
    """
    Associates a hierarchical DEVS model with the simulation engine.
    """

    ###
    def __init__(self, model):
        """
        Constructor of the simulator.
        Args:
            model - a valid COUPLED model (created with the provided function)
            controller - the name of the controller, defaults to "Controller"
                         shouldn't be modified normally, though it allows nicer
                         nested simulation or parallel simulation
        """
        controller = 0

        if model is not None and not isinstance(model, CoupledDEVS):
            raise DEVSException("Currently, only Coupled models can be simulated; \nThis could also mean that there are ambiguous imports for the model and the experiment file.\nE.g. caused by symlinks or different import mechanisms\nExpected: " + str(CoupledDEVS) + ", got: " + str(model.__class__.name))

        if middleware.USE_PYRO:
            # Start the controller
            # But only if none is already running
            try:
                getProxy(controller).getName()
            except:
                # No matter what happens, it probably doesn't mean anything good
                # Most likely, the server was killed so we will have to restart it
                self.process = threading.Thread(target=startServer, args=[controller])
                self.process.daemon = True
                self.process.start()
                time.sleep(0.5)

        # Controller is the main simulation server
        if model is not None:
            self.controller_name = str(controller)
            self.controller = getProxy(self.controller_name)
            self.controller.setCoupledModel(model, self.controller_name, None)
            self.controller.setID()
            self.controller.setAllData()

        # Make an event for waiting until the GVT calculation is done
        self.runGVT = True
        self.callbacks = []

        # Fix the complete hierarchy
        self.controller.fixHierarchy(self.controller_name, "")

        self.controller.directConnect()

    def registerState(self, variable, model):
        location, id = self.controller.findModel(model)
        self.callbacks.append([location, id, variable])

    def checkpoint(self):
        outfile = open("checkpoint_SIM.pdc", 'w')
        pickle.dump(self, outfile)

    def loadCheckpoint(self, GVT):
        self.controller = getProxy(self.controller_name)
        # Set restore to True to make sure that we append to the previous file
        self.controller.setVerbose(self.verbose, self.outfile, restore=True)

        locations = list(range(COMM_WORLD.Get_size()))
        for i in locations:
            # Construct the ring
            getProxy(locations[i]).setNextLP(locations[(i+1) % len(locations)], len(locations))
        self.real_simulate()

    ###
    def simulate(self,
                 termination_condition=None,
                 termination_time=float('inf'),
                 verbose=False,
                 xml=False,
                 vcd=False,
                 termination_location=None,
                 logaddress=('localhost', 514),
                 loglevel=logging.WARN,
                 outfile=None,
                 GVT_freq=1,
                 CHK_freq=-1,
                 state_saving=2,
                 seed=1,
                 allowNested=True,
                 manualCopy=False,
                 disallowIrreversible=False,
                 realTimeInputPortReferences={},
                 realtime=False,
                 generatorfile=None,
                 subsystem="python"
                 ):
        #TODO update
        """
        Simulate the model at this simulation kernel. Several options are possible
        to guide simulation.
        Args:
            termination_condition - a function taking 2 parameters
                                        time - simulation time
                                        model - the local model
                                    this will be run to check whether or not
                                    simulation should still progress. This function
                                    should only have access to LOCAL variables as
                                    the timewarp implementation doesn't guarantee
                                    other variables to be correct. If this is
                                    defined, it will override the global
                                    termination time
            termination_time - the time at which the simulation should stop. This
                               time is the global time, so no event after this time
                               will ever be simulated (contrary to the local
                               termination condition). Termination_time should be
                               used instead of termination_condition if possible
                               for performance considerations
            verbose - should a verbose human-readable trace file be generated
            xml - should an XML file be generated (devstrace.xml), this requires
                  an implementation of the toXML() function
            vcd - should a VCD file be generated (devstrace.vcd), this should only
                  be used when simulating logic circuits as otherwise an exception
                  will be thrown
            termination_location - the name of the simulation kernel that is
                                   responsible for deciding whether simulation may
                                   terminate or not. Value is ignored if no
                                   termination_condition is provided
            logaddress - the location of the syslog server that should be used,
                         in the format (location, portnumber). Syslog messages
                         will be sent with the UDP protocol
            loglevel - provides the level at which logging should happen, this
                       variable should be provided in the form of a logging.*
                       variable
            outfile - filename that should be used for the verbose output, default
                      None means output to stdout
            GVT_freq - the interval that should be used between two consecutive GVT
                       calculations (in seconds). This interval should not be too
                       small as it will completely stall simulation. Should be at
                       least 1 second.
            CHK_freq - the number of GVT rounds to pass before creating a new
                       checkpoint. Set this to -1 to prevent checkpoint creation.
                       Only possible if MPI is used as a backend
            state_saving - define which way to use to save the state, options are:
                            0: use deepcopy
                               can copy everything, but very slow
                            1: use pickle with protocol 0
                               can copy most things, relatively slow
                            2: use pickle with highest available protocol
                               can copy most things, relatively fast
                            3: use copy (UNSAFE)
                               makes a shallow copy, fast
                            4: no copying (UNSAFE)
                               can only copy primitive objects, though extremely fast
                           Choosing 2 is probably the best choice, all options marked
                           with UNSAFE should NOT be used unless you know what you
                           are doing, as the state revertion of time warp could be
                           corrupted
            seed - the seed that must be used in simulation. Note that this seed
                   is also forwarded to each server.
        """
        #TODO complete this documentation
        self.GVT_freq = GVT_freq
        # Can only be multiples
        self.CHK_freq = int(CHK_freq)
        self.checkpointCounter = 0
        if 0 <= self.CHK_freq < 1:
            raise DEVSException("Checkpointing frequency should be at least 1")

        if self.CHK_freq > 0 and not middleware.USE_MPI:
            raise DEVSException("Checkpointing is only possible with MPI")

        if self.CHK_freq > 0 and realtime:
            raise DEVSException("Checkpointing and realtime don't work together")

        if not middleware.USE_MPI and not middleware.USE_PYRO:
            # Default to MPI, which is needed for MPIFaker
            middleware.USE_MPI = True

        if middleware.USE_MPI and middleware.USE_PYRO:
            raise DEVSException("You should use only one middleware")

        # Check if the GVT interval is decent
        if self.GVT_freq < 1:
            raise DEVSException("GVT interval is too small for a useful simulation, \
                                 should be at least 1 second.")

        self.verbose = verbose
        self.outfile = outfile
        self.xml = xml
        self.vcd = vcd
        self.address = logaddress
        self.loglevel=loglevel
        self.seed=seed
        self.manualCopy = manualCopy
        self.disallowIrreversible = disallowIrreversible
        self.allowNested = allowNested
        self.realTimeInputPortReferences = realTimeInputPortReferences
        self.realtime = realtime
        self.generatorfile = generatorfile

        # Seed the random number generator
        # This needs to be done deterministically
        # to guarantee the same stream of pseudo-random
        # numbers for each (repeated) simulation experiment.
        # By default, the random number generated is
        # seeded by a number obtained from the system clock.
        random.seed(seed)

        try:
            ##### Optimizations
            ### Use automatically generated ID's instead of getModelFullName
            if middleware.USE_MPI:
                loclist = list(range(COMM_WORLD.Get_size()))
            else:
                loclist = list(self.controller.getLocationList(set()))
                # Sort is not absolutely necessary, though it will be small and easens debugging
                loclist.sort()

            for location in loclist:
                proxy = getProxy(location)
                # For each simulation server, set the relevant simulation variables
                # Most of these are not strictly needed at each kernel, though it
                # allows for performance optimisations (e.g. not sending verbose output
                # if the controller will not use it)
                proxy.setGlobals(verbose=verbose,
                                 xml=xml,
                                 vcd=vcd,
                                 address=logaddress,
                                 loglevel=loglevel,
                                 controller=self.controller_name,
                                 seed=seed,
                                 gvtfrequency=self.GVT_freq,
                                 checkpointfrequency=self.CHK_freq,
                                 kernels=len(loclist),
                                 statesaver=state_saving,
                                 manualCopy=manualCopy,
                                 allowNested=allowNested,
                                 disallowIrreversible=disallowIrreversible,
                                 realtime=realtime,
                                 inputReferences=realTimeInputPortReferences)
                proxy.buildList()

            # Set the verbosity on the controller only, otherwise each kernel
            # would open the file itself, causing problems. Furthermore, all
            # verbose output will be sent to the controller
            self.controller.setVerbose(verbose, outfile)

            for i in loclist:
                getProxy(i).setKernels(loclist)

            for i in range(len(loclist)):
                # Construct the ring
                getProxy(loclist[i]).setNextLP(loclist[(i+1) % len(loclist)], len(loclist))

            # Reconstruct everywhere
            for location in loclist:
                proxy = getProxy(location)
                proxy.buildList()

            # Check whether global or local termination should be used
            if termination_condition is not None:
                # Local termination condition
                if termination_location is None:
                    termination_location = self.controller_name
                getProxy(termination_location).setTerminationCondition(termination_condition)
                self.controller.setTerminationServer(termination_location)
            else:
                # Global termination condition
                for location in loclist:
                    proxy = getProxy(location)
                    makeOneway(proxy, "setTerminationTime")
                    proxy.setTerminationTime(termination_time)

            # Start all necessary tracers, which these are, are decided elsewhere
            self.controller.startTracers()
            if self.CHK_freq > 0:
                self.checkpoint()

            if not realtime:
                # No realtime, just run as usual
                self.real_simulate(loclist)
            else:
                # Real time, we need to make sure that we are working locally
                if len(loclist) > 1:
                    raise DEVSException("Real time simulation only possible locally")
                global server
                from . import RTthreads
                from . import environments
                from . import cores
                if subsystem == "python":
                    subsystem = cores.PythonThreads()
                elif subsystem == "tkinter":
                    subsystem = cores.TkinterThreads()
                else:
                    raise DEVSException("Unknown threading subsystem: " + str(subsystem))
                generator = environments.AsynchronousComboGenerator(generatorfile, subsystem)
                RTthreads.main(server.simstack[0].model, generator, server.simstack[0], subsystem)

        except DEVSException as e:
            print(e)
            # Should also exit on a DEVSException since this isn't really meant to happen
            import sys
            sys.exit(1)

    def real_simulate(self, locations = list(range(COMM_WORLD.Get_size()))):
        try:
            for location in locations:
                # Don't run all of these on a seperate thread, as it returns no result
                proxy = getProxy(location)
                if True:
                #if len(locations) != 1:
                    makeOneway(proxy, "simulate")
                proxy.simulate()

            self.controller.waitFinish(len(locations))
            assert debug("Finished waiting for all processors")

        except DEVSException as e:
            print(e)
            # Should also exit on a DEVSException since this isn't really meant to happen
            import sys
            sys.exit(1)

        # Perform all pending operations
        assert debug("Performing all delayed actions")
        self.controller.performActions()

        # Stop all running tracers
        assert debug("Stopping all tracers")
        self.controller.stopTracers()

        # Now the state is stable, fetch all registered states before shutting down
        assert debug("Fetching all requested states")
        for i in self.callbacks:
            location, model_id, variable = i
            state = getProxy(location).getState(model_id)
            assert debug("Setting state for " + str(variable))
            setattr(self, variable, state)

        # Shut down every location
        assert debug("Shutting down servers")
        for loc in locations:
            proxy = getProxy(loc)
            if middleware.USE_PYRO:
                try:
                    proxy.finish()
                except Pyro4.errors.ConnectionClosedError:
                    # Normal that the connection gets closed...
                    pass
            elif middleware.USE_MPI:
                # If this is oneway, we will stop the simulation even before the finish was called everywhere
                proxy.finish()
