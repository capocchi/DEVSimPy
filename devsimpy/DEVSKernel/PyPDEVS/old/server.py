# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# server.py --- Server program for DEVS simulation, used with Pyro
#                     --------------------------------
#                            Copyright (c) 2013
#                              Hans Vangheluwe
#                            Yentl Van Tendeloo
#                       McGill University (Montréal)
#                     --------------------------------
# Version 2.0                                        last modified: 30/01/13
#  - Allow distributed and parallel simulation
#    
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from .basesimulator import *
from .controller import *
from . import middleware
from .threadpool import ThreadPool
import threading
import time

import sys
from .util import *
from .logger import *
from .DEVS import *

#cython cdef class Server:
class Server(object): #cython-remove
    noforward = frozenset(["__str__", "__getstate__", "__setstate__", "__repr__", "simstack"])
    local = frozenset(["setCoupledModel", "finish", "endNestedSim", "nestedSim", "continuePrevSim", "startNestedSim", "announceSim", "announceEnd", "setKernels", "notifyDone"])

    def __init__(self, name, daemon = None):
        self.daemon = daemon
        self.name = str(name)
        self.simstack = [None]
        import logging
        setLogger(str(name), ('localhost', 514), logging.DEBUG)
        MPIRedirect.local = self
        if middleware.USE_MPI:
            self.threadpool = ThreadPool(5)

    def getName(self):
        # Actually more of a ping function...
        return self.name

    # All calls to this server are likely to be forwarded to the currently
    #  active simulation kernel, so provide an easy forwarder
    def __getattr__(self, name):
        # For accesses that are actually meant for the currently running kernel
        if name in Server.noforward:
            raise AttributeError()
        if self.simstack[-1] is None:
            return getattr(self.simstack[-2], name)
        else:
            return getattr(self.simstack[-1], name)

    def setNextLP(self, location, size):
        self.nextLP = getProxy(location)
        self.nextLPid = location
        self.size = size
        for i in self.simstack:
            i.setNextLP(location, size)

    def getNextLP(self):
        return self.nextLPid

    def nestedSim(self):
        self.simstack[-1].nestedlock.acquire()
        # Now the current simulation is halted, ready to add a new simulation

    def endNestedSim(self):
        sim = self.simstack.pop()
        # Clear simulator
        del sim

    def continuePrevSim(self):
        self.simstack[-1].nestedlock.release()

    def getLayer(self):
        return len(self.simstack)

    def startNestedSim(self):
        self.simstack.append(None)

    def announceSim(self, requestname):
        # A new simulation must start, halt ALL simulators
        # Wait for the GVT to stop running
        #NOTE mandatory that this runs on the controller
        # Try to initiate a nested simulation at this level
        if not self.simstack[-1].nestingLock.acquire(False):
            return False
        for i in range(self.size):
            if str(i) == str(requestname):
                # Don't wait for ourselves, as we are still simulating while inside the nested model
                continue
            getProxy(i).nestedSim()
        for i in range(self.size):
            # All cores are locked, initiate a new round
            getProxy(i).startNestedSim()
        return True

    def announceEnd(self, requestname):
        # Prevent GVT algorithm from running in this unstable state
        for i in range(self.size):
            getProxy(i).endNestedSim()
        for i in range(self.size):
            if str(i) == str(requestname):
                # Don't continue with ourselves, since we are actually still running
                continue
            getProxy(i).continuePrevSim()
        # Unlock GVT lock
        self.simstack[-1].nestingLock.release()

    def processMPI(self, data, comm, remote):
        # Receiving a new request
        resendTag = data[0]
        function = data[1]
        kernel = data[2]
        args = data[3]
        kwargs = data[4]
        # Run this simulation at the topmost simulation kernel
        if (function in Server.local):
            func = getattr(self, function)
        else:
            func = getattr(self.simstack[kernel], function)
        result = func(*args, **kwargs)
        if result is None:
            result = 0
        if resendTag is not None:
            assert debug("Sending data to " + str(remote) + " -- " + str(resendTag) + ": " + str(result))
            comm.send(result, dest=remote, tag=resendTag)

    def listenMPI(self):
        """
        import cProfile
        cProfile.runctx("self.profile_listenMPI()", locals(), globals())

    def profile_listenMPI(self):
        """
        comm = COMM_WORLD
        #NOTE could preallocate the memory for the incomming call, though possible threading problems
        lasttime = time.time()
        status = MPI.Status()
        while True:
            assert debug("[" + str(comm.Get_rank()) + "]Listening to remote " + str(MPI.ANY_SOURCE) + " -- " + str(MPI.ANY_TAG))
            # First check if a message is present, otherwise we would have to do busy polling
            """
            while not comm.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status):
                # Yield to other threads
                # 0 to mean that we should yield elsewhere, UNLESS no other process is waiting
                time.sleep(0)
            """
            data = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
            tag = status.Get_tag()
            assert debug("Got data from " + str(status.Get_source()) + " (" + str(status.Get_tag()) + "): " + str(data))
            if tag == 0:
                # Flush all waiters, as we will never receive an answer when we close the receiver...
                for i in MPIRedirect.waiting:
                    try:
                        i.set()
                    except AttributeError:
                        # It was not a lock...
                        pass
                    except KeyError:
                        # It was deleted in the meantime
                        pass
                break
            elif tag == 1:
                # NOTE Go back to listening ASAP, so do the processing on another thread
                if data[1] == "getTargets":
                    # This should not be queued as it might be called recursively and we want to prevent this
                    threading.Thread(target=Server.processMPI, args=[self, list(data), comm, status.Get_source()]).start()
                else:
                    self.threadpool.add_task(Server.processMPI, self, list(data), comm, status.Get_source())
            else:
                # Receiving an answer to a previous request
                try:
                    event = MPIRedirect.waiting[tag]
                    MPIRedirect.waiting[tag] = data
                    event.set()
                except KeyError:
                    # Probably processed elsewhere already, just skip
                    pass
                except AttributeError:
                    # Key was already set elsewhere
                    pass

    def bootMPI(self):
        if COMM_WORLD.Get_size() > 1:
            listener = threading.Thread(target=Server.listenMPI, args=[self])
            listener.start()

    def setCoupledModel(self, modelCode, parent_location, parent_id, imports = None):
        if isinstance(modelCode, str):
            # Put this here for Python3
            model = None
            if imports is not None:
                exec(imports)
            model = eval(modelCode)
        else:
            model = modelCode
        if not isinstance(model, CoupledDEVS):
            raise DEVSException("Only coupled models are allowed to be distributed")
        model.internal = False
        model.location = self.name
        model.setRootSim(self, self.name)
        if parent_id is not None:
            model.parent = RemoteCDEVS(parent_location)
        else:
            model.parent = None
        if self.name == "0":
            sim = Controller(self.name, model)
        else:
            sim = BaseSimulator(self.name, model)
        self.simstack[-1] = sim
        # Should still fill in all model_ids
        sim.setID()

    def notifyDone(self, name):
        for i in self.locations:
            proxy = getProxy(i)
            makeOneway(proxy, "notifyDone")
            proxy.notifyKernelDone(name)

    def finish(self):
        sim = self.simstack[-1]
        sim.simlock.acquire()
        sim.nestedlock.acquire()
        # Shut down all threads on the topmost simulator
        sim.finished = True
        sim.inmsg.set()
        sim.shouldrun.set()
        if middleware.USE_MPI:
            # It is possible that we are still waiting on a reply
            #  since it was agreed to stop, all messages should be useless
            for i in MPIRedirect.waiting:
                try:
                    i.set()
                except AttributeError:
                    # It was not a lock...
                    pass
                except KeyError:
                    # It was deleted in the meantime
                    pass

        # Wait until they are done
        sim.queueFinish.wait()
        sim.simFinish.wait()
        if middleware.USE_PYRO:
            if len(self.simstack) == 1:
                try:
                    self.daemon.shutdown()
                except:
                    pass
        # Release the simlock, since we are possibly working in one of the layers
        #  which will try to grab the simlock
        sim.nestedlock.release()
        sim.simlock.release()

    def setKernels(self, kernels):
        self.locations = kernels

def startServer(name):
    from . import stacktracer
    stacktracer.trace_start("trace_" + str(name) + ".html",interval=2,auto=True) # Set auto flag to always update file!
    daemon = Pyro4.Daemon()
    simserver = Server(name, daemon)
    ns = Pyro4.locateNS()
    uri = daemon.register(simserver)
    ns.register(str(name), uri)
    # Run the loop until something happens (probably keyboardinterrupt...)
    try:
        daemon.requestLoop()
    except:
        daemon.shutdown()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        startServer(str(sys.argv[1]))
    else:
        print("Wrong invocation, should be of the form:")
        print(("   " + str(sys.argv[0]) + " name"))
