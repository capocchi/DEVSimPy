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
Class containing a kind of RMI implementation over MPI.
"""

oneways = frozenset(["simulate", 
                     "receiveControl", 
                     "receive", 
                     "finishSimulation", 
                     "notifyWait", 
                     "notifyRun", 
                     "prepare", 
                     "receiveAntiMessages", 
                     "migrationUnlock", 
                     "notifyMigration", 
                     "requestMigrationLock", 
                     "setGVT"])

import pypdevs.middleware as middleware

class MPIFaker(object):
    """
    A dummy implementation of MPI4Py if none is found
    """
    # Don't follow coding style here, as we need to be compatible with the mpi4py interface
    @staticmethod
    def Get_size():
        """
        Return the size of the MPI world. Always 1, since it is only used in cases where local simulation is done.

        :returns: int -- number of MPI processes running
        """
        return 1

    @staticmethod
    def Get_rank():
        """
        Return the rank of the current process in the MPI world. Always 0, since it is only used in cases where local simulation is done.

        :returns: int -- rank of the current process
        """
        return 0

try:
    from mpi4py import MPI
    COMM_WORLD = MPI.COMM_WORLD
except ImportError:
    # MPI4Py not found, fall back to the dummy implementation
    COMM_WORLD = MPIFaker()

import threading
from pypdevs.logger import *

def cleaning():
    """
    Clean up the list of all waiting asynchronous connections

    Should be ran on a seperate thread and will simply wait on the connection status to be 'complete'. This is necessary for the MPI specification.
    """
    import pypdevs.accurate_time as time
    while 1:
        try:
            # This is atomic (at least where it matters)
            MPI.Request.Wait(MPIRedirect.lst.pop())
        except IndexError:
            # List is empty
            time.sleep(1)
        except:
            # Can happen during shutdown, though it won't be recognized as 'AttributeError'
            pass

class MPIRedirect(object):
    """
    Redirect all calls to an instantiation of this class to the server for which it was created, uses MPI (or the dummy implementation).
    
    For speed, it contains an optimisation when the call is actually done locally (it will simply start a thread then). This complete
    implemenation is based on so called 'magic functions' from Python.
    """
    # Reserve 50 slots, this is (hopefully) way too much, though the backend would crash if we run out of these...
    # Honestly, if you have 50 connections for which you are waiting, you will have worse problems than running out of IDs
    waiting = [None] * 50
    # Don't use range itself, as this doesn't work in Python3
    free_ids = [i for i in range(50)]
    noproxy = frozenset(["__getnewargs__", 
                         "__getinitargs__", 
                         "__str__", 
                         "__repr__"])
    local = None
    lst = []

    if COMM_WORLD.Get_size() > 1:
        thrd = threading.Thread(target=cleaning, args=[])
        thrd.daemon = True
        thrd.start()

    def __init__(self, rank):
        """
        Constructor.

        :param rank: the rank of the server to redirect the call to
        :param oneways: iterable containing all functions that should be done without waiting for completion
        """
        self.rank = int(rank)
        self.oneway = oneways

    def __getinitargs__(self):
        """
        For pickling

        :returns: list containing the rank
        """
        return [self.rank]

    def __getstate__(self):
        """
        For pickling

        :returns: dictionary containing the rank and the oneway list
        """
        return {"rank": self.rank, "oneway": self.oneway}

    def __setstate__(self, state):
        """
        For pickling

        :param state: the dictionary provided by the *__getstate__* method
        """
        self.rank = state["rank"]
        self.oneway = state["oneway"]

    def __getattr__(self, name):
        """
        Determine whether or not we should redirect the call to the local or the remote server

        :param name: the name of the function to call
        :returns: function -- function to be actually called to perform the action
        """
        if name in MPIRedirect.noproxy:
            raise AttributeError(name)
        def newcall(*args, **kwargs):
            """
            A call to a remote location
            """
            return MPIRedirect.remoteCall(self, name, *args, **kwargs)
        return newcall

    def remoteCall(self, method, *args, **kwargs):
        """
        Make the remote call

        :param method: method name to call (as a string)
        :returns: return value of the called method; always None in case it is a one-way call
        """
        # Unique tag, but at least 2 (0 reserved for exit, 1 is reserved for calls)
        wait = str(method) not in self.oneway
        if wait:
            call_id = MPIRedirect.free_ids.pop()
        else:
            # Mention that we are not waiting for a reply
            call_id = None
        data = [call_id, method, args, kwargs]
        if wait:
            MPIRedirect.waiting[call_id] = event = threading.Event()
        MPIRedirect.lst.append(COMM_WORLD.isend(data, dest=self.rank, tag=1))
        if wait:
            event.wait()
            response = MPIRedirect.waiting[call_id]
            # Clear the object from memory
            MPIRedirect.waiting[call_id] = None
            MPIRedirect.free_ids.append(call_id)
            return response
  
class LocalRedirect(object):
    """
    Local redirector class
    """
    def localCall(self, method, *args, **kwargs):
        """
        Actually perform the local call

        :param method: the name of the method
        :returns: the return value of the function, None if it is a oneway call
        """
        func = getattr(self.server, method)
        if str(method) in self.oneway:
            threading.Thread(target=func, args=args, kwargs=kwargs).start()
        else:
            return func(*args, **kwargs)

    def __init__(self, server):
        """
        Constructor.

        :param server: the local server
        """
        self.server = server
        self.oneway = oneways

    def __getattr__(self, name):
        """
        Determine whether or not we should redirect the call to the local or the remote server

        :param name: the name of the function to call
        :returns: function -- function to be actually called to perform the action
        """
        if name in MPIRedirect.noproxy:
            raise AttributeError(name)
        def localcall(*args, **kwargs):
            """
            A call to a local location
            """
            return LocalRedirect.localCall(self, name, *args, **kwargs)
        return localcall

    def __getinitargs__(self):
        """
        For pickling

        :returns: list containing the rank
        """
        return [self.server]

    def __getstate__(self):
        """
        For pickling

        :returns: dictionary containing the rank and the oneway list
        """
        return {"oneway": self.oneway}

    def __setstate__(self, state):
        """
        For pickling

        :param state: the dictionary provided by the *__getstate__* method
        """
        self.oneway = state["oneway"]
        # No need to save the server, as it is impossible to restore it anyway
