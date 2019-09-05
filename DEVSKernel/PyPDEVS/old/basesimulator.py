# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# basesimulator.py --- 'Plain' DEVS Model Simulator
#                     --------------------------------
#                            Copyright (c) 2013
#                             Hans  Vangheluwe
#                            Yentl Van Tendeloo
#                       McGill University (Montréal)
#                     --------------------------------
# Version 2.0                                       last modified: 05/03/2013
#  - Split up the base simulator
#    
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


from .solver import Solver

#cython from message cimport Message, NetworkMessage
from .message import Message, NetworkMessage #cython-remove

from .util import *
from .messageScheduler import MessageScheduler
from .DEVS import *
import threading
import time
import sys
import logging
from . import middleware
from .logger import *
import cProfile
try:
    import pickle as pickle
except ImportError:
    import pickle
from copy import deepcopy, copy
import random
from .tracers import Tracers
import time

def never_ending_termination_function(time, model):
    """
    A termination function that never ends, used for local simulation
    """
    return False

def ending_termination_function(time, model):
    """
    A termination function that immediately ends, used when a model must stop ASAP
    """
    return True

class BaseSimulator(Solver):
    """
    The BaseSimulator class, this is the core of the complete simulation and
    is exported with Pyro as the representation of a server.
    """
    def __init__(self, name, model = None):
        """
        Constructor
        Args:
            name - the desired name of the server, this is the one used in the models
                   and will be used within the Pyro nameserver
        """
        Solver.__init__(self)
        self.hasSent = False
        self.inits()
        self.finish_sent = False
        self.reverts = 0
        self.transitioning = set()
        self.model = model
        self.tracers = Tracers()
        self.modelname_cache = {}
        self.directConnected = False
        self.irreversible = False
        self.sendmsgcounter = 0
        self.depends = set()
        self.revertion_limit = 100
        self.checkpoint_restored = False

        self.name = str(name)

    def __setstate__(self, retdict):
        """
        Reset the state with pickle
        """
        self.inits()

        for i in retdict:
            setattr(self, i, retdict[i])
        self.tracers = Tracers()
        # Overwrite variables for GVT algorithm
        self.color = False
        self.transitioning = set()
        self.V = {}
        self.Tmin = float('inf')
        self.controlmsg = None
        self.waiting = 0
        self.totalCounter = 0
        self.sentAlready = []
        self.checkpoint_restored = True

        self.setGlobals(address=self.address, 
                        loglevel=self.loglevel, 
                        verbose=self.verbose, 
                        xml=self.xml, 
                        vcd=self.vcd, 
                        controller=self.controller_name, 
                        seed=self.seed, 
                        checkpointfrequency=self.checkpointFreq, 
                        gvtfrequency=self.GVT_freq, 
                        statesaver=self.state_saving, 
                        kernels=self.kernels,
                        manualCopy=self.manualCopy,
                        allowNested=self.allowNested,
                        disallowIrreversible=self.disallowIrreversible,
                        realtime=self.realtime,
                        inputReferences=self.realTimeInputPortReferences)

    def __getstate__(self):
        """
        Fetch a pickle-compliant representation of the model
        """
        retdict = {}
        for i in dir(self):
            if getattr(self, i).__class__.__name__ in ["instancemethod", "lock", "_Event", "Thread", "method-wrapper", "builtin_function_or_method"]:
                # unpicklable, so don't copy it
                continue
            elif (str(i) not in ["sentAlready", "tracers", "inputScheduler", "inqueue", "actions", "transitioning", "modelname_cache"]) and (not str(i).startswith("__")):
                retdict[str(i)] = getattr(self, i)
                # ELSE
                # wastefull to pickle, since they contain information about the future that will
                #  certainly be replicated when restoring from checkpoint
            elif (str(i) == "outputQueue") and (self.irreversible):
                # If the model is irreversible, we should also save the outputQueue
                retdict[str(i)] = getattr(self, i)
        return retdict

    def inits(self):
        """
        Initialise the simulation kernel, this is split up from the constructor to
        make it possible to reset the kernel without reconstructing the kernel.
        """
        self.model = None
        self.model_ids = {}
        self.actions = []
        self.actionlock = threading.Lock()
        self.shouldrun = threading.Event()
        self.finishCheck = threading.Event()
        self.waiting = 0
        self.waitingLock = threading.Lock()
        self.emptyQueue = threading.Event()
        self.visited = False
        self.termination_server = False
        self.termination_time = float('inf')
        self.termination_name = ""
        self.termination_local = True

        self.procTransition = True

        self.to_reschedule = []

        self.termination_condition = never_ending_termination_function;
        self.reverted = False
        self.blockOutgoing = False

        # Mattern's GVT algorithm
        # False = white, True = red
        self.color = False
        self.V = {}
        self.Tmin = float('inf')
        self.controlmsg = None
        self.GVT = -float('inf')
        #self.GVT = 0

        self.prevtime = (0, 0)
        self.sentAlready = []

        self.inputScheduler = MessageScheduler()
        self.outputQueue = []

        self.totalCounter = 0

        self.simlock = threading.Lock()
        self.nestedlock = threading.Lock()
        # Acquire the lock ASAP, to prevent simulation during/after shutdown
        # it has to be released as soon as the simulation is commenced
        self.simlock.acquire()
        self.nestedlock.acquire()
        self.unprocessed = False
        self.waitForGVT = threading.Event()
                
        self.inmsg = threading.Event()
        self.inlock = threading.Lock()
        self.inqueue = []

        self.Vchange = threading.Event()

        self.simFinish = threading.Event()
        self.queueFinish = threading.Event()

        self.finished = False

        self.GVTfinished = threading.Event()
        self.GVTcomp = threading.Lock()
        self.nestingLock = threading.Lock()

    def setTerminationServer(self, name):
        """
        Sets the name of the kernel that is responsible for providing the termination
        of the simulation.
        Args:
            name - the name of the kernel
        """
        self.termination_name = name

    def setTerminationTime(self, time):
        """
        Sets the time at which simulation should stop, setting this will override
        the local simulation condition.
        Args:
            time - the time at which the simulation should stop
        """
        self.termination_time = time
        self.termination_local = False

    def getLocationList(self, currentset):
        """
        Returns the list of all models that are present in this simulation kernel
        """
        currentset.add(self.name)
        return self.model.getLocationList(currentset)

    def setID(self):
        """
        Sets the ID's of the kernel to those specified in its root model
        """
        self.model_ids = self.model.model_ids

    def getComponentSet(self):
        """
        Returns the list of all components present in the current simulation kernel
        """
        model = self.model
        retvalue = [[i.location, i.model_id] for i in model.componentSet]
        return retvalue

    def setAllData(self):
        """
        Calls setData on every model in the current simulation
        """
        for i in self.model.componentSet:
            i.setData()

    def getModelName(self):
        """
        Returns the name of the rootmodel of the simulation kernel
        """
        return self.model.getModelName()

    def getModelFullName(self):
        """
        Returns the name of the rootmodel of the simulation kernel
        """
        return self.model.getModelFullName()

    def buildList(self):
        """
        Configures the list of all models present in the simulation kernel, needed
        make a fast event heap possible.
        """
        id_fetch = {}
        for model_id in self.model_ids:
            model = self.model_ids[model_id]
            id_fetch[model.model_id] = [model.timeNext, model.model_id, True, model]
        self.setID_fetch(id_fetch)
 
    def receiveExternal(self, msg):
        """
        Make this simulation kernel receive an external message
        (external being 'from another simulation kernel').

        This function will not process the message itself, but simply add it to
        a list that gets processed elsewhere, to limit the number of threads and
        make it possible for the function to return quickly.
        """
        # Prevent stopping the simulation kernel
        self.unprocessed = True
        assert debug("Waiting on lock")
        self.inlock.acquire()
        assert debug("Received external message: " + str(msg))
        self.inqueue.append(msg)
        # Notify that there is a new message
        self.inmsg.set()
        self.inlock.release()
        self.shouldrun.set()
 
    def externalQueueProcessor(self):
        """
        A process that should run on a seperate thread. It processes all messages
        put into the inputQueue by the 'receiveExternal' function.

        It doesn't use busy waiting and can only be finished by setting the
        finished variable of the simulation kernel.

        Will also emmit an event as soon as the queue is empty, to notify the
        simulation kernel that it may progress. This thread must ALWAYS be called
        before a simulation step, because incomming message need to be processed
        as soon as possible (they might be anti-messages).
        """
        while True:
            self.inmsg.wait()
            if self.finished:
                break
            self.inmsg.clear()
            self.inlock.acquire()
            #if len(self.inqueue) > 0:
            while len(self.inqueue) > 0:
                # Make sure the message is only popped as soon as it is completely processed
                evt = self.inqueue[0]
                self.inlock.release()

                # Process the message
                self.externalInput(evt)

                self.inlock.acquire()
                self.inqueue.pop(0)
            self.emptyQueue.set()
            self.inlock.release()
        self.queueFinish.set()

    def notifySend(self, destination, timestamp, color):
        """
        Notify the simulation kernel of the sending of a message. Needed for
        GVT calculation.
        Args:
            destination - the name of the simulation kernel that has to receive
                          the message that is being sent
            timestamp - the simulation time at which the message is sent
            color - the color of the message being sent
                    (due to Mattern's algorithm)
        """
        # Keep a totalCounter for ending the simulation
        self.totalCounter += 1
        assert debug("Sending message with color: " + str(color) + " at time " + str(timestamp) + " to " + str(destination))
        if color == False:
            self.V[destination] = self.V.get(destination, 0) + 1
            assert debug("Increasing vector to " + str(self.V))
        else:
            self.Tmin = min(self.Tmin, timestamp)
            assert debug("Decreasing Tmin to " + str(self.Tmin))

    def notifyReceive(self, color):
        """
        Notify the simulation kernel of the receiving of a message. Needed for
        GVT calculation.
        Args:
            color - the color of the received message
                    (due to Mattern's algorithm)
        """
        assert debug("Received message with color: " + str(color))
        # Keep a totalCounter for ending the simulation
        self.totalCounter -= 1
        if color == False:
            self.V[self.name] = self.V.get(self.name, 0) - 1
            assert debug("Decreasing vector to " + str(self.V))
            self.Vchange.set()

    def setNextLP(self, location, size):
        """
        Set the location that is next to this simulation kernel, used
        to construct a ring algorithm
        Args:
            location - the name of the next simulation kernel
        """
        # Do this oneway instead of async, as we don't need the results anyway
        self.nextLP = getProxy(location)
        self.size = size
        makeOneway(self.nextLP, "receiveControl")
        makeOneway(self.nextLP, "setGVT")

    def waitUntilOK(self):
        """
        Returns as soon as all messages to this simulation kernel are received.
        Needed due to Mattern's algorithm. Uses events to prevent busy looping.
        """
        while not (self.V.get(self.name, 0) + self.controlmsg[2].get(self.name, 0) <= 0):
            self.nestedlock.release()
            self.simlock.release()
            # Use an event to prevent busy looping
            self.Vchange.wait()
            self.Vchange.clear()
            # Free the lock
            self.simlock.acquire()
            self.nestedlock.acquire()

    def receiveControl(self, msg):
        """
        Process an incomming control message for GVT calculation.
        Args:
            msg - the control message
        """
        assert debug("Got control message: " + str(msg) + " at " + str(self.name))
        assert debug("Own vector: " + str(self.V))
        self.controlmsg = msg
        m_clock = self.controlmsg[0]
        m_send = self.controlmsg[1]
        count = self.controlmsg[2]

        self.inlock.acquire()
        if len(self.inqueue) > 0:
            minfound = float('inf')
            # This shouldn't require locking, as we only append at the end elsewhere
            for i in self.inqueue:
                if i.timestamp[0] < minfound:
                    minfound = i.timestamp[0]
                    m_clock = min(m_clock, minfound)
        self.inlock.release()

        assert debug("TimeNext: " + str(self.model.timeNext[0]))
        assert debug("TimeLast: " + str(self.model.timeLast[0]))
        assert debug("PrevTime: " + str(self.prevtime[0]))
        self.simlock.acquire()
        self.nestedlock.acquire()
        if self.name == self.controller_name:
            assert debug("Waiting until OK")
            self.waitUntilOK()
            assert debug("OK")
            # This newtime calculation should happen AFTER the waiting, otherwise all intermediate messages are ignored!
            newtime = min(self.model.timeNext[0], self.model.timeLast[0], self.prevtime[0])
            if allZeroDict(count) and self.color == False:
                GVT = min(m_clock, m_send)
                assert debug("FOUND GVT: " + str(GVT))
                self.color = False
                assert debug("Set color to " + str(self.color))
                self.nestedlock.release()
                self.simlock.release()
                self.setGVT(GVT)
                # Don't lock it again
                return
            else:
                assert debug("GVT not found after 1 round, progressing (possibly color == True)")
                new_count = {}
                addDict(new_count, self.V)
                addDict(new_count, count)
                assert debug("Vector: " + str(new_count))
                msg = [newtime, min(m_send, self.Tmin), new_count]
                assert debug("Controller sends out msg " + str(msg))
                self.color = False
                assert debug("Set color to " + str(self.color))
                assert debug("Cleared V")
                self.V = {}
                self.nextLP.receiveControl(msg)
        else:
            newtime = min(self.model.timeNext[0], self.model.timeLast[0], self.prevtime[0])
            if self.color == False:
                # Become Red
                self.Tmin = float('inf')
                self.color = True
                assert debug("Set color to " + str(self.color))
                assert debug("Set Tmin to " + str(self.Tmin))
            elif self.color == True:
                # Become White
                self.color = False
                assert debug("Set color to " + str(self.color))
            assert debug("Waiting until OK")
            self.waitUntilOK()
            assert debug("OK")
            new_count = {}
            addDict(new_count, self.V)
            addDict(new_count, count)
            assert debug("Cleared V")
            self.V = {}
            msg = [min(m_clock, newtime), min(m_send, self.Tmin), new_count]
            assert debug("Sending msg " + str(msg))
            self.nextLP.receiveControl(msg)
        self.nestedlock.release()
        self.simlock.release()

    def setGVT(self, GVT):
        """
        Sets the GVT of this simulation kernel. This value should not be smaller than
        the current GVT (this would be impossible for a correct GVT calculation). Also
        cleans up the input, output and state buffers used due to time-warp.
        Furthermore, it also processes all messages scheduled before the GVT.
        Args:
            GVT - the desired GVT
        """
        # GVT is just a time, it does not contain an age field!
        assert debug("Got setGVT")
        if GVT < self.GVT:
            raise DEVSException("GVT cannot decrease from " + str(self.GVT) + " to " + str(GVT) + "!")
        if GVT == self.GVT:
            # The same, so don't do the batched fossil collection
            # This will ALWAYS happen at the controller first, as this is the one that gets called with the GVT update first
            #   if the value should change, it will do a complete round and finally set the variable
            #   if the value stays the same, we can stop immediately
            self.GVTdone()
            return
        self.simlock.acquire()
        self.nestedlock.acquire()
        assert debug("Set GVT to " + str(GVT))
        self.GVT = GVT

        nqueue = []
        self.inputScheduler.cleanup((GVT, 1))

        self.performActions(GVT)

        # outputQueue is NOT sorted!
        # Why is outputQueue not sorted?
        nqueue = [i for i in self.outputQueue if i.timestamp[0] >= GVT]
        self.outputQueue = nqueue

        self.model.setGVT(GVT)
        # Make a checkpoint too
        if self.checkpointCounter == self.checkpointFreq:
            self.checkpoint()
            self.checkpointCounter = 0
        else:
            self.checkpointCounter += 1
        assert debug("Forward GVT message")
        self.nextLP.setGVT(GVT)
        self.nestedlock.release()
        self.simlock.release()

    def externalInput(self, msg):
        """
        Processes an external input message, this should NOT be called manually as
        it will immediately process the message before all other messages that are
        passed 'the right way'.
        Args:
            msg - the message to be processed
        """
        # Now all incomming message checking should happen here!
        # NOTE make sure that the notifyReceive and simlock don't deadlock!
        messagetype = msg.messagetype
        if messagetype != 3:
            raise DEVSException("Non-data message received from external node: " + str(msg))
        self.simlock.acquire()
        self.nestedlock.acquire()
        self.notifyReceive(msg.color)
        assert debug("Processing external msg: " + str(msg))
        if msg.antimessage:
            self.inputScheduler.unschedule(msg)
            if msg.timestamp <= self.prevtime:
                self.revert(msg.timestamp)
                self.unprocessed = True
            assert debug("Got anti message for UUID " + str(msg.uuid))
            assert debug("  prevtime: " + str(self.prevtime))
            assert debug("  sentAlready: " + str(len(self.sentAlready)))
            # NOTE an anti-message should not pass to further models, as direct
            #      connection will make sure that all these steps are one-step
            #      thus preventing the need for propagation.
            self.nestedlock.release()
            self.simlock.release()
            return
        elif (msg.timestamp <= self.prevtime) and (messagetype == 3):
            # Message arrives after a transition, so we need to revert
            self.revert(msg.timestamp)

        # Now the message is an 'ordinary' message, just schedule it for processing
        # Only process data messages, other messages should not be sent externally
        self.unprocessed = True
        self.shouldrun.set()
        self.inputScheduler.schedule(msg)
        self.nestedlock.release()
        self.simlock.release()

    def revert(self, time):
        """
        Revert the current simulation kernel to the specified time. All messages
        sent after this time will be invalidated, all states produced after this
        time will be removed.
        Args:
            time - the desired time for revertion. This time MUST be >= current GVT
        """
        # Don't assert that it is not irreversible, as an irreversible component could theoretically still be reverted, but this MUST be to a state when it was not yet irreversible
        # Reverting the complete LP
        assert debug("Removing actions from time " + str(time))
        self.reverts += 1
        proxy = getProxy(self.controller_name)
        #TODO possible speedup if this becomes oneway?
        # MPI guarantees us ordered delivery, so this message will arrive and be processed before other actions
        # and thus also locking the actionLock in the controller, preventing conflicts
        proxy.removeActions(self.model.getModelFullName(), time)
        # Also revert the input message scheduler
        self.inputScheduler.revert(time)
        # Now revert all local models
        self.model.revert(time)
        assert debug("Reverted all models")
        # There is probably an unprocessed message by now (as otherwise we wouldn't need a revertion)
        self.unprocessed = True

        # Clear sentAlready, since we are doing a complete revertion
        self.sentAlready = []
        assert debug("Setting reverted = True")
        if (not self.hasSent) and self.prevtime == time:
            self.blockOutgoing = False
        else:
            self.blockOutgoing = True
        #self.blockOutgoing = True
        self.reverted = True
        self.prevtime = tuple(time)

        # Invalidate all output messages after or at time
        nqueue = []
        for i in self.outputQueue:
            # Do not invalidate messages at this time itself, as they are processed in this time step and not generated in this timestep
            if i.timestamp > time:
                cleaned = {}
                for j in list(i.content.keys()):
                    cleaned[j] = None
                loc = i.destination
                #TODO does this work with our proxy objects?
                assert debug("Invalidating message " + str(i.uuid))
                antimsg = NetworkMessage(Message(i.timestamp, i.messagetype, cleaned), True, i.uuid, self.color, loc)
                # A List means that it has to go through the proxy immediately
                self.notifySend(loc, antimsg.timestamp[0], antimsg.color)
                # Not async as we don't want lots of threads
                remote = getProxy(loc)
                makeOneway(remote, "send")
                remote.send(None, antimsg, external=True)
            else:
                nqueue.append(i)
        self.outputQueue = nqueue
        self.shouldrun.set()

    def send(self, model_id, msg, external = False):
        """
        Send a message to a specific model
        Args:
            model_id - identifier of the model, can be either an ID or None (denotes root model at this simulator)
            msg - message to pass
            external - whether or not this message was received over the network
        Returns:
            the message that was generated, None in case it was an external call
        """
        model = self.model if (model_id is None) else self.model_ids[model_id]

        if external:
            moddata = {}
            for entry in msg.content:
                # Remap the port ID to the local ports
                inport = model.remapNum2Port[entry]
                moddata[inport] = msg.content[entry]
            # Overwrite the original message
            msg.content = moddata
            self.receiveExternal(msg)
        elif isinstance(model, CoupledDEVS):
            # Simple local simulation
            return self.coupledReceive(model, msg)
        elif isinstance(model, AtomicDEVS):
            return self.atomicReceive(model, msg)

    def getTimeNext(self):
        """
        Returns the timeNext of the rootmodel (and thus of this simulation kernel)
        Returns:
            timeNext
        """
        return self.model.timeNext

    def setTerminationCondition(self, termination_condition):
        """
        Sets the termination condition of this simulation kernel. This means that this kernel
        will be responsible for signalling all other kernels that simulation may be stopped
        as soon as they have progressed as far as this kernel.
    
        This signalling should happen through the controller.
        Args:
            termination_condition - a function that takes 2 parameters
                                       time - the current simulation time
                                       model - the local model
                                    and returns a boolean whether or not simulation
                                    can stop in this situation
        """
        self.termination_condition = termination_condition
        # Mark this server as the one responsible for stopping the simulation
        self.termination_server = True

    def check(self, clocktime = -1):
        """
        Checks wheter or not simulation should still continue. This will either
        call the global time termination check, or the local state termination
        check, depending on configuration.

        Using the global time termination check is a lot FASTER and should be used
        if possible.
        Args:
            clocktime - the time at which this check should happen
        """
        # Return True = stop simulation
        # Return False = continue simulation

        if clocktime == -1:
            clocktime = self.model.timeNext[0]
        if self.termination_local:
            # Only pass the time, not the age, as this is an implementation detail
            # that the user should not be aware of
            if self.termination_condition(clocktime, self.model):
                cnt = True
                try:
                    cnt = self.termination_condition(self.inputScheduler.readFirst().timestamp[0], self.model)
                except IndexError:
                    # No more messages in input
                    pass
            else:
                cnt = False

            # Notify all others that simulation may finish
            if self.termination_server and cnt and not self.finish_sent:
                # Local conditions _currently_ state that simulation can finish
                # due to timewarp, we aren't sure if this is actually the case,
                # so wait until GVT has arrived to make a certain guess
                getProxy(self.controller_name).finishAtTime(clocktime)
                self.finish_sent = True
                self.term_time = clocktime
                # Keep progressing, otherwise GVT calculation might stall
                #TODO can't we just return True to keep this core idle?
                return False
            elif self.termination_server and not cnt and self.finish_sent and (self.term_time > clocktime):
                getProxy(self.controller_name).invalidateFinishAtTime()
                self.finish_sent = False
                self.term_time = float('inf')
            elif self.termination_server and cnt and self.finish_sent:
                # Keep going to advance GVT
                return False
        else:
            # Much simpler checks in case the global simulation time is requested
            if clocktime > self.termination_time:
                cnt = True
                try:
                    cnt = self.inputScheduler.readFirst().timestamp[0] > self.termination_time
                except IndexError:
                    pass
            else:
                cnt = False
        return cnt

    def invalidateFinishAtTime(self):
        """
        Invalidate a previously set finish time
        """
        self.termination_time = float('inf')

    def finishAtTime(self, clock):
        """
        Signal this kernel that it may stop at the provided time
        Args:
            clock - the time to stop
        """
        if clock < self.termination_time:
            self.termination_time = clock

    def finishSimulation(self):
        """
        Changes the termination condition of all simulation kernels to
        stop the simulation. This uses a ring algorithm.
        """
        if self.termination_condition == ending_termination_function:
            # The end of the ring algorithm
            assert debug("Ending finishSimulation")
            return
        self.termination_condition = ending_termination_function
        self.termination_server = False
        assert debug("Sending finishSimulation to the next simulator in the ring")
        makeOneway(self.nextLP, "finishSimulation")
        self.nextLP.finishSimulation()

    def action(self, action):
        """
        Perform an action immediatly at this kernel
        """
        exec(action)

    def delayedAction(self, time, model, action):
        """
        Perform an irreversible action (I/O, prints, global messages, ...). All
        these actions will be performed in the order they should be generated
        in a non-distributed simulation. All these messages might be reverted in
        case a revertion is performed by the calling model.

        Args:
            time - the simulation time at which this command was requested
            model - the model that issued this command
            action - the command that must be executed. This should be a string
                     that is executable in the context of the controller
        """
        assert debug("Adding action for time " + str(time) + ", GVT = " + str(self.GVT))
        if time[0] < self.GVT:
            raise DEVSException("Cannot execute action before the GVT! (time = " + str(time) + ")")
        self.actionlock.acquire()
        self.actions.append([time, model, action])
        self.actionlock.release()

    def removeActions(self, model, time):
        """
        Remove all actionsn specified by a model, starting from a specified time.
        This function should be called when the model is reverted and its actions
        have to be undone
        Args:
            model - the name of the reverted model
            time - the time to which is reverted, should not be smaller than GVT
                   as these have already been executed.
        """
        if time[0] < self.GVT:
            raise DEVSException("Cannot remove action from before the GVT!")
        self.actionlock.acquire()
        #TODO Check this, might cause problems for local termination conditions
        if self.termination_time >= time[0] and model == self.termination_name:
            self.termination_time = float('inf')
        # Actions are unsorted, so we have to go through the complete list
        self.actions = [i for i in self.actions if not ((i[1] == model or model == "*") and (i[0] >= time))]
        self.actionlock.release()

    def performActions(self, gvt = float('inf')):
        """
        Perform all irreversible actions up to the provided time.
        If time is not specified, all queued actions will be executed (in case simulation is finished)
        Args:
            gvt - time up to which all actions should be executed
        """
        if gvt >= self.termination_time and self.termination_local:
            # Should allow finishing
            # But crop of to the termination_time as we might have simulated slightly too long
            gvt = self.termination_time - EPSILON
            self.finishSimulation()
        self.actionlock.acquire()
        if gvt != float('inf'):
            # Only take the relevant part to sort, this will decrease complexity
            lst = []
            remainder = []
            for i in self.actions:
                if i[0][0] < gvt:
                    lst.append(i)
                else:
                    remainder.append(i)
        else:
            lst = self.actions
            remainder = []
        self.actions = remainder
        # Release the lock ASAP, to allow other actions to be performed
        self.actionlock.release()

        # Sort on time first, then on MESSAGE, not on model
        lst.sort(key=lambda i: [i[0], i[2]])

        # Now execute each action in order
        for i in lst:
            exec(i[2])

    def setGlobals(self, address, loglevel, verbose, xml, vcd, controller, seed, checkpointfrequency, gvtfrequency, statesaver, kernels, manualCopy, allowNested, disallowIrreversible, realtime, inputReferences):
        """
        Configure all 'global' variables for this kernel
        Args:
            address - address of the syslog server
            loglevel - level of logging library
            verbose - whether or not verbose tracing should happen
            xml - whether or not xml tracing should happen
            vcd - whether or not vcd tracing should happen
            controller - name of the actual controller
            seed - seed for random number generation
            checkpointfrequency - frequency at which checkpoints should be made
            gvtfrequency - frequency at which GVT calculations should happen
            statesaver - statesaving method
            kernels - number of simulation kernels in total
            manualCopy - whether or not a state copy function is defined by the user
            allowNested - should nested simulation be allowed
        """
        self.verbose = verbose
        self.xml = xml
        self.vcd = vcd
        self.address = address
        self.loglevel = loglevel
        self.seed = seed
        # Print immediately if real time simulation is done
        self.tracers.setImmediate(realtime)
        self.tracers.setVerbose(verbose)
        self.kernels = kernels
        self.state_saving = statesaver
        self.manualCopy = manualCopy
        self.allowNested = allowNested
        self.disallowIrreversible = disallowIrreversible
        self.realtime = realtime
        self.realTimeInputPortReferences = inputReferences
        #TODO 
        #setLogger(self.name, address, loglevel)
        self.tracers.setXML(xml)
        self.tracers.setVCD(vcd)
        self.checkpointFreq = checkpointfrequency
        self.checkpointCounter = 0
        self.controller_name = controller
        self.GVT_freq = gvtfrequency
        if self.controller_name == self.name and not realtime:
            # We seem to be the controller
            # Start up the GVT algorithm then
            self.eventGVT = threading.Event()
            self.runGVT = True
            self.runGVTthread()
        random.seed(seed)

    def setVerbose(self, verbose, outfile = None, restore=False):
        self.tracers.setVerbose(verbose, outfile, restore)

    def alreadySentCheck(self, message):
        """
        Check whether or not a message has already been sent in the current simulationstep
        Args:
            message - the message to check, only the UUID will be used to check
        Return:
            bool - is this message already sent?
        """
        uuid = message.uuid
        for i in self.sentAlready:
            if uuid == i:
                return True
        return False

    #TODO this method can use some heavy optimisations
    def findMessage(self, clock):
        """
        Search for the first message that must be sent next
        Args:
            clock - current simulation time
        Return:
            (clock, message) - either (clock, None) if no message must be sent
                               before clock, or the message that has to be sent
                               together with the simulation time.
        """
        msg = None
        assert debug("Searching first message to process")
        try:
            message = self.inputScheduler.readFirst()
        except IndexError:
            assert debug("Out of bounds, no new messages to process")
            return clock, msg
        assert debug("Checking message " + str(message))
        #if (self.prevtime == message.timestamp) and ((len(self.sentAlready) > 0) or (self.reverted)):
        # Messages for this iteration should still be sent even if there is a difference of EPSILON
        if (abs(self.prevtime[0] - message.timestamp[0]) < EPSILON and (self.prevtime[1] == message.timestamp[1])) and ((len(self.sentAlready) > 0) or (self.reverted)):
            if self.alreadySentCheck(message):
                #TODO can't we remove this already SentCheck?
                assert debug("Already sent this message")
                self.inputScheduler.removeFirst()
                return self.findMessage(clock)
            assert debug("flow-through message found: " + str(message))
            msg = message
            self.sentAlready.append(message.uuid)
            clock = self.prevtime
        elif self.prevtime < message.timestamp <= clock:
            assert debug("Found new base message: " + str(message))
            if self.sentAlready == []:
                assert debug("Is clean, advancing clock")
                msg = message
                self.sentAlready = [message.uuid]
                self.prevtime = message.timestamp
                clock = self.prevtime
                self.hasSent = False

        # Don't always pop, as we might not have returned a message from the queue
        if msg is not None:
            assert debug("Message popped")
            self.inputScheduler.removeFirst()
        return clock, msg

    #@profile
    def simstep(self, clock, msg):
        """
        Perform 1 step in the simulation
        Args:
            clock - current simulation time
            msg - message to be sent in this step
        """
        # Either send this external message to the model, or just do transitions
        if msg is not None:
            oldTL = self.model.timeLast
            # Send the message containing the data
            self.send(None, msg)
            self.model.timeLast = min(oldTL, msg.timestamp)
        else:
            self.unprocessed = False
            msg = Message(clock, 2)
            #TODO optimisation: don't do this if we already see that we have reverted?
            assert debug("START OUTPUT GENERATION PHASE")
            data = self.send(None, msg)
            self.hasSent = True
            assert debug("END OUTPUT GENERATION PHASE")
            #TODO data can be used at the root for the ROOT OUTPUT
            assert debug("@ messages processed")
            msg.messagetype = 1
            # Take a dirty shortcut, though it saves LOTS of time
            cDEVS = self.model
            assert debug("START TRANSITION PHASE")
            for trans in self.transitioning:
                self.atomicReceive(trans, msg)
                # Was already unscheduled while fetching imminent children
                #TODO unschedule too when receiving external input, so this command can dissapear
                cDEVS.scheduler.unschedule(trans)
                cDEVS.scheduler.schedule(trans)
            assert debug("END TRANSITION PHASE")
            cDEVS.scheduler.optimize(len(cDEVS.componentSet))
            cDEVS.timeLast = clock
            #cDEVS.myInput = {}
            cDEVS.setTimeNext()
            # Recompute the timeNext of the coupled model
            self.transitioning = set()
            self.reverted = False
            self.blockOutgoing = False

    def simulatorProcessEvent(self, eventPort="", eventValue="", eventTime=0):
        # For real time
        if (not self.check()):
            if eventPort == "" and eventValue == "":
                clock = self.getTimeNext()
                msg = None
                self.procTransition = True
            else:
                # Should be a list for PDEVS...
                if not isinstance(eventValue, list):
                    eventValue = [eventValue]
                # Fake injection method...
                # Not really that tidy, though it should work
                nport = Port()
                nport.outLine = [self.realTimeInputPortReferences[eventPort]]
                msg = Message((eventTime, 1), 3, {nport : eventValue})
                clock = (eventTime, 1)
                self.procTransition = False
            self.prevtime = clock
            if self.check(clock[0]) or clock[0] == float('inf'):
                self.unprocessed = False
                return
            self.simstep(clock, msg)
            if msg is not None:
                self.procTransition = True
                self.simstep(clock, None)
            self.clock = clock
            self.oldClock = self.clock
            self.clock = self.getTimeNext()
            self.waitTimeInterval = self.clock[0] - self.oldClock[0]

    def runsim(self):
        """
        Run the simulation until the termination condition signals the
        end of the simulation. Keeps processing until there are no more
        dirty queue's, so doesn't stop immediately after fulfulling the
        termination condition.
        """
        clock = self.getTimeNext()
        # Either the termination condition doesn't allow stopping (the default)
        #  or we have sent some messages, but not yet done their control messages
        #  or we still have some messages in the inputqueue that are not processed
        #   (possibly anti-messages or stragler messages)
        while (not self.check()) or (len(self.sentAlready) > 0) or (self.unprocessed):
            if len(self.inqueue) > 0:
                self.inmsg.set()
                # No busy looping
                self.emptyQueue.wait()
                self.emptyQueue.clear()
            # Start simulation
            self.simlock.acquire()
            self.nestedlock.acquire()

            # First flush the inputqueue as these messages are very important
            # Check if there are external messages that need to be processed
            if self.irreversible and len(self.inputScheduler.heap) == 0:
                clock = self.getTimeNext()
                msg = None
            else:
                clock, msg = self.findMessage(self.getTimeNext())

            if msg is None:
                # No more messages before the timeNext of the model, so flush everything
                assert debug("Flushing msg's")
                if len(self.sentAlready) > 0:
                    clock = self.prevtime
                    self.sentAlready = []
                    # Otherwise, the clock is already set correctly
                self.procTransition = True
            else:   
                self.procTransition = False
            self.prevtime = clock
            assert debug("Sending msg = " + str(msg))

            if self.check(clock[0]) or clock[0] == float('inf'):
                # Special case
                self.sentAlready = []
                self.unprocessed = False
                self.nestedlock.release()
                self.simlock.release()
                break

            assert debug("Processing @ clock " + str(clock))
            # Round of to prevent slight floating point differences... EPSILON alone doesn't always suffice when revertions happen...
            clock = (round(clock[0], 6), clock[1])
            """
            try:
                self.simstep(clock, msg)
                clock = self.getTimeNext()
            except Exception as e:
                print("Queueing exception")
                self.delayedAction(clock, self.model.getModelFullName(), "raise pickle.loads(" + str(pickle.dumps(e)) + ")")
                break
            finally:
                self.nestedlock.release()
                self.simlock.release()
            """
            self.simstep(clock, msg)
            clock = self.getTimeNext()
            self.nestedlock.release()
            self.simlock.release()

    def finishRing(self, count):
        """
        Go over the ring and ask each kernel whether it is OK to stop simulation
        or not. Uses a count to check that no messages are yet to be processed.
        Args:
            count - counter of all sent/received messages
        Return:
            bool - is it ok to stop all kernels?
        """
        if not self.simlock.acquire(False):
            # Can't even acquire the simlock, so something is busy
            assert debug("FINISH -- Simlock active")
            return False
        if not self.nestedlock.acquire(False):
            # Can't acquire the nestedlock, so something is busy
            self.simlock.release()
            assert debug("FINISH -- Nestedlock active")
            return False
        if self.shouldrun.isSet():
            # Quick stop
            assert debug("FINISH -- Shouldrun active at " + str(self.name))
            retval = False
        elif self.unprocessed or len(self.inqueue) > 0:
            assert debug("FINISH -- Unprocessed active")
            retval = False
        elif self.name == self.controller_name:
            # We are round
            if count == 0:
                # All messages received!
                retval = True
            else:
                # Some message not yet received :(
                assert debug("FINISH -- Not received all")
                retval = False
        else:
            retval = self.nextLP.finishRing(self.totalCounter + count)
        if not retval and not self.irreversible:
            # If we have work to do, set the shouldrun flag to prevent deadlocks
            # Never set the shouldrun event in case the simulator is reversible, otherwise we will deadlock
            self.shouldrun.set()
        self.nestedlock.release()
        self.simlock.release()
        return retval

    def loadstate(self, savedstate):
        if self.state_saving == 5:
            return savedstate.copy()
        elif self.state_saving == 2:
            return pickle.loads(savedstate)
        elif self.state_saving == 0:
            return deepcopy(savedstate)
        elif self.state_saving == 1:
            return pickle.loads(savedstate)
        elif self.state_saving == 3:
            return copy(savedstate)
        elif self.state_saving == 4:
            return savedstate

    def savestate(self, presentstate):
        # Put the most frequently used on top
        if self.state_saving == 5:
            return presentstate.copy()
        elif self.state_saving == 2:
            return pickle.dumps(presentstate, pickle.HIGHEST_PROTOCOL)
        elif self.state_saving == 0:
            return deepcopy(presentstate)
        elif self.state_saving == 1:
            return pickle.dumps(presentstate, 0)
        elif self.state_saving == 3:
            return copy(presentstate)
        elif self.state_saving == 4:
            return presentstate

    def checkpoint(self):
        """
        Save a checkpoint of the current basesimulator, this function will assume
        that no messages are still left in the medium, since these are obviously
        not saved by pickling the base simulator.
        """
        # pdc = PythonDevs Checkpoint
        outfile = open("checkpoint_" + str(round(self.GVT, 2)) + "_" + str(self.name) + ".pdc", 'w')
        pickle.dump(self, outfile)

    def loadCheckpoint(self):
        """
        Alert this kernel that it is restoring from a checkpoint
        """
        #NOTE irreversible components are not loadable!
        # pdc = PythonDevs Checkpoint
        # Loading to self directly is impossible

        # Just perform a revertion
        # but clear the queues first
        if not self.irreversible:
            self.outputQueue = []
        # and the inputQueue, since every model will be reset to GVT
        #  everything that happens before GVT can be cleared by revertion
        #  everything that happens after GVT will be replicated by the external models
        # Useful, since this also allows us to skip saving all this info in the pickled data
        self.inputScheduler = MessageScheduler()
        self.inqueue = []
        self.actions = []
        self.revert((self.GVT, 0))

    def simulate(self):
        """
        Start up simulation on this kernel
        """
        thrd = threading.Thread(target=BaseSimulator.externalQueueProcessor, args=[self])
        thrd.daemon = True
        thrd.start()

        if len(self.depends) == 0:
            self.irreversible = True

        if self.kernels == 1:
            self.irreversible = True

        if self.disallowIrreversible:
            self.irreversible = False

        if self.irreversible:
            pass
            assert info("Became irreversible")

        #TODO this code should be removed someday
        if self.irreversible and self.checkpointFreq > 0:
            self.irreversible = False
            
        # Send the init message
        if self.GVT == -float('inf'):
            #NOTE this message should have gone through the model before the next message
            self.send(None, Message((0, 0), 0))
            assert debug("Inits sent")
            clock = self.model.timeNext
        self.nestedlock.release()
        self.simlock.release()

        controller = getProxy(self.controller_name)
        makeOneway(controller, "notifyWait")
        makeOneway(controller, "notifyRun")
        while True:
            self.runsim()
            # Notify that we are currently not doing anything
            #NOTE note that we can NOT shut down the recv channel, as we might receive controller messages
            controller.notifyWait()
            if self.irreversible:
                makeOneway(controller, "notifyDone")
                controller.notifyDone(self.name)
                self.shouldrun.clear()
                if len(self.inqueue) == 0 and self.unprocessed:
                    self.unprocessed = False
                break
            self.shouldrun.wait()
            self.shouldrun.clear()
            if self.finished:
                # Simulation has finished
                break
            # Notify that we are running again
            controller.notifyRun()
        self.simFinish.set()
        assert info(str(self.name) + " is done")
        assert info("Number of revertions at " + str(self.name) + ": " + str(self.reverts))

    def fixHierarchy(self, name, parentname):
        """
        Recreate the hierarchy of the local models
        Args:
            name - the name of the kernel where the model's parent is located
        """
        if self.model.parent is not None:
            self.model.parent.remote_location = name
            self.model.parent.proxy = getProxy(name)
            self.model.parent.name = parentname
        self.model.fixHierarchy(self.name, parentname)

    #TODO might need some more checks
    def directConnect(self):
        """
        Direct connect this kernel's model
        """
        if self.directConnected:
            return
        #self.model.printModel()
        newlist = []
        queue = []
        #self.model.printModel()
        for d in self.model.componentSet:
            if isinstance(d, AtomicDEVS):
                # An atomic model, this has to stay the same
                newlist.append(d)
                assert debug("Adding child " + str(d.getModelFullName()))
            elif isinstance(d, CoupledDEVS):
                # A coupled model, this must be expanded
                assert debug("Extending children of " + str(d.getModelFullName()))
                self.model.componentSet.extend(d.componentSet)
            elif isinstance(d, RemoteCDEVS):
                # A remote model, ask the remote kernel for all necessary information
                newlist.append(d)
                # Add the remote model itself, though it might become useless
                queue.append(d.remote_location)
                depend = False
                # Only mark this as a dependency in case it really depends on us
                for i in d.IPorts:
                    for j in i.inLine:
                        if j.hostDEVS == self:
                            depend = True
                if depend:
                    getProxy(d.remote_location).dependsOn(self.name)
        self.model.componentSet = newlist
        # The complete structure should be flat by now
        self.directConnected = True

        searchset = list(self.model.componentSet)
        searchset.append(self.model)
        for comp in searchset:
            for outport in comp.OPorts:
                newline = []
                for outline in outport.outLine:
                    if isinstance(outline.hostDEVS, CoupledDEVS) and outline.hostDEVS != self.model:
                        outport.outLine.extend(outline.outLine)
                    elif outline not in newline:
                        newline.append(outline)
                outport.outLine = newline
            for inport in comp.IPorts:
                newline = []
                for inline in inport.inLine:
                    if isinstance(inline.hostDEVS, CoupledDEVS) and inline.hostDEVS != self.model:
                        inport.inLine.extend(inline.inLine)
                    elif inline not in newline:
                        newline.append(inline)
                inport.inLine = newline

        for i in queue:
            getProxy(i).directConnect()

        # Don't think about our own ports if nothing is connected to it. So make
        # a list of all connected ports, this way, we also make this one step
        outs = []
        portlist = []
        for comp in self.model.componentSet:
            portlist.extend(comp.OPorts)
        for outport in portlist:
            # These are all internal outports, just do an algorithm similar to the one in the previous PyDEVS
            newline = []
            for outline in outport.outLine:
                if isinstance(outline.hostDEVS, CoupledDEVS) and (outline.hostDEVS != self.model):
                    # This port is connected to a local coupled model, so just extend our list of search locations with all ports that are connected to this coupled models input port
                    outport.outLine.extend(outline.outLine)
                elif isinstance(outline.hostDEVS, AtomicDEVS) and (outline not in newline):
                    newline.append(outline)
                elif isinstance(outline.hostDEVS, RemoteCDEVS):
                    # Create a direct connection for each remote model that we found
                    targets = outline.hostDEVS.getTargets(outline.hostDEVS.getModelFullName(), outline.getPortName())
                    remapped = {}
                    for target in targets:
                        current = remapped.get(target[0], [])
                        current.append([target[1], target[2]])
                        remapped[target[0]] = current
                    for entry in list(remapped.items()):
                        location = entry[0]
                        connected = entry[1]
                        rcdevs = RemoteCDEVS(location, connected)
                        self.model.componentSet.append(rcdevs)
                        rcdevs.parent = self.model
                        rcdevs.setRootSim(self, self.name)
                        rcdevs.setData()
                        getProxy(rcdevs.remote_location).dependsOn(self.name)
                        rcdevs.fullName = "REMOTE to " + str(location)
                        self.model.model_ids[rcdevs.model_id] = rcdevs
                        outline.outLine.append(rcdevs.inport)
                        newline.append(rcdevs.inport)
                elif isinstance(outline.hostDEVS, CoupledDEVS) and (outline.hostDEVS == self.model):
                    # A connection that goes up to the parent, we need to ask the parent to fix this connection for us
                    # But do this later on
                    if self.model.parent is not None:
                        #print("Fetching targets for " + str(outline.getPortFullName()))
                        targets = self.model.parent.getTargets(self.model.getModelFullName(), outline.getPortName())
                        #print("Got: " + str(targets))
                        remapped = {}
                        for target in targets:
                            current = remapped.get(target[0], [])
                            current.append([target[1], target[2]])
                            remapped[target[0]] = current
                        for entry in list(remapped.items()):
                            location = entry[0]
                            connected = entry[1]
                            rcdevs = RemoteCDEVS(location, connected)
                            self.model.componentSet.append(rcdevs)
                            rcdevs.parent = self.model
                            rcdevs.setRootSim(self, self.name)
                            rcdevs.setData()
                            getProxy(rcdevs.remote_location).dependsOn(self.name)
                            rcdevs.fullName = "REMOTE to " + str(location)
                            self.model.model_ids[rcdevs.model_id] = rcdevs
                            newline.append(rcdevs.inport)
            outport.outLine = newline
        #self.model.printModel()

    def returnTargets(self, port):
        targets = []
        #print("Searching targets for port with outline: " + str(port.outLine))
        for outport in port.outLine:
            #print("Checking port " + str(outport.getPortFullName()))
            if isinstance(outport.hostDEVS, CoupledDEVS) and (outport.hostDEVS != self.model):
                #print("COUPLED")
                targets.extend(self.returnTargets(outport))
            elif isinstance(outport.hostDEVS, CoupledDEVS) and (outport.hostDEVS == self.model):
                #print("COUPLED HIERARCHY")
                targets.extend(self.model.parent.getTargets(self.model.getModelFullName(), outport.getPortName()))
            elif isinstance(outport.hostDEVS, AtomicDEVS):
                #print("ATOMIC")
                targets.append([self.name, outport.hostDEVS.getModelFullName(), outport.getPortName()])
            elif isinstance(outport.hostDEVS, RemoteCDEVS):
                #print("REMOTE")
                targets.extend(outport.hostDEVS.getTargets(outport.hostDEVS.getModelFullName(), outport.getPortName()))
            else:
                raise DEVSException("Unknown error while performing direct connection")
        return targets

    def getTargets(self, modelname, portname):
        #TODO multiple remotes are UNTESTED!
        # We can assume that this model was already direct connected
        #print("Fetching targets for " + modelname + " ==> " + portname)
        port = None
        #print("GetTargets called at " + str(self.name) + " for " + str(modelname) + " --> " + str(portname))
        if not self.directConnected:
            self.directConnect()
        for model in self.model.componentSet:
            if model.getModelFullName() == modelname:
                for oport in model.OPorts:
                    if oport.getPortName() == portname:
                        port = oport
                for iport in model.IPorts:
                    if iport.getPortName() == portname:
                        port = iport
        if self.model.getModelFullName() == modelname:
            for oport in self.model.OPorts:
                if oport.getPortName() == portname:
                    port = oport
            for iport in self.model.IPorts:
                if iport.getPortName() == portname:
                    port = iport
        if port is not None:
            #print("Found a port here: " + str(port.getPortFullName()))
            return self.returnTargets(port)
        else:
            # This should not happen
            raise DEVSException("Direct connection to unknown port requested at " + str(self.name) + ": " + str(modelname) + "." + str(portname))

    def startTracers(self):
        """
        Start all tracers
        """
        self.tracers.startTracers()

    def stopTracers(self):
        """
        Stop all tracers
        """
        self.tracers.stopTracers()

    def getVCDVariables(self):
        """
        Generate a list of all variables that exist in the current scope
        Returns:
            list - all VCD variables in current scope
        """
        if self.visited:
            return []
        else:
            variables = []
            for d in self.model.componentSet:
                if not isinstance(d, RemoteCDEVS):
                    variables.extend(d.getVCDVariables())
            self.visited = True
            variables.extend(self.nextLP.getVCDVariables())
            return variables

    def findModel(self, name):
        # Will be only 1 step in each basesimulator due to direct connection
        bestmatch = ""
        foundmodel = None
        assert debug("Finding model")
        if self.model.getModelFullName() == name:
            return self.name, self.model.model_id
        for i in self.model.componentSet:
            assert debug("Checking " + str(i.getModelFullName()))
            if name.startswith(i.getModelFullName()):
                if (name == i.getModelFullName()) and (not isinstance(i, RemoteCDEVS)):
                    # At endpoint
                    return self.name, i.model_id
                elif len(bestmatch) <= i.getModelFullName():
                    bestmatch = i.getModelFullName()
                    foundmodel = i
        if foundmodel is not None:
            if not isinstance(foundmodel, RemoteCDEVS):
                # This means that no _exact_ match is found and that it is a terminal!
                raise DEVSException("Not a Remote CDEVS model!\nSearching for " + str(name) + " but closest match was " + str(foundmodel.getModelFullName()))
            else:
                proxy = getProxy(foundmodel.remote_location)
                return proxy.findModel(name)
        else:
            raise DEVSException("Model doesn't exist!")

    def getState(self, model_id):
        return self.model_ids[model_id].state

    def getInOut(self, name):
        assert debug("GetInOut called")
        if isinstance(name, list):
            ports = [self.getModelByName(connection[0]).getPortByName(connection[1]) for connection in name]
            nport = Port(name="proxy-" + str(len(self.model.remapPort2Num)), isInput=True)
            nport.outLine = ports
            nextcount = len(self.model.remapPort2Num)
            self.model.remapPort2Num[nport] = nextcount
            self.model.remapNum2Port[nextcount] = nport
            nportlist = [["inport", nport.type(), nextcount]]
            return nportlist
        else:
            model = self.getModelByName(name)
            #print("Modifying remapper for " + str(model))
            if model.remapNum2Port != {}:
                # We already created this mapping, save ourself the time of doing it again
                return model.saved_ports
            portlist = list(model.IPorts)
            portlist.extend(model.OPorts)
            counter = len(model.remapNum2Port)
            ports = []
            for port in portlist:
                ports.append([port.getPortName(), port.type(), counter])
                model.remapPort2Num[port] = counter
                model.remapNum2Port[counter] = port
                counter += 1
            #print("Remapper set to " + str(model.remapNum2Port) + " for " + str(model))
            model.saved_ports = ports
            return ports

    def waitGVT(self):
        self.GVTfinished.wait()

    def lockGVT(self):
        self.GVTfinished.clear()
        self.GVTcomp.acquire()

    def unlockGVT(self):
        self.GVTcomp.release()
        self.GVTfinished.set()

    def runGVTthread(self):
        self.gvtthread = threading.Thread(target=BaseSimulator.threadGVT, args=[self, self.GVT_freq])
        self.gvtthread.start()

    def threadGVT(self, freq):
        """
        Run the GVT algorithm, this method should be called in its own thread,
        because it will block
        """
        controller = getProxy(self.controller_name)
        # Wait for the simulation to have done something useful before we start
        self.eventGVT.wait(freq)
        # Maybe simulation already finished...
        while self.runGVT:
            GVT = self.initGVT()
            # Limit the GVT algorithm, otherwise this will flood the ring
            self.eventGVT.wait(freq)

    def getModelidByName(self, name):
        return self.getModelByName(name).model_id

    def getModelByName(self, name):
        if name is None:
            return self.model
        try:
            return self.modelname_cache[name]
        except KeyError:
            assert debug("Keyerror")
            self.modelname_cache[name] = self.model_ids[self.findModel(name)[1]]
            return self.modelname_cache[name]

    def dependsOn(self, location):
        assert debug("Kernel at " + str(self.name) + " depends on kernel at " + str(location))
        self.depends.add(location)

    def notifyKernelDone(self, name):
        try:
            self.depends.remove(name)
            assert debug("Notified that " + str(name) + " is done")
            if len(self.depends) == 0:
                self.irreversible = True
                assert debug(str(self.name) + " became irreversible")
        except KeyError:
            pass

    def genUUID(self):
        self.sendmsgcounter += 1
        return hash("%s-%s" % (self.name, self.sendmsgcounter))
