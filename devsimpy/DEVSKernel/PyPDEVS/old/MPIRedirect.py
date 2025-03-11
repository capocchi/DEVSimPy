from . import middleware
import sys

class MPIFaker(object):
    @staticmethod
    def Get_size():
        return 1

    @staticmethod
    def Get_rank():
        return 0

try:
    from mpi4py import MPI
    COMM_WORLD = MPI.COMM_WORLD
except ImportError:
    COMM_WORLD = MPIFaker()
    #TODO make switchable to the fake environment
    if middleware.USE_MPI and False:
        print("MPI used as backend, but MPI4py not found")
        sys.exit(1)

from . import util
import random
import threading
from .logger import *

class MPIRedirect(object):
    # Reserve 50 slots, this is (hopefully) way too much, though the backend would crash if we run out of these...
    # Honestly, if you have 50 connections for which you are waiting, you will have worse problems than running out of IDs
    waiting = [None] * 50
    # Don't use range itself, as this doesn't work in Python3
    free_ids = [i for i in range(50)]
    noproxy = frozenset(["__getnewargs__", "__getinitargs__", "__str__", "__repr__"])
    id_lock = threading.Lock()
    local = None
    lst = []

    def __init__(self, rank):
        if rank is None:
            self.rank = None
        else:
            self.rank = int(rank)
        self.oneway = []

    def __getinitargs__(self):
        return [self.rank]

    def __getstate__(self):
        return {"rank": self.rank}

    def __setstate__(self, state):
        self.oneway = []
        self.rank = state["rank"]

    def __getattr__(self, name):
        if name in MPIRedirect.noproxy:
            raise AttributeError(name)
        def newcall(*args, **kwargs):
            return MPIRedirect.remoteCall(self, name, *args, **kwargs)
        def localcall(*args, **kwargs):
            return MPIRedirect.localCall(self, name, *args, **kwargs)
        if (not middleware.USE_MPI) or (self.rank == COMM_WORLD.Get_rank()):
            return localcall
        else:
            return newcall

    def setOneWay(self, method):
        self.oneway.append(str(method))

    def remoteCall(self, method, *args, **kwargs):
        # Unique tag, but at least 2 (0 reserved for exit, 1 is reserved for calls)
        wait = str(method) not in self.oneway
        if wait:
            MPIRedirect.id_lock.acquire()
            call_id = MPIRedirect.free_ids.pop()
            MPIRedirect.id_lock.release()
        else:
            # Mention that we are not waiting for a reply
            call_id = None
        try:
            kernelnum = len(MPIRedirect.local.simstack) - 1
        except AttributeError:
            kernelnum = 0
        data = [call_id, method, kernelnum]
        data.append(args)
        data.append(kwargs)
        if wait:
            event = threading.Event()
            MPIRedirect.waiting[call_id] = event
        comm = COMM_WORLD
        MPIRedirect.lst.append(comm.isend(data, dest=self.rank, tag=1))
        #print("SEND OK")
        if wait:
            event.wait()
            response = MPIRedirect.waiting[call_id]
            # Clear the object from memory
            MPIRedirect.waiting[call_id] = None
            MPIRedirect.id_lock.acquire()
            MPIRedirect.free_ids.append(call_id)
            MPIRedirect.id_lock.release()
            return response
        else:
            return None
  
    def localCall(self, method, *args, **kwargs):
        wait = str(method) not in self.oneway
        if MPIRedirect.local is not None:
            func = getattr(MPIRedirect.local, method)
        else:
            if middleware.USE_MPI:
                raise util.DEVSException("You forgot to run the simulator with the MPI startup script (mpirunner.py)")
            elif middleware.USE_PYRO:
                # This shouldn't happen
                raise util.DEVSException("Simulation server in Pyro didn't boot yet")
        if wait:
            return func(*args, **kwargs)
        else:
            threading.Thread(target=func, args=args, kwargs=kwargs).start()
