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
Actual simulation kernel
"""
from pypdevs.solver import Solver

from pypdevs.util import *
from pypdevs.messageScheduler import MessageScheduler
from pypdevs.message import NetworkMessage
from pypdevs.DEVS import RootDEVS, CoupledDEVS, AtomicDEVS
from pypdevs.statesavers import *
import threading
from pypdevs.logger import *
try:
    import pickle as pickle
except ImportError:
    import pickle
from pypdevs.tracer import Tracers
from pypdevs.activityVisualisation import *
from collections import defaultdict
import pypdevs.accurate_time as time

try:
    import queue
except ImportError:
    import queue as Queue
from collections import deque

class BaseSimulator(Solver):
    """
    The BaseSimulator class, this is the actual simulation kernel.
    """
    def __init__(self, name, model, server):
        """
        Constructor

        :param name: the name of the kernel
        :param model: the model to initialise the kernel with
        """
        Solver.__init__(self)
        self.inits()
        self.server = server
        self.finish_sent = False
        self.reverts = 0
        self.transitioning = defaultdict(int)
        self.model = model
        self.tracers = Tracers()
        self.irreversible = False
        self.temporary_irreversible = False
        self.send_msg_counter = 0
        self.checkpoint_restored = False
        self.name = name
        self.realtime = False
        self.reset = False
        self.use_DSDEVS = False
        self.activity_tracking = False
        self.memoization = False
        self.total_activities = defaultdict(float)
        self.msg_sent = 0
        self.msg_recv = 0
        self.simlock_request = False

    def resetSimulation(self, scheduler):
        """
        Resets the simulation kernel to the saved version; can only be invoked after a previous simulation run.

        :param scheduler: the scheduler to set
        """
        model, model_ids = self.model, self.model_ids
        self.inits()
        self.finish_sent = False
        self.reverts = 0
        self.transitioning = defaultdict(int)
        self.tracers = Tracers()
        self.irreversible = False
        self.temporary_irreversible = False
        self.send_msg_counter = 0
        self.checkpoint_restored = False
        self.realtime = False
        self.reset = True
        proxy = self.getProxy(self.name)
        proxy.saveAndProcessModel(self.pickled_model, scheduler)

    def __setstate__(self, retdict):
        """
        For pickling

        :param retdict: dictionary containing the attributes to set
        """
        self.inits()

        for i in retdict:
            setattr(self, i, retdict[i])

    def __getstate__(self):
        """
        For pickling

        :returns: dictionary containing attributes and their values
        """
        retdict = {}
        unpicklable = frozenset(["instancemethod",
                                "lock",
                                "_Event",
                                "Thread",
                                "method-wrapper",
                                "builtin_function_or_method"])
        unnecessary = frozenset(["input_scheduler",
                                "inqueue",
                                "actions",
                                "server",
                                "msg_sent",
                                "msg_recv",
                                "send_msg_counter",
                                "output_queue",
                                "accumulator",
                                "control_msg",
                                "transitioning",
                                "Vchange",
                                "V"])
        for i in dir(self):
            if getattr(self, i).__class__.__name__ in unpicklable:
                # unpicklable, so don't copy it
                continue
            elif str(i) == "tracers":
                retdict["tracers"] = self.tracers.tracers_init
            elif (str(i) not in unnecessary) and (not str(i).startswith("__")):
                retdict[str(i)] = getattr(self, i)
        return retdict

    def inits(self):
        """
        Initialise the simulation kernel, this is split up from the constructor to
        make it possible to reset the kernel without reconstructing the kernel.
        """
        self.model = None
        self.model_ids = []
        self.actions = []
        self.waiting = 0
        self.actionlock = threading.Lock()
        self.should_run = threading.Event()

        self.termination_time = (float('inf'), 1)
        self.termination_time_check = True
        self.termination_condition = None

        self.block_outgoing = None

        self.priorcount = 0
        self.priorlock = threading.Lock()
        self.priorevent = threading.Event()
        self.priorevent.set()
        self.relocation_pending = False

        self.prevtime_finished = False

        # Mattern's GVT algorithm
        # 0 = white1
        # 1 = red1
        # 2 = white2
        # 3 = red2
        self.color = 0
        self.V = [{}, {}, {}, {}]
        self.Tmin = float('inf')
        self.control_msg = None
        self.gvt = -float('inf')
        self.accumulator = defaultdict(int)
        self.send_msg_counter = 0

        self.prevtime = (0, 0)
        self.clock = (-float('inf'), 0)

        self.input_scheduler = MessageScheduler()
        self.output_queue = []

        self.simlock = threading.Lock()
        self.Vlock = threading.Lock()
        # Acquire the lock ASAP, to prevent simulation during/after shutdown
        # it has to be released as soon as the simulation is commenced
        self.simlock.acquire()
        self.wait_for_gvt = threading.Event()
                
        self.Vchange = [threading.Event() for _ in range(4)]
        self.sim_finish = threading.Event()
        self.finished = False

        self.inqueue = deque()

    def getProxy(self, rank):
        """
        Get a proxy to the specified rank.

        Method will simply forward the request to its server object.

        :param rank: the rank to return a proxy to
        """
        return self.server.getProxy(rank)

    def getSelfProxy(self):
        """
        Get a proxy to ourself.

        This method is useful in case the underlying code has no idea on which node it is running and it simply wants to contact its kernel.
        It also differs from simply calling the code on the object of the kernel, as this provides a wrapper for asynchronous local invocation.
        """
        return self.server.getProxy(self.name)

    def setTerminationTime(self, time):
        """
        Sets the time at which simulation should stop, setting this will override
        the local simulation condition.

        :param time: the time at which the simulation should stop
        """
        self.termination_time = time
        # Set it in case the kernel was already stopped and an invalidation happened
        self.should_run.set()

    def sendModel(self, model, model_ids, scheduler_type, flattened):
        """
        Send a model to this simulation kernel, as this one will be simulated

        :param model: the model to set
        :param model_ids: list containing all models in order of their model_ids
        :param scheduler_type: string representation of the scheduler to use
        :param flattened: whether or not the model had its ports decoupled from the models to allow pickling
        """
        self.flattened = flattened
        if flattened:
            model.unflattenConnections()
        self.total_model = model
        self.model_ids = model_ids

        self.destinations = [None] * len(self.model_ids)
        counter = 0
        local = []
        remotes = False
        for atomic in self.model_ids:
            if atomic.location == self.name:
                # Model is simulated here
                self.destinations[counter] = atomic
                local.append(atomic)
            else:
                self.destinations[counter] = atomic.location
                remotes = True
            counter += 1

        self.local = local
        if isinstance(model, CoupledDEVS):
            self.model = RootDEVS(self.local, model.component_set, scheduler_type)
        elif isinstance(model, AtomicDEVS):
            self.model = RootDEVS(self.local, [model], scheduler_type)

        self.activities = {}

    def migrateTo(self, destination, model_ids):
        """
        Migrate all models to a new destination

        :param destination: destination of all models specified hereafter
        :param model_ids: iterable containing all models to migrate simultaneously
        """
        # Assumes that the simlock is already acquired
        # Make sure that the model that we are migrating is local here
        #assert info("Migrating " + str(model_ids) + " to " + str(destination))
        models = set()
        for model_id in model_ids:
            if isinstance(self.destinations[model_id], int):
                raise DEVSException(
                    "Cannot migrate model that is not local to the source!")
            if not self.destinations[model_id].relocatable:
                raise DEVSException(
                    "Model %s is fixed and is not allowed to be relocated" 
                    % self.destinations[model_id].getModelFullName())
            models.add(self.destinations[model_id])
        destination = int(destination)
        if destination == self.name:
            # Model is already there...
            return
        #assert info("Migration approved of %s from node %d to node %d" % (model_ids, self.name, destination))

        for model in models:
            # All models are gone here, so remove them from the scheduler
            self.model.scheduler.unschedule(model)

        for i in range(self.kernels):
            if i != destination and i != self.name:
                self.getProxy(i).notifyMigration(model_ids, destination)

        remote = self.getProxy(destination)
        # NOTE Due to the revertions, the outputQueue will be completely empty because:
        #        - messages before the GVT are cleaned up due to fossil collection
        #        - messages after the GVT are cleaned up due to the revertion that sends anti-messages
        # Furthermore, the state vector will be as small as possible to reduce the amount of data that has to be transferred
        # The inputqueue requires some small processing: all future incomming messages for the model that gets migrated
        # needs to be found. The processed messages list should be empty, with the following reason as the outputQueue.
        remote.messageTransfer(self.input_scheduler.extract(model_ids))
        bundled_models = [
            (m.model_id, (m.time_last, m.time_next, m.state)) for m in models]
        #TODO clean up this code to use the bundling somewhat more efficient
        remote.activateModels(bundled_models)
        for model in models:
            # No need to ask the new node whether or not there are specific nodes that also have to be informed
            #remote.activateModel(model.model_id, (model.time_last, model.time_next, model.state))
            # Delete our representation of the model
            model.state = None
            model.old_states = []
            del self.activities[model.model_id]

        # Remove the model from the component_set of the RootDEVS
        components = self.model.component_set
        self.model.component_set = [m for m in components if m not in models]
        for model_id in model_ids:
            self.model.local_model_ids.remove(model_id)
            self.destinations[model_id] = destination
            self.model_ids[model_id].location = destination

        # Now update the time_next and time_last values here
        self.model.setTimeNext()

    def notifyMigration(self, model_ids, destination):
        """
        Notify the migration of a model_id to a new destination

        :param model_ids: the model_ids that gets moved
        :param destination: the node location that now hosts the model_id
        """
        if destination == self.name:
            # No need to notify ourselves, simply here for safety as it shouldn't be called
            return
        for model_id in model_ids:
            self.destinations[model_id] = destination
            self.model_ids[model_id].location = destination

    def requestMigrationLock(self):
        """
        Request this kernel to lock itself ASAP to allow a relocation to happen. This will invoke the *notifyLocked* method on the controller as soon as locking succeeded.
        """
        with self.priorlock:
            self.priorcount += 1
            self.priorevent.clear()
        self.relocation_pending = True
        self.simlock.acquire()
        with self.Vlock:
            self.revert((self.gvt, 0))
        self.getProxy(0).notifyLocked(self.name)

    def migrationUnlock(self):
        """
        Unlocks the simulation lock remotely.

        .. warning:: do not use this function, unless you fully understand what you are doing!
        """
        with self.priorlock:
            self.priorcount -= 1
            if self.priorcount == 0:
                self.priorevent.set()

        self.prevtime_finished = False
        self.relocation_pending = False
        self.simlock.release()

    def activateModels(self, bundle):
        """
        Call the activateModel method on a list of arguments

        :param bundle: a bundle of messages to send, each entry should contain a tuple that can be expanded for the call
        """
        for model_id, current_state in bundle:
            self.activateModel(model_id, current_state)

    def activateModel(self, model_id, current_state):
        """
        Activate the model at this kernel, thus allowing the kernel to use (and schedule) this model. 
        Note that a revert to the GVT has to happen before calling this function, since the old_states 
        are not transferred and thus reverting is impossible.

        :param model_id: the id of the model that has to be activated
        :param currentState: the current state of the model that gets migrated
        """
        new_model = self.model_ids[model_id]
        old_location = new_model.location
        new_model.location = self.name
        self.model.component_set.append(new_model)
        self.model.local_model_ids.add(new_model.model_id)
        new_model.time_last = current_state[0]
        new_model.time_next = current_state[1]
        new_model.state = current_state[2]
        new_model.old_states = [self.state_saver(new_model.time_last, 
                                                new_model.time_next, 
                                                new_model.state, 
                                                0.0, 
                                                {}, 
                                                0.0)]
        # It is a new model, so add it to the scheduler too
        self.model.scheduler.schedule(new_model)
        self.destinations[model_id] = new_model
        self.model.setTimeNext()
        self.activities[model_id] = 0.0

    def messageTransfer(self, extraction):
        """
        Transfer the messages during a model transfer

        :param extraction: the extraction generated by the *messageScheduler*
        """
        self.input_scheduler.insert(extraction, self.model_ids)

    def notifySend(self, destination, timestamp, color):
        """
        Notify the simulation kernel of the sending of a message. Needed for
        GVT calculation.

        :param destination: the name of the simulation kernel that will receive the sent message
        :param timestamp: simulation time at which the message is sent
        :param color: color of the message being sent (for Mattern's algorithm)
        """
        self.msg_sent += 1
        self.V[color][destination] = self.V[color].get(destination, 0) + 1
        if color == 1 or color == 3:
            self.Tmin = min(self.Tmin, timestamp)

    def notifyReceive(self, color):
        """
        Notify the simulation kernel of the receiving of a message. Needed for
        GVT calculation.

        :param color: the color of the received message (for Mattern's algorithm)
        """
        #assert debug("Received message with color: " + str(color))
        self.msg_recv += 1
        self.V[color][self.name] = self.V[color].get(self.name, 0) - 1
        self.Vchange[color].set()

    def waitUntilOK(self, vector):
        """
        Returns as soon as all messages to this simulation kernel are received.
        Needed due to Mattern's algorithm. Uses events to prevent busy looping.

        :param vector: the vector number to wait for. Should be 0 for colors 0 and 1, should be 1 for colors 2 and 3.
        """
        while not (self.V[vector].get(self.name, 0) + 
                   self.control_msg[2].get(self.name, 0) <= 0):
            self.Vlock.release()
            # Use an event to prevent busy looping
            self.Vchange[vector].wait()
            self.Vchange[vector].clear()
            # Free the lock
            self.Vlock.acquire()
        return False

    def receiveControl(self, msg, first=False):
        """
        Receive a GVT control message and process it. Method will block until the GVT is actually found, so make this an asynchronous call, or run it on a seperate thread.

        This code implements Mattern's algorithm with a slight modification: it uses 4 different colours to distinguish two subsequent runs. Furthermore, it always requires 2 complete passes before a GVT is found.
        """
        self.control_msg = msg
        m_clock = self.control_msg[0]
        m_send = self.control_msg[1]
        waiting_vector = self.control_msg[2]
        accumulating_vector = self.control_msg[3]

        with self.Vlock:
            prevcolor = 3 if self.color == 0 else self.color - 1
            color = self.color
            finished = (self.name == 0 and 
                        not first and 
                        (color == 0 or color == 2))
            if self.name == 0 and not first:
                if not allZeroDict(waiting_vector):
                    raise DEVSException("GVT bug detected")
                waiting_vector = accumulating_vector
                self.control_msg[2] = accumulating_vector
                accumulating_vector = {}
            if finished:
                from math import floor
                gvt = floor(min(m_clock, m_send))
                print("Got GVT")
                if gvt < self.gvt:
                    raise DEVSException("GVT is decreasing")
                self.accumulator = waiting_vector
                use_last_state = self.relocator.useLastStateOnly()
                self.getProxy(self.name).setGVT(gvt, 
                                                [], 
                                                use_last_state)
                return
            else:
                self.waitUntilOK(prevcolor)
                addDict(waiting_vector, self.V[prevcolor])
                addDict(accumulating_vector, self.V[color])
                self.V[prevcolor] = {}
                self.V[color] = {}
                if not self.prevtime_finished:
                    localtime = self.prevtime[0]
                else:
                    localtime = float('inf')
                ntime = localtime if self.name == 0 else min(m_clock, localtime)
                msg = [ntime, 
                       min(m_send, self.Tmin), 
                       waiting_vector, 
                       accumulating_vector]
                self.Tmin = float('inf')
            self.color = (self.color + 1) % 4
        self.next_LP.receiveControl(msg)

    def setIrreversible(self):
        """
        Mark this node as **temporary** irreversible, meaning that it can simply be made reversible later on. 
        This can be used when all nodes are ran at a single node due to relocation, though future relocations might again move some nodes away.
        """
        self.temporary_irreversible = True

    def unsetIrreversible(self):
        """
        Unmark this node as **temporary** irreversible.
        """
        self.temporary_irreversible = False

    def setGVT(self, gvt, activities, last_state_only):
        """
        Sets the GVT of this simulation kernel. This value should not be smaller than
        the current GVT (this would be impossible for a correct GVT calculation). Also
        cleans up the input, output and state buffers used due to time-warp.
        Furthermore, it also processes all messages scheduled before the GVT.

        :param gvt: the desired GVT
        :param activities: the activities of all seperate nodes as a list
        :param last_state_only: whether or not all states should be considered or only the last
        """
        # GVT is just a time, it does not contain an age field!
        #assert debug("Got setGVT")
        if gvt < self.gvt:
            raise DEVSException("GVT cannot decrease from %s to %s!" 
                                % (self.gvt, gvt))
        if gvt == self.gvt:
            # The same, so don't do the batched fossil collection
            # This will ALWAYS happen at the controller first, as this is the one that gets called with the GVT update first
            #   if the value should change, it will do a complete round and finally set the variable
            #   if the value stays the same, we can stop immediately
            #assert info("Set GVT to %s" % GVT)

            if self.initial_allocator is not None:
                if gvt >= self.initial_allocator.getTerminationTime():
                    # The initial allocator period is over, so switch to normal simulation
                    relocs = self.getInitialAllocations()
                    # Possibly, the locations are altered, so reset everything
                    for model in self.model.component_set:
                        model.location = 0
                    # Function pointers, so CamelCase
                    self.atomicOutputGeneration = self.atomicOutputGeneration_backup
                    self.performRelocationsInit(relocs)
                # Clear activities for now, as we don't want activity relocation medling in our affairs
                activities = []

            if activities:
                if self.old_gvt == -float('inf'):
                    self.old_gvt = 0.
                horizon = self.gvt - self.old_gvt
                if self.gvt != self.old_gvt and activities[0][1] is not None:
                    f = open("activity-log", 'a')
                    f.write(str((self.gvt - self.old_gvt) / 2 + self.old_gvt))
                    for _, a in activities:
                        f.write(" %s" % (a / horizon))
                    f.write("\n")
                    f.close()
                self.findAndPerformRelocations(gvt, activities, horizon)
            # Otherwise: there was no pass in the GVT ring, indicating that no GVT progress was made
            # This also indicates that the activities will NOT be reset
            self.GVTdone()
            return

        self.simlock_request = True
        with self.simlock:
            self.simlock_request = False
            #assert debug("Set GVT to " + str(GVT))
            self.old_gvt = self.gvt
            self.gvt = gvt

            nqueue = []
            self.input_scheduler.cleanup((gvt, 1))

            self.performActions(gvt)

            found = False
            for index in range(len(self.output_queue)):
                if self.output_queue[index].timestamp[0] >= gvt:
                    found = True
                    self.output_queue = self.output_queue[index:]
                    break
            if not found:
                self.output_queue = []

            self.activities = {}
            self.model.setGVT(gvt, self.activities, last_state_only)
            addDict(self.total_activities, self.activities)
            if self.temporary_irreversible:
                #print("Setting new state for %s models" % len(self.model.component_set))
                for model in self.model.component_set:
                    activity = self.total_activities[model.model_id]
                    model.old_states = [self.state_saver(model.time_last,
                                                         model.time_next, 
                                                         model.state, 
                                                         activity, 
                                                         None, 
                                                         None)]
                #TODO this is commented...
                #self.totalActivities = defaultdict(float)
            # Make a checkpoint too
            if self.checkpoint_counter == self.checkpoint_freq:
                self.checkpoint()
                self.checkpoint_counter = 0
            else:
                self.checkpoint_counter += 1

        # Move the pending activities
        if last_state_only:
            activity_sum = None
        else:
            activity_sum = sum(self.activities.values())

        activities.append((self.name, activity_sum))
        self.next_LP.setGVT(gvt, activities, last_state_only)

    def revert(self, time):
        """
        Revert the current simulation kernel to the specified time. All messages
        sent after this time will be invalidated, all states produced after this
        time will be removed.

        :param time: the desired time for revertion.

        .. note:: Clearly, this time should be >= the current GVT
        """
        # Don't #assert that it is not irreversible, as an irreversible component could theoretically still be reverted, but this MUST be to a state when it was not yet irreversible
        # Reverting the complete LP
        if time[0] < self.gvt:
            raise DEVSException("Reverting to time %f, before the GVT (%f)!" 
                                % (time[0], self.gvt))
        #assert debug("Removing actions from time " + str(time))
        self.transitioning = defaultdict(int)
        self.reverts += 1
        #assert debug("Revert to time " + str(time) + ", clock = " + str(self.clock))
        if self.do_some_tracing:
            self.getProxy(0).removeActions(self.model.local_model_ids, time)
        # Also revert the input message scheduler
        self.input_scheduler.revert(time)
        # Now revert all local models
        controller_revert = self.model.revert(time, self.memoization)
        #assert debug("Reverted all models")

        self.clock = self.prevtime = time

        # Invalidate all output messages after or at time
        end = -1
        unschedules = {}
        unschedules_mintime = {}
        for index, value in enumerate(self.output_queue):
            # Do not invalidate messages at this time itself, as they are processed in this time step and not generated in this timestep
            if value.timestamp > time:
                model_id = value.destination
                mintime = unschedules_mintime.get(model_id,
                                                  (float('inf'), 0))
                unschedules_mintime[model_id] = min(mintime, value.timestamp)
                unschedules.setdefault(model_id, []).append(value.uuid)
            else:
                #assert debug("NOT invalidating " + str(value.uuid))
                end = index
        self.output_queue = self.output_queue[:end+1]

        try:
            self.block_outgoing = self.output_queue[-1].timestamp
        except IndexError:
            self.block_outgoing = None

        # Don't need the Vlock here, as we already have it
        for model_id in unschedules:
            dest_kernel = self.destinations[model_id]
            if not isinstance(dest_kernel, int):
                raise DEVSException("Revertion due to relocation to self... This is impossible!")
            mintime = unschedules_mintime[model_id]
            # Assume we have the simlock already
            self.notifySend(dest_kernel, mintime[0], self.color)
            self.getProxy(dest_kernel).receiveAntiMessages(mintime, 
                                                           model_id, 
                                                           unschedules[model_id], 
                                                           self.color)

        # Controller has read one of the reverted states, so force a rollback there
        if controller_revert:
            self.notifySend(0, time[0], self.color)
            self.getProxy(0).receiveAntiMessages(time, None, [], self.color)
        self.should_run.set()

    def send(self, model_id, timestamp, content):
        """
        Prepare a message to be sent remotely and do the actual sending too.

        :param model_id: the id of the model that has to receive the message
        :param timestamp: timestamp of the message
        :param content: content of the message being sent
        """
        if self.block_outgoing == timestamp and (not self.checkpoint_restored):
            # If the model was just reverted, we don't need to sent out these 
            # messages because they are already in the receivers queues.
            #assert debug("Not sending message " + str(timestamp))
            return

        self.checkpoint_restored = False
        remote_location = self.destinations[model_id]
        # NOTE the Vlock is already acquired by the sender
        msg = NetworkMessage(timestamp, 
                             content, 
                             self.genUUID(), 
                             self.color, 
                             model_id)

        # Assume we have the simlock
        self.notifySend(remote_location, msg.timestamp[0], msg.color)

        # The message should be saved, though it should not be a copy. This is because the middleware will make
        # a copy itself, making this old message unused. Furthermore, the receiver will always create a copy
        # of the message to be safe, making a copy at the source unnecessary
        self.output_queue.append(msg)

        self.getProxy(remote_location).receive(msg)

    def receive(self, msg):
        """
        Make the kernel receive the provided message.

        The method will return as soon as possible to prevent a big number of pending messages.
        Furthermore, acquiring the locks here would be impractical since we only process all incomming messages one at a time.

        :param msg: a NetworkMessage to process
        """
        # NOTE ports could change at run-time, though this is not a problem in distributed simulation!
        # NOTE no need for locking, as all methods of a deque object is atomic
        self.inqueue.append(msg)
        self.should_run.set()

    def processIncommingMessages(self):
        """
        Process all incomming messages and return.

        This is part of the main simulation loop instead of being part of the message receive method, as we require the simlock for this. Acquiring the simlock elsewhere might take some time!
        """
        while self.inqueue:
            msg = self.inqueue.popleft()
            dest_model = msg.destination
            if dest_model not in self.model.local_model_ids:
                # NOTE do it this way to make sure that anti message properties are conserved
                #      furthermore, it prevents the message from being invalidated
                self.notifyReceive(msg.color)
                dest = self.destinations[dest_model]
                msg.color = self.color
                # No need to reencode the data, as it was still encoded
                self.notifySend(dest, msg.timestamp[0], self.color)
                self.getProxy(dest).receive(msg)
                continue
            #assert debug("Processing external msg: " + str(msg))
            model = self.model_ids[dest_model]
            msg.content = {model.ports[e]: msg.content[e] for e in msg.content}
            if msg.timestamp <= self.prevtime:
                # Timestamp is before the prevtime
                # so set the prevtime back in the past
                self.revert(msg.timestamp)
            elif self.prevtime_finished:
                # The prevtime is irrelevant, as we have finished simulation
                self.prevtime = msg.timestamp
            self.prevtime_finished = False
            self.notifyReceive(msg.color)

            # Now the message is an 'ordinary' message, just schedule it for processing
            self.input_scheduler.schedule(msg)
            self.model.time_next = min(self.model.time_next, msg.timestamp)

    def receiveAntiMessages(self, mintime, model_id, uuids, color):
        """
        Process a (possibly huge) batch of anti messages for the same model

        :param mintime: the lowest timestamp of all messages being cancelled
        :param model_id: the model_id of the receiving model whose messages need to be negated, None to indicate a general rollback
        :param uuids: list of all uuids to cancel
        :param color: color for Mattern's algorithm

        .. note:: the *model_id* is only required to check whether or not the model is still local to us
        """
        # Important that this function is called oneway, as it can be called in such a way that it deadlocks otherwise
        with self.priorlock:
            self.priorcount += 1
            self.priorevent.clear()

        try:
            with self.simlock:
                with self.Vlock:
                    if (model_id not in self.model.local_model_ids and 
                            model_id is not None):
                        self.notifyReceive(color)
                        destination = self.destinations[model_id]
                        self.getProxy(destination).receiveAntiMessages(mintime, 
                                                                       model_id, 
                                                                       uuids, 
                                                                       self.color)
                        self.notifySend(destination, mintime[0], self.color)
                        return
                    if mintime <= self.prevtime:
                        # Timestamp is before the prevtime
                        # so set the prevtime back in the past
                        self.revert(mintime)
                    elif self.prevtime_finished:
                        # The prevtime is irrelevant, as we have finished simulation
                        self.prevtime = mintime
                    self.prevtime_finished = False
                    self.notifyReceive(color)
                    if model_id is not None:
                        self.input_scheduler.massUnschedule(uuids)
        finally:
            with self.priorlock:
                self.priorcount -= 1
                if self.priorcount == 0:
                    self.priorevent.set()

    def check(self):
        """
        Checks wheter or not simulation should still continue. This will either
        call the global time termination check, or the local state termination
        check, depending on configuration.

        Using the global time termination check is a lot FASTER and should be used
        if possible.

        :returns: bool -- whether or not to stop simulation
        """
        # Return True = stop simulation
        # Return False = continue simulation
        if self.prevtime[1] > 1000:
            # Max loop checks
            raise DEVSException("Maximal number of 0 timeAdvance loops detected")
        if self.termination_time_check:
            # Finish at the termination time
            if self.model.time_next > self.termination_time:
                try:
                    timestamp = self.input_scheduler.readFirst().timestamp
                    return timestamp > self.termination_time
                except IndexError:
                    # No message waiting to be processed, so finished
                    return True
            else:
                return False
        else:
            # Use a termination condition
            # This code is only ran at the controller, as this is the only one with a termination condition
            if (self.prevtime[0] == float('inf') or 
                    self.termination_condition(self.prevtime, self.total_model)):
                if not self.finish_sent:
                    self.finishAtTime((self.prevtime[0], self.prevtime[1] + 1))
                    self.finish_sent = True
                return True
            elif self.finish_sent:
                self.finishAtTime((float('inf'), float('inf')))
                self.finish_sent = False
            return False

    def finishAtTime(self, clock):
        """
        Signal this kernel that it may stop at the provided time

        :param clock: the time to stop at
        """
        for num in range(self.kernels):
            self.getProxy(num).setTerminationTime(clock)

    def massDelayedActions(self, time, msgs):
        """
        Call the delayedAction function multiple times in succession.

        Mainly implemented to reduce the number of round trips when tracing.

        :param time: the time at which the action should happen
        :param msgs: list containing elements of the form (model_id, action)
        """
        for model_id, action in msgs:
            self.delayedAction(time, model_id, action)

    def delayedAction(self, time, model_id, action):
        """
        Perform an irreversible action (I/O, prints, global messages, ...). All
        these actions will be performed in the order they should be generated
        in a non-distributed simulation. All these messages might be reverted in
        case a revertion is performed by the calling model.

        :param time: the simulation time at which this command was requested
        :param model_id: the model_id of the model that requested this command
        :param action: the actual command to be executed as soon as it is safe
        """
        #assert debug("Adding action for time " + str(time) + ", GVT = " + str(self.GVT))
        if time[0] < self.gvt:
            raise DEVSException("Can't execute action (%s) before the GVT (%s)!"
                                % (time, self.gvt))
        if (self.irreversible and 
                len(self.actions) > 0 and 
                time > self.actions[-1][0]):
            self.performActions()
        # An append is an atomic action, though we need to lock it as other operations on it arent' atomic
        with self.actionlock:
            self.actions.append([time, model_id, action])

    def removeActions(self, model_ids, time):
        """
        Remove all actions specified by a model, starting from a specified time.
        This function should be called when the model is reverted and its actions
        have to be undone

        :param model_ids: the model_ids of all reverted models
        :param time: time up to which to remove all actions
        """
        if time[0] < self.gvt:
            raise DEVSException("Cannot remove action (%s) before the GVT (%s)!"
                                % (time, self.gvt))
        #assert debug("Removing actions for time " + str(time) + " and for ids " + str(model_ids))
        # Actions are unsorted, so we have to go through the complete list
        with self.actionlock:
            self.actions = [i for i in self.actions 
                              if not ((i[1] in model_ids) and (i[0] >= time))]

    def performActions(self, gvt = float('inf')):
        """
        Perform all irreversible actions up to the provided time.
        If time is not specified, all queued actions will be executed (in case simulation is finished)

        :param gvt: the time up to which all actions should be executed
        """
        if (gvt >= self.termination_time[0] and 
                self.termination_condition is not None):
            # But crop of to the termination_time as we might have simulated slightly too long
            gvt = self.termination_time[0] + EPSILON
        with self.actionlock:
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

        # Sort on time first, then on MESSAGE, not on model
        lst.sort(key=lambda i: [i[0], i[2]])

        # Now execute each action in order
        for i in lst:
            exec(i[2])

    def removeTracers(self):
        """
        Removes all currently registered tracers. This does not clean them up, as this should already be done by the code at the end of the simulation.
        """
        self.tracers = Tracers()

    def setGlobals(self, 
                   address, 
                   loglevel, 
                   checkpoint_frequency, 
                   checkpoint_name, 
                   statesaver, 
                   kernels, 
                   msg_copy, 
                   memoization, 
                   tracers):
        """
        Configure all 'global' variables for this kernel

        :param address: address of the syslog server
        :param loglevel: level of logging library
        :param checkpoint_frequency: frequency at which checkpoints should be made
        :param checkpoint_name: name of the checkpoint to save
        :param statesaver: statesaving method
        :param kernels: number of simulation kernels in total
        :param msg_copy: message copy method
        :param memoization: use memoization or not
        """
        for tracer in tracers:
            self.tracers.registerTracer(tracer, self.server, self.checkpoint_restored)
        self.do_some_tracing = self.tracers.hasTracers()
        self.address = address
        self.loglevel = loglevel
        self.kernels = kernels
        self.next_LP = self.getProxy((self.name + 1) % kernels)
        self.irreversible = self.kernels == 1
        self.temporary_irreversible = self.irreversible
        state_saving_options = {0: DeepCopyState, 
                                1: PickleZeroState, 
                                2: PickleHighestState, 
                                3: CopyState, 
                                4: AssignState, 
                                5: CustomState, 
                                6: MarshalState}
        self.state_saver = state_saving_options[statesaver]
        # Save the integer value for checkpointing
        self.state_saving = statesaver
        self.msg_copy = msg_copy
        setLogger(self.name, address, loglevel)
        self.checkpoint_name = checkpoint_name
        self.checkpoint_freq = checkpoint_frequency
        self.checkpoint_counter = 0
        self.memoization = memoization

    def processMessage(self, clock):
        """
        Find the first external message smaller than the clock and process them if necessary. Return the new time_next for simulation.

        :param clock: timestamp of the next internal transition
        :returns: timestamp of the next transition, taking into account external messages
        """
        try:
            message = self.input_scheduler.readFirst()
        except IndexError:
            # No input messages
            return clock
        if message.timestamp < clock:
            # The message is sent before the timenext, so update the clock
            clock = message.timestamp
        try:
            while (abs(clock[0] - message.timestamp[0]) < EPSILON and 
                    (clock[1] == message.timestamp[1])):
                for port in message.content:
                    aDEVS = port.host_DEVS
                    content = message.content[port]
                    aDEVS.my_input.setdefault(port, []).extend(content)
                    self.transitioning[aDEVS] |= 2
                self.input_scheduler.removeFirst()
                message = self.input_scheduler.readFirst()
        except IndexError:
            # At the end of the scheduler, so we are done
            pass
        return clock

    def realtimeWait(self):
        """
        Perform the waiting for input required in realtime simulation.

        The time_next of the model will be updated accordingly and all messages will be routed.
        """
        # NOTE a scale of 2 means that simulation will take twice as long
        self.performActions()
        # Wait for the determined period of time
        current_realtime_time = (time.time() - self.rt_zerotime)
        scaled_realtime_time = current_realtime_time / self.realtime_scale
        self.asynchronous_generator.checkInterrupt(scaled_realtime_time)
        next_sim_time = min(self.model.time_next[0], 
                          self.termination_time[0], 
                          self.asynchronous_generator.getNextTime())
        # Scaled realtime
        next_sim_time *= self.realtime_scale

        # Subtract the time that we already did our computation
        wait_time = next_sim_time - current_realtime_time

        if wait_time <= 0:
            # Do the transition directly
            self.realtime_counter -= 1
            if self.realtime_counter < 0:
                self.realtime_counter = 100
                self.threading_backend.wait(0.01, self.runsim)
                return True
            # Transition
            #NOTE actually, we should set the time_next here too...
            #     otherwise we will always have a 'perfect' time_next
            return False
        else:
            interrupt = self.threading_backend.getInterrupt()
            if interrupt is None:
                self.realtime_counter = 100
                self.threading_backend.wait(wait_time, self.runsim)
                return True
            try:
                portname, event_value = interrupt.split(" ")
                event_port = self.portmap[portname]
            except ValueError:
                # Couldn't split, means we should stop
                import sys
                sys.exit(0)
            # Process the input
            #NOTE no distinction between PDEVS and CDEVS is necessary, as CDEVS is internally handled just like PDEVS
            #     wrappers are provided to 'unpack' the list structure
            if isinstance(event_port.host_DEVS, AtomicDEVS):
                msg = {event_port: [event_value]}
                event_port.host_DEVS.my_input = msg
                self.transitioning[event_port.host_DEVS] = 2
                time_diff = time.time() - self.rt_zerotime
                self.model.time_next = (time_diff / self.realtime_scale, 1)
            else:
                # We are outputting on a Coupled DEVS model, so we just find out what its ports are connected to
                time_diff = time.time() - self.rt_zerotime
                tn = time_diff / self.realtime_scale
                for p, z in event_port.routing_outline:
                    ev = event_value if z is None else z(event_value)
                    msg = {p: [ev]}
                    p.host_DEVS.my_input = msg
                    self.transitioning[p.host_DEVS] = 2
                    self.model.time_next = (tn, 1)
            # Transition
            return False

    def runsim(self):
        """
        Run a complete simulation run. Can be run multiple times if this is required in e.g. a distributed simulation.
        """
        self.realtime_counter = 100
        while 1:
            if self.realtime and self.realtimeWait():
                # Make implicit use of shortcut evaluation,
                # The realtimeWait method will return True if it forces a simulation stop
                break

            if self.inqueue:
                with self.simlock:
                    with self.Vlock:
                        self.processIncommingMessages()
            self.priorevent.wait()

            # Only do the check here, after setting the next time of the simulation
            
            # All priority threads are cleared, so obtain the simulation lock ourself
            while self.simlock_request:
                time.sleep(0.00001)
            with self.simlock:
                if self.check():
                    self.prevtime_finished = True
                    break
                # Process all incomming messages
                if not self.irreversible:
                    # Check the external messages only if there is a possibility for them to arrive
                    # This is a slight optimisation for local simulation
                    tn = self.processMessage(self.model.time_next)
                else:
                    tn = self.model.time_next
                if tn[0] == float('inf'):
                    # Always break, even if the terminiation condition/time was wrong
                    self.transitioning = defaultdict(int)
                    self.prevtime_finished = True
                    break
                cDEVS = self.model
                # Round of the current clock time, which is necessary for revertions later on
                self.current_clock = (round(tn[0], 6), tn[1])

                # Don't interrupt the output generation, as these nodes WILL be marked as 'sent'
                with self.Vlock:
                    reschedule = self.coupledOutputGeneration(self.current_clock)
                try:
                    self.massAtomicTransitions(self.transitioning, self.current_clock)
                    cDEVS.scheduler.massReschedule(reschedule)
                    if self.use_DSDEVS:
                        # Check for dynamic structure simulation
                        self.performDSDEVS(self.transitioning)
                except QuickStopException:
                    # For relocations that should interrupt the simulation algorithm
                    self.simlock.release()
                    self.priorevent.wait()
                    self.simlock.acquire()
                    continue

                # Put this in a lock to prevent a possible infinite time_next from reading the prevtime with the old value
                with self.Vlock:
                    # Fetch the next time of a transition
                    cDEVS.setTimeNext()
                    # Clear all transitioning elements
                    self.transitioning = defaultdict(int)
                    # No longer block any output messages
                    self.block_outgoing = None

                    # self.clock now contains the time at which NO messages were sent
                    self.prevtime = self.current_clock
                    self.clock = self.model.time_next

    def finishRing(self, msg_sent, msg_recv, first_run=False):
        """
        Go over the ring and ask each kernel whether it is OK to stop simulation
        or not. Uses a count to check that no messages are yet to be processed.

        :param msg_sent: current counter for total amount of sent messages
        :param msg_recv: current counter for total amount of received messages
        :param first_run: whether or not to forward at the controller
        :returns: int -- amount of messages received and sent (-1 signals running simulation)
        """
        #NOTE due to the MPI backend changing None to 0, we need to return something else, like a -1...
        # Try to obtain the simulation lock first
        if not self.simlock.acquire(False):
            # It was already taken, so something is still working
            return -1
        try:
            if self.should_run.isSet():
                # We should still run
                return -1
            elif self.name == 0 and not first_run:
                # We are done, so return if they are equal
                if msg_sent == msg_recv:
                    return msg_sent
                else:
                    # Some messages are not yet received, so not correct
                    return -1
        finally:
            # Always release the simlock when we got it
            self.simlock.release()
        # Ask the next node for its situation
        return self.next_LP.finishRing(self.msg_sent + msg_sent, 
                                       self.msg_recv + msg_recv)

    def checkpoint(self):
        """
        Save a checkpoint of the current basesimulator, this function will assume
        that no messages are still left in the medium, since these are obviously
        not saved by pickling the base simulator.
        """
        # pdc = PythonDevs Checkpoint
        outfile = open("%s_%s_%s.pdc" 
                       % (self.checkpoint_name, round(self.gvt, 2), self.name), 'w')
        # If the model was flattened when it was sent to this node, we will also need to flatten it while checkpointing
        if self.flattened:
            self.model.flattenConnections()
        pickle.dump(self, outfile)
        if self.flattened:
            # Don't forget to unflatten!
            self.model.unflattenConnections()

    def loadCheckpoint(self):
        """
        Alert this kernel that it is restoring from a checkpoint
        """
        # Overwrite variables for GVT algorithm
        self.color = 0
        self.transitioning = defaultdict(int)
        self.V = [{}, {}, {}, {}]
        self.Tmin = float('inf')
        self.control_msg = None
        self.waiting = 0
        self.checkpoint_restored = True

        tracerlist = self.tracers
        self.tracers = Tracers()

        self.setGlobals(address=self.address, 
                        loglevel=self.loglevel, 
                        tracers=tracerlist,
                        memoization=self.memoization,
                        checkpoint_name = self.checkpoint_name,
                        checkpoint_frequency=self.checkpoint_freq, 
                        statesaver=self.state_saving, 
                        kernels=self.kernels,
                        msg_copy=self.msg_copy)
        # Still unflatten the model if it was flattened (due to pickling limit)
        if self.flattened:
            self.model.unflattenConnections()

        self.msg_sent = 0
        self.msg_recv = 0
        self.priorcount = 0
        self.priorevent = threading.Event()
        self.priorevent.set()
        self.priorlock = threading.Lock()
        #self.inqueue = Queue.Queue()
        self.inqueue = deque()

        # Just perform a revertion
        # but clear the queues first
        self.output_queue = []
        # and the inputQueue, since every model will be reset to GVT
        #  everything that happens before GVT can be cleared by revertion
        #  everything that happens after GVT will be replicated by the external models
        # Useful, since this also allows us to skip saving all this info in the pickled data
        self.input_scheduler = MessageScheduler()
        self.actions = []
        with self.Vlock:
            self.revert((self.gvt, 0))

    def simulate_sync(self):
        """
        A small wrapper around the simulate() function, though with a different name to allow a much simpler MPI one way check
        """
        self.simulate()

    def simulate(self):
        """
        Simulate at this kernel
        """
        had_lock = not self.simlock.acquire(False)
        if had_lock:
            # We already had the lock, so normal simulation
            # Send the init message
            if self.gvt == -float('inf'):
                # To make sure that the GVT algorithm won't start already and see that this
                # model has nothing to simulate
                self.model.time_next = (0, 0)
                self.coupledInit()
        else:
            # We didn't have the lock yet, so this is a continueing simulation
            pass
        self.simlock.release()

        controller = self.getProxy(0)
        self.finished = False

        if self.realtime:
            self.runsim()
            self.sim_finish.set()
            return

        while 1:
            self.runsim()
            if self.irreversible:
                self.should_run.clear()
                break
            self.should_run.wait()
            self.should_run.clear()
            if self.finished:
                break
        self.sim_finish.set()

    def setAttr(self, model_id, attr, value):
        """
        Sets an attribute of a model.

        :param model_id: the id of the model to alter
        :param attr: string representation of the attribute to alter
        :param value: value to set
        """
        setattr(self.model_ids[model_id], attr, value)

    def setStateAttr(self, model_id, attr, value):
        """
        Sets an attribute of the state of a model

        :param model_id: the id of the model to alter
        :param attr: string representation of the attribute to alter
        :param value: value to set
        """
        setattr(self.model_ids[model_id].state, attr, value)

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

    def getGVT(self):
        """
        Return the GVT of this kernel

        :returns: float -- the current GVT
        """
        return self.gvt

    def getTime(self):
        """
        Return the current time of this kernel

        :returns: float -- the current simulation time
        """
        return self.prevtime[0]

    def getState(self, model_id):
        """
        Return the state of the specified model

        :param model_id: the model_id of the model of which the state is requested
        :returns: state -- the state of the requested model
        """
        return self.model_ids[model_id].state

    def getStateAtTime(self, model_id, request_time):
        """
        Gets the state of a model at a specific time

        :param model_id: model_id of which the state should be fetched
        :param request_time: time of the state
        """
        return self.model_ids[model_id].getState(request_time, False)

    def genUUID(self):
        """
        Create a unique enough ID for a message

        :returns: string -- a unique string for the specific name and number of sent messages
        """
        self.send_msg_counter += 1
        return "%s-%s" % (self.name, self.send_msg_counter)

    def getLocation(self, model_id):
        """
        Returns the location at which the model with the provided model_id runs

        :param model_id: the model_id of the model of which the location is requested
        :returns: int -- the number of the kernel where the provided model_id runs
        """
        fetched = self.destinations[model_id]
        if isinstance(fetched, int):
            return fetched
        else:
            return self.name

    def getActivity(self, model_id):
        """
        Returns the activity for a certain model id from the previous iteration

        :param model_id: the model_id to check
        :returns: float -- the activity
        """
        return self.activities.get(model_id, 0.0)

    def getCompleteActivity(self):
        """
        Returns the complete dictionary of all activities

        :returns: dict -- mapping of all activities
        """
        return self.activities

    def getTotalActivity(self, time=(float('inf'), float('inf'))):
        """
        Returns a dictionary containing the total activity through the complete simulation run

        :param time: time up to which to return activity
        :returns: dict -- mapping of all activities, but simulation-wide
        """
        if not self.irreversible:
            activities = {}
            self.model.fetchActivity(time, activities)
            addDict(activities, self.total_activities)
            return activities
        else:
            return self.total_activities

    def recomputeTA(self, model_id, time):
        """
        Recompute the timeAdvance of a specific model and reapply it. It should only be called after the model was changed using one of the provided functions.
        The change will seemingly have happened right after the last simulation step, so your timeAdvance should **NOT** return something smaller than this.
        The actual *absolute* time_next will be determined at the time of the last transition too. If the model was not altered in a way that causes a major change
        to the state, the *elapsed* time attribute will take care of this call perfectly.
        """
        if hasattr(self.model, "scheduler"):
            model = self.model_ids[model_id]
            # Termination time will always be correct
            model.elapsed = time - model.time_last[0]
            ta = model.timeAdvance()
            model.time_next = (time + model.elapsed + ta, 1)
            if model.time_next[0] < time:
                raise DEVSException("Model user modification causes a transition in the past")
            self.model.scheduler.massReschedule([model])
            self.model.setTimeNext()
        else:
            # We have not yet run coupledInit, so this will happen automatically
            pass
