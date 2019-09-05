# -*- coding: Latin-1 -*-
"""
Server for DEVS simulation
"""
from .basesimulator import BaseSimulator
from .controller import Controller
from . import middleware
from .threadpool import ThreadPool
import threading

import sys
from .util import *
from .logger import *

class Server(object):
    """
    A server to host MPI, will delegate all of its calls to the active simulation kernel.
    """
    # Don't forward some of the internally provided functions, but simply raise an AttributeError
    noforward = frozenset(["__str__", "__getstate__", "__setstate__", "__repr__"])

    def __init__(self, name, totalSize):
        """
        Constructor

        :param name: the name of the server, used for addressing (in MPI terms, this is the rank)
        :param totalSize: the total size of the network in which the model lives
        """
        self.name = name
        self.kernel = None
        self.size = totalSize
        self.proxies = [MPIRedirect(i) for i in range(totalSize)]
        from .MPIRedirect import LocalRedirect
        self.proxies[name] = LocalRedirect(self)
        self.queuedMessages = []
        self.queuedTime = None
        if totalSize > 1:
            self.threadpool = ThreadPool(2)
            self.bootMPI()

    def getProxy(self, rank):
        """
        Get a proxy to a specified rank. 
        
        This rank is allowed to be the local server, in which case a local shortcut is created.

        :param rank: the rank to return a proxy to, should be an int
        :returns: proxy to the server, either of type MPIRedirect or LocalRedirect
        """
        return self.proxies[rank]

    def checkLoadCheckpoint(self, name, gvt):
        """
        Reconstruct the server from a checkpoint.

        :param name: name of the checkpoint
        :param gvt: the GVT to restore to
        :returns: bool -- whether or not the checkpoint was successfully loaded
        """
        rank = self.name
        #assert debug("Accessing file " + str("%s_%s_%s.pdc" % (name, gvt, rank)))
        try:
            infile = open("%s_%s_%s.pdc" % (name, gvt, rank), 'r')
            pickle.load(infile)
            return True
        except KeyboardInterrupt:
            # If the user interrupts, still reraise
            raise
        except Exception as e:
            # Something went wrong
            print(("Error found: " + str(e)))
            return False
        
    def loadCheckpoint(self, name, gvt):
        """
        Reconstruct the server from a checkpoint.

        :param name: name of the checkpoint
        :param gvt: the GVT to restore to
        """
        rank = self.name
        #assert debug("Accessing file " + str("%s_%s_%s.pdc" % (name, gvt, rank)))
        infile = open("%s_%s_%s.pdc" % (name, gvt, rank), 'r')
        self.kernel = pickle.load(infile)
        self.kernel.server = self
        from .MPIRedirect import LocalRedirect
        self.proxies[self.name] = LocalRedirect(self)
        infile.close()
        #assert debug("Closing file")
        self.kernel.loadCheckpoint()

    def setPickledData(self, pickled_data):
        """
        Set the pickled representation of the model.

        For use on the controller itself, as this doesn't need to unpickle the model.

        :param pickled_data: the pickled model
        """
        self.kernel.pickledModel = pickled_data

    def prepare(self, scheduler):
        """
        Prepare the server to receive the complete model over MPI

        :param scheduler: the scheduler to use
        """
        data = middleware.COMM_WORLD.bcast(None, root=0)
        if data is not None:
            self.saveAndProcessModel(data, scheduler)
            middleware.COMM_WORLD.barrier()

    def saveAndProcessModel(self, pickledModel, scheduler):
        """
        Receive the model and set it on the server, but also saves it for further reinitialisation.

        :param pickledModel: pickled representation of the model
        :param scheduler: the scheduler to use
        """
        self.sendModel(pickle.loads(pickledModel), scheduler)
        self.kernel.pickledModel = pickledModel

    def getName(self):
        """
        Returns the name of the server

        Is practically useless, since the server is previously addressed using its name. This does have a use as a ping function though.
        """
        # Actually more of a ping function...
        return self.name

    # All calls to this server are likely to be forwarded to the currently
    #  active simulation kernel, so provide an easy forwarder
    def __getattr__(self, name):
        """
        Remote calls happen on the server object, though it is different from the simulation kernel itself. Therefore, forward the actual function call to the correct kernel.

        :param name: the name of the method to call
        :returns: requested attribute
        """
        # For accesses that are actually meant for the currently running kernel
        if name in Server.noforward:
            raise AttributeError()
        return getattr(self.kernel, name)

    def processMPI(self, data, comm, remote):
        """
        Process an incomming MPI message and reply to it if necessary

        :param data: the data that was received
        :param comm: the MPI COMM object
        :param remote: the location from where the message was received
        """
        # Receiving a new request
        resendTag = data[0]
        function = data[1]
        args = data[2]
        kwargs = data[3]
        result = getattr(self, function)(*args, **kwargs)
        if resendTag is not None:
            if result is None:
                result = 0
            comm.send(result, dest=remote, tag=resendTag)

    def listenMPI(self):
        """
        Listen for incomming MPI messages and process them as soon as they are received
        """
        comm = middleware.COMM_WORLD
        status = middleware.MPI.Status()
        while 1:
            #assert debug("[" + str(comm.Get_rank()) + "]Listening to remote " + str(middleware.MPI.ANY_SOURCE) + " -- " + str(middleware.MPI.ANY_TAG))
            # First check if a message is present, otherwise we would have to do busy polling
            data = comm.recv(source=middleware.MPI.ANY_SOURCE, tag=middleware.MPI.ANY_TAG, status=status)
            tag = status.Get_tag()
            #assert debug("Got data from " + str(status.Get_source()) + " (" + str(status.Get_tag()) + "): " + str(data))
            if tag == 0:
                # Flush all waiters, as we will never receive an answer when we close the receiver...
                self.finishWaitingPool()
                break
            elif tag == 1:
                # NOTE Go back to listening ASAP, so do the processing on another thread
                if data[1] == "receive" or data[1] == "receiveAntiMessages":
                    self.threadpool.add_task(Server.processMPI, self, list(data), comm, status.Get_source())
                else:
                    # Normal 'control' commands are immediately executed, as they would otherwise have the potential to deadlock the node
                    threading.Thread(target=Server.processMPI, args=[self, list(data), comm, status.Get_source()]).start()
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
        
    def finishWaitingPool(self):
        """
        Stop the complete MPI request queue from blocking, used when stopping simulation is necessary while requests are still outstanding.
        """
        for i in MPIRedirect.waiting:
            try:
                i.set()
            except AttributeError:
                # It was not a lock...
                pass
            except KeyError:
                # It was deleted in the meantime
                pass

    def bootMPI(self):
        """
        Boot the MPI receivers when necessary, on an other thread to prevent blocking
        """
        if self.size > 1:
            listener = threading.Thread(target=Server.listenMPI, args=[self])
            # Make sure that this is a daemon on the controller, as otherwise this thread will prevent the atexit from stopping
            # Though on every other node this should NOT be a daemon, as this is the only part still running

            if middleware.COMM_WORLD.Get_rank() == 0:
                listener.daemon = True
            listener.start()

    def sendModel(self, data, scheduler):
        """
        Receive a complete model and set it.

        :param data: a tuple containing the model, the model_ids dictionary, scheduler name, and a flag for whether or not the model was flattened to allow pickling
        :param scheduler: the scheduler to use
        """
        model, model_ids, flattened = data
        if self.name == 0:
            self.kernel = Controller(self.name, model, self)
        else:
            self.kernel = BaseSimulator(self.name, model, self)
        self.kernel.sendModel(model, model_ids, scheduler, flattened)

    def finish(self):
        """
        Stop the currently running simulation
        """
        sim = self.kernel
        with sim.simlock:
            # Shut down all threads on the topmost simulator
            sim.finished = True
            sim.shouldrun.set()
            self.finishWaitingPool()

            # Wait until they are done
            sim.simFinish.wait()

    def queueMessage(self, time, model_id, action):
        """
        Queue a delayed action from being sent, to make it possible to batch them.
        
        Will raise an exception if previous messages form a different time were not yet flushed!
        This flushing is not done automatically, as otherwise the data would be received at a further timestep
        which causes problems with the GVT algorithm.

        :param time: the time at which the action happens
        :param model_id: the model_id that executed the action
        :param action: the action to execute (as a string)
        """
        if self.queuedTime is None:
            self.queuedTime = time
        elif time != self.queuedTime:
            raise DEVSException("Queued message at wrong time! Probably forgot a flush")
        self.queuedMessages.append([model_id, action])

    def flushQueuedMessages(self):
        """
        Flush all queued messages to the controller. This will block until all of them are queued.
        It is required to flush all messages right after all of them happened and this should happen within the critical section!
        """
        if self.queuedTime is not None:
            self.getProxy(0).massDelayedActions(self.queuedTime, self.queuedMessages)
            self.queuedMessages = []
            self.queuedTime = None
