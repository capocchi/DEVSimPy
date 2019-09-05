import sys
sys.path.append("../src/")
from DEVS import CoupledDEVS, AtomicDEVS, RootDEVS, directConnect
from infinity import INFINITY
from collections import defaultdict
from util import allZeroDict, addDict

from statesavers import PickleHighestState as state_saver
from message import NetworkMessage
from messageScheduler import MessageScheduler

class SimulatedCModel(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "root")
        self.model1 = self.addSubModel(SimulatedModel(1), 0)
        self.model2 = self.addSubModel(SimulatedModel(2), 1)
        self.model3 = self.addSubModel(SimulatedModel(3), 1)
        self.connectPorts(self.model1.outport, self.model2.inport)
        self.connectPorts(self.model2.outport, self.model3.inport)
        self.connectPorts(self.model3.outport, self.model1.inport)

class ModelState(object):
    def __init__(self, value):
        self.value = value
        self.stateHistory = []

class SimulatedModel(AtomicDEVS):
    def __init__(self, name):
        AtomicDEVS.__init__(self, str(name))
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")
        if name == 1:
            self.state = ModelState(2)
        else:
            self.state = ModelState(None)

    def intTransition(self):
        #print("INTERNAL TRANSITION @ %s, %s" % (self.getModelFullName(), self.timeLast))
        self.state.value = None
        self.state.stateHistory.append("INT " + str(self.timeLast))
        print(("HISTORY of %s: %s" % (self.getModelFullName(), self.state.stateHistory)))
        return self.state

    def extTransition(self, inputs):
        #print("EXTERNAL TRANSITION @ %s, %s" % (self.getModelFullName(), self.timeLast))
        self.state.value = inputs[self.inport][0]
        self.state.stateHistory.append("EXT " + str(self.timeLast))
        print(("HISTORY of %s: %s" % (self.getModelFullName(), self.state.stateHistory)))
        return self.state

    def timeAdvance(self):
        if self.state.value is not None:
            return 0.1
        else:
            return 1.0
            #return INFINITY

    def outputFnc(self):
        return {self.outport: [self.state.value]}

class Cluster(CoupledDEVS):
    def __init__(self, nodes):
        CoupledDEVS.__init__(self, "Cluster")
        self.nodes = [self.addSubModel(Node(i, nodes)) for i in range(nodes)]
        self.network = [[self.addSubModel(Network("%i-->%i" % (j, i))) for i in range(nodes)] for j in range(nodes)]

        for startid in range(nodes):
            for endid in range(nodes):
                self.connectPorts(self.nodes[startid].outports[endid], self.network[startid][endid].inport)
                self.connectPorts(self.network[startid][endid].outport, self.nodes[endid].inports[startid])

class NodeState(object):
    def __init__(self, name, totalsize):
        self.simulationtime = (0, 0)
        self.prevtime = (0, 0)
        self.terminationtime = (3, 0)
        model = SimulatedCModel()
        self.model_ids = []
        locations = defaultdict(list)
        model.finalize(name="", model_counter=0, model_ids=self.model_ids, locations=locations, selectHierarchy=[])
        if isinstance(model, CoupledDEVS):
            model.componentSet = directConnect(model.componentSet, True)
        self.destinations = [None] * len(model.componentSet)
        self.kernels = len(list(locations.keys()))
        local = []
        for m in model.componentSet:
            self.destinations[m.model_id] = m if m.location == name else m.location
            if m.location == name:
                m.timeNext = (m.timeAdvance(), 1)
                m.timeLast = (0, 0)
                m.oldStates = [state_saver(m.timeLast, m.timeNext, m.state, 0.0, {}, 0.0)]
                local.append(m)
        self.model = RootDEVS(local, model.componentSet, ("schedulerML", "SchedulerML"))
        self.model.setScheduler(self.model.schedulerType)
        self.model.setTimeNext()
        self.externalQueue = {}
        self.color = False
        self.sendmsgcounter = 0
        self.outputQueue = []
        self.messageScheduler = MessageScheduler()
        self.V = [{}, {}, {}, {}]
        self.Tmin = float('inf')
        self.blockOutgoing = None
        self.run_GVT = 1.0
        self.gvt_check = None
        self.GVT = -float('inf')
        self.relocation_rules = None
        self.kernels_to_relocate = None
        from manualRelocator import ManualRelocator
        self.relocator = ManualRelocator()
        self.relocator.addDirective(1.0, 1, 0)
        self.locked = False
        self.accumulator = {}

    def copy(self):
        #TODO keep this up to date
        import pickle
        a = pickle.loads(pickle.dumps(self))
        a.model = self.model
        a.model_ids = list(self.model_ids)
        a.destinations = list(self.destinations)
        a.externalQueue = dict(self.externalQueue)
        a.outputQueue = list(self.outputQueue)
        return a

    def __getstate__(self):
        retdict = {}
        for i in dir(self):
            if getattr(self, i).__class__.__name__ in ["instancemethod", "method-wrapper", "builtin_function_or_method"]:
                continue
            elif str(i).startswith("__"):
                continue
            retdict[str(i)] = getattr(self, i)
        return retdict

    def __setstate__(self, inp):
        for i in inp:
            setattr(self, i, inp[i])

class Node(AtomicDEVS):
    def __init__(self, name, totalsize):
        AtomicDEVS.__init__(self, "Node_%i" % name)
        self.nodename = name
        self.totalsize = totalsize
        self.inports = [self.addInPort("inport_%i" % i) for i in range(totalsize)]
        self.outports = [self.addOutPort("outport_%i" % i) for i in range(totalsize)]
        self.state = NodeState(name, totalsize)

    def genUUID(self):
        self.state.sendmsgcounter += 1
        return "%s-%s" % (self.nodename, self.state.sendmsgcounter)

    def send(self, model_id, timestamp, content):
        if self.state.blockOutgoing == timestamp:
            return
        msg = NetworkMessage(timestamp, content, self.genUUID(), self.state.color, model_id)
        self.state.outputQueue.append(msg)
        self.notifySend(self.state.destinations[model_id], timestamp[0], msg.color)
        self.state.externalQueue.setdefault(self.outports[self.state.destinations[model_id]], []).append(msg)

    def processMessage(self, clock):
        try:
            message = self.state.messageScheduler.readFirst()
        except IndexError:
            # No input messages
            return clock
        if message.timestamp < clock:
            # The message is sent before the timenext, so update the clock
            clock = message.timestamp
        try:
            while (abs(clock[0] - message.timestamp[0]) < 1e-6 and (clock[1] == message.timestamp[1])):
                print(("Process message with UUID " + str(message.uuid)))
                for port in message.content:
                    port.hostDEVS.myInput.setdefault(port, []).extend(message.content[port])
                    self.state.transitioning[port.hostDEVS] |= 2
                self.state.messageScheduler.removeFirst()
                message = self.state.messageScheduler.readFirst()
        except IndexError:
            # At the end of the scheduler, so we are done
            pass
        return clock

    def receiveControl(self, msg, first=False):
        self.state.controlmsg = msg
        m_clock = msg[0]
        m_send = msg[1]
        waiting_vector = msg[2]
        accumulating_vector = msg[3]

        color = self.state.color
        finished = (self.nodename == 0 and not first and (color == 0 or color == 2))
        if self.nodename == 0 and not first:
            if not allZeroDict(waiting_vector):
                raise DEVSException("GVT bug detected")
            waiting_vector = accumulating_vector
            accumulating_vector = {}
        if finished:
            from math import floor
            GVT = floor(min(m_clock, m_send))
            self.state.accumulator = waiting_vector
            self.state.externalQueue.setdefault(self.outports[self.nodename], []).append(("setGVT_local", [GVT, [], self.state.relocator.useLastStateOnly()]))
            return None
        else:
            return self.tryIfOk(color, waiting_vector, accumulating_vector)

        """
        if self.state.color == 0 or self.state.color == 2:
            # We are currently white, about to turn red
            if self.nodename == 0 and not first:
                # The controller received the message that went around completely
                # The count != check is needed to distinguish between init and finish
                # So we are finished now, don't update the color here!!
                if not allZeroDict(count):
                    raise DEVSException("GVT bug detected")
                # Perform some rounding to prevent slight deviations due to floating point errors
                from math import floor
                GVT = floor(min(m_clock, m_send))
                print("Found GVT " + str(GVT))
                # Do this with a proxy to make it async
                self.state.externalQueue.setdefault(self.outports[self.nodename], []).append(("setGVT_local", [GVT, [], self.state.relocator.useLastStateOnly()]))
            else:
                # Either at the controller at init
                #  or just a normal node that is about to turn red
                self.state.color = (self.state.color + 1) % 4
                addDict(count, self.state.V[v])
                self.state.V[v] = {}
                msg = [min(m_clock, self.state.prevtime[0]), min(m_send, self.state.Tmin), count]
                self.state.externalQueue.setdefault(self.outports[(self.nodename+1)%self.totalsize], []).append(("receiveControl", [msg]))
            return None
        elif self.state.color == 1 or self.state.color == 3:
            # We are currently red, about to turn white
            # First wait for all messages in the medium
            return self.tryIfOk(v, count)
        """

    def findAndPerformRelocations(self, GVT, activities, horizon):
        relocate = self.state.relocator.getRelocations(GVT, activities, horizon)
        relocate = {key: relocate[key] for key in relocate if self.state.model_ids[key].location != relocate[key] and self.state.model_ids[key].relocatable}

        if not relocate:
            self.state.run_GVT = 1.0
            return

        kernels = {}
        self.state.locked_kernels = set()
        relocation_rules = {}
        for model_id in relocate:
            source = self.state.model_ids[model_id].location
            destination = relocate[model_id]
            if source == destination:
                continue
            kernels[source] = kernels.get(source, 0) + 1
            kernels[destination] = kernels.get(destination, 0) + 1
            if kernels[source] == 1:
                # We are the first to lock it, so actually send the lock
                self.state.externalQueue.setdefault(self.outports[source], []).append(("requestMigrationLock", []))
                #self.getProxy(source).requestMigrationLock()
            if kernels[destination] == 1:
                # We are the first to lock it, so actually send the lock
                self.state.externalQueue.setdefault(self.outports[destination], []).append(("requestMigrationLock", []))
                #self.getProxy(destination).requestMigrationLock()
            relocation_rules.setdefault((source, destination), set()).add(model_id)
        self.performRelocations(relocation_rules, kernels)

    def performRelocations(self, relocation_rules, kernels):
            for source, destination in list(relocation_rules.keys()):
                if source in self.state.locked_kernels and destination in self.state.locked_kernels:
                    models = relocation_rules[(source, destination)]
                    unlock = []
                    if kernels[source] == 1:
                        unlock.append(source)
                    if kernels[destination] == 1:
                        unlock.append(destination)
                    self.state.externalQueue.setdefault(self.outports[source], []).append(("migrateTo", [destination, models, unlock]))
                    #self.getProxy(source).migrateTo(destination, models)
                    del relocation_rules[(source, destination)]
                    kernels[source] -= len(models)
                    kernels[destination] -= len(models)
            if relocation_rules:
                # Still something to do
                self.state.relocation_rules = relocation_rules
                self.state.kernels_to_relocate = kernels
            else:
                # At the end, so a normal return
                self.state.relocation_rules = None
                self.state.kernels_to_relocate = None

    def setGVT_local(self, GVT, activities, lastStateOnly):
        if GVT < self.state.GVT:
            raise DEVSException("GVT cannot decrease from " + str(self.GVT) + " to " + str(GVT) + "!")
        if GVT == self.state.GVT:
            # At the controller too
            # Restart the GVT algorithm within 1 time unit
            if activities:
                if self.state.oldGVT == -float('inf'):
                    self.oldGVT = 0.
                horizon = self.state.GVT - self.state.oldGVT
                self.findAndPerformRelocations(GVT, activities, horizon)
        else:
            self.state.oldGVT = self.state.GVT
            self.state.GVT = GVT

            nqueue = []
            self.state.messageScheduler.cleanup((GVT, 1))

            #self.performActions(GVT)

            found = False
            for index in range(len(self.state.outputQueue)):
                if self.state.outputQueue[index].timestamp[0] >= GVT:
                    found = True
                    self.state.outputQueue = self.state.outputQueue[index:]
                    break
            if not found:
                self.state.outputQueue = []
            self.state.activities = {}
            self.state.model.setGVT(GVT, self.state.activities, lastStateOnly)
            if lastStateOnly:
                activitySum = 0
            else:
                activitySum = sum(self.state.activities.values())
            activities.append((self.name, activitySum))
            self.state.externalQueue.setdefault(self.outports[(self.nodename+1)%self.totalsize], []).append(("setGVT_local", [GVT, activities, lastStateOnly]))

    def tryIfOk(self, color, waiting_vector, accumulating_vector):
        prevcolor = 3 if color == 0 else color - 1
        if self.state.V[prevcolor].get(self.nodename, 0) + self.state.controlmsg[2].get(self.nodename, 0) <= 0:
            addDict(waiting_vector, self.state.V[prevcolor])
            addDict(accumulating_vector, self.state.V[color])
            self.state.V[prevcolor] = {}
            self.state.V[color] = {}
            ntime = self.state.prevtime[0] if self.nodename == 0 else min(self.state.controlmsg[0], self.state.prevtime[0])
            msg = [ntime, min(self.state.controlmsg[1], self.state.Tmin), waiting_vector, accumulating_vector]
            self.state.Tmin = float('inf')
            self.state.externalQueue.setdefault(self.outports[(self.nodename+1)%self.totalsize], []).append(("receiveControl", [msg]))
            self.state.color = (self.state.color + 1) % 4
            return False
        else:
            return color, waiting_vector, accumulating_vector
        
    def activateModel(self, model_id, currentState):
        new_model = self.state.model_ids[model_id]
        old_location = new_model.location
        new_model.location = self.nodename
        self.state.model.componentSet.append(new_model)
        self.state.model.local_model_ids.add(new_model.model_id)
        new_model.timeLast = currentState[0]
        new_model.timeNext = currentState[1]
        new_model.state = currentState[2]
        new_model.oldStates = [state_saver(new_model.timeLast, new_model.timeNext, new_model.state, 0.0, {}, 0.0)]
        # It is a new model, so add it to the scheduler too
        self.state.model.scheduler.schedule(new_model)
        self.state.destinations[model_id] = new_model
        self.state.model.setTimeNext()
        self.state.activities[model_id] = 0.0

    def messageTransfer(self, extraction):
        self.state.messageScheduler.insert(extraction, self.state.model_ids)

    def migrateTo(self, destination, model_ids, unlock):
        # Assumes that the simlock is already acquired
        # Make sure that the model that we are migrating is local here
        #assert info("Migrating " + str(model_ids) + " to " + str(destination))
        models = set()
        for model_id in model_ids:
            if isinstance(self.state.destinations[model_id], int):
                raise DEVSException("Cannot migrate model that is not local to the source!")
            if not self.state.destinations[model_id].relocatable:
                raise DEVSException("Model %s was marked as fixed and is therefore not allowed to be relocated" % self.state.destinations[model_id].getModelFullName())
            models.add(self.state.destinations[model_id])
        destination = int(destination)
        if destination == self.name:
            # Model is already there...
            return
        #assert info("Migration approved of %s from node %d to node %d" % (model_ids, self.name, destination))

        for model in models:
            # All models are gone here, so remove them from the scheduler
            self.state.model.scheduler.unschedule(model)

        for i in range(self.state.kernels):
            if i != destination and i != self.name:
                self.state.externalQueue.setdefault(self.outports[i], []).append(("notifyMigration", [model_ids, destination]))
                #self.getProxy(i).notifyMigration(model_ids, destination)
        self.state.externalQueue.setdefault(self.outports[destination], []).append(("messageTransfer", [self.state.messageScheduler.extract(model_ids)]))
        #remote.messageTransfer(self.inputScheduler.extract(model_ids))
        for model in models:
            # No need to ask the new node whether or not there are specific nodes that also have to be informed
            self.state.externalQueue.setdefault(self.outports[destination], []).append(("activateModel", [model.model_id, (model.timeLast, model.timeNext, model.state)]))
            #remote.activateModel(model.model_id, (model.timeLast, model.timeNext, model.state))
            # Delete our representation of the model
            model.state = None
            model.oldStates = []
            del self.state.activities[model.model_id]
        for m in unlock:
            self.state.externalQueue.setdefault(self.outports[m], []).append(("migrationUnlock", []))

        # Remove the model from the componentSet of the RootDEVS
        self.state.model.componentSet = [m for m in self.state.model.componentSet if m not in models]
        for model_id in model_ids:
            self.state.model.local_model_ids.remove(model_id)
            self.state.destinations[model_id] = destination
            self.state.model_ids[model_id].location = destination

        # Now update the timeNext and timeLast values here
        self.state.model.setTimeNext()

    def notifyMigration(self, model_ids, destination):
        if destination == self.nodename:
            # No need to notify ourselves, simply here for safety as it shouldn't be called
            return
        for model_id in model_ids:
            self.state.destinations[model_id] = destination
            self.state.model_ids[model_id].location = destination

    def requestMigrationLock(self):
        self.state.locked = True
        self.revert_local((self.state.GVT, 0))
        self.state.externalQueue.setdefault(self.outports[0], []).append(("notifyLocked", [self.nodename]))

    def migrationUnlock(self):
        self.state.locked = False

    def notifyLocked(self, name):
        self.state.locked_kernels.add(name)

    def intTransition(self):
        # Just do some processing
        self.state.run_GVT -= self.timeAdvance()
        self.state.externalQueue = {}
        self.state.transitioning = defaultdict(int)

        if self.state.run_GVT <= 0 and self.nodename == 0:
            # Start the GVT algorithm
            self.receiveControl([float('inf'), float('inf'), self.state.accumulator, {}], True)
            self.state.run_GVT = float('inf')
        if self.state.gvt_check is not None:
            rv = self.tryIfOk(*self.state.gvt_check)
            if not isinstance(rv, tuple):
                self.state.gvt_check = None

        if self.state.relocation_rules is not None:
            self.performRelocations(self.state.relocation_rules, self.state.kernels_to_relocate)
            return self.state

        if self.state.locked:
            return self.state

        ctime = self.processMessage(self.state.model.timeNext)
        if ctime > self.state.terminationtime:
            self.state.simulationtime = ctime
            return self.state
        outputs = {}
        transitioning = self.state.model.scheduler.getImminent(ctime)
        for i in transitioning:
            outputs.update(i.outputFnc())
            self.state.transitioning[i] |= 1
        remotes = {}
        for i in outputs:
            for dest in i.outLine:
                destADEVS = dest.hostDEVS
                if destADEVS.location == self.nodename:
                    destADEVS.myInput.setdefault(dest, []).extend(outputs[i])
                    self.state.transitioning[destADEVS] |= 2
                else:
                    remotes.setdefault(destADEVS.model_id, {}).setdefault(dest.port_id, []).extend(outputs[i])
        for destination in remotes:
            self.send(destination, ctime, remotes[destination])
        for aDEVS in self.state.transitioning:
            t = self.state.transitioning[aDEVS]
            aDEVS.timeLast = ctime
            activityTrackingPreValue = aDEVS.preActivityCalculation()
            if t == 1:
                aDEVS.state = aDEVS.intTransition()
            elif t == 2:
                aDEVS.elapsed = ctime[0] - aDEVS.timeLast[0] 
                aDEVS.state = aDEVS.extTransition(aDEVS.myInput)
            elif t == 3:
                aDEVS.state = aDEVS.confTransition(aDEVS.myInput)
            ta = aDEVS.timeAdvance()
            aDEVS.timeNext = (aDEVS.timeLast[0] + ta, 1 if ta != 0 else aDEVS.timeLast[1] + 1)
            aDEVS.oldStates.append(state_saver(aDEVS.timeLast, aDEVS.timeNext, aDEVS.state, aDEVS.postActivityCalculation(activityTrackingPreValue), {}, 0))
            aDEVS.myInput = {}
        self.state.model.scheduler.massReschedule(list(self.state.transitioning.keys()))
        self.state.prevtime = ctime
        self.state.model.setTimeNext()
        self.state.simulationtime = self.state.model.timeNext
        return self.state

    def notifyReceive(self, color):
        self.state.V[color][self.nodename] = self.state.V[color].get(self.nodename, 0) - 1

    def notifySend(self, destination, timestamp, color):
         self.state.V[color][destination] = self.state.V[color].get(destination, 0) + 1
         if color == 1 or color == 3:
            self.state.Tmin = min(self.state.Tmin, timestamp)

    def revert_local(self, time):
        self.state.messageScheduler.revert(time)
        self.state.model.revert(time, False)
        self.state.model.setTimeNext()
        self.state.prevtime = time
        self.state.simulationtime = (0, 0)

        # Invalidate all output messages after or at time
        end = -1
        unschedules = {}
        unschedules_mintime = {}
        print(("Reverting to time " + str(time)))
        for index, value in enumerate(self.state.outputQueue):
            # Do not invalidate messages at this time itself, as they are processed in this time step and not generated in this timestep
            if value.timestamp > time:
                model_id = value.destination
                unschedules_mintime[model_id] = min(unschedules_mintime.get(model_id, (float('inf'), 0)), value.timestamp)
                unschedules.setdefault(model_id, []).append(value.uuid)
            else:
                #assert debug("NOT invalidating " + str(value.uuid))
                end = index
        self.state.outputQueue = self.state.outputQueue[:end+1]

        try:
            self.state.blockOutgoing = self.state.outputQueue[-1].timestamp
        except IndexError:
            self.state.blockOutgoing = None

        # Don't need the Vlock here, as we already have it
        for model_id in unschedules:
            dest_kernel = self.state.destinations[model_id]
            if not isinstance(dest_kernel, int):
                raise DEVSException("Impossible")
                continue
            mintime = unschedules_mintime[model_id]
            # Assume we have the simlock already
            self.state.externalQueue.setdefault(self.outports[dest_kernel], []).append(("receiveAntiMessage", [mintime, model_id, unschedules[model_id], self.state.color]))
            self.notifySend(dest_kernel, mintime[0], self.state.color)

    def extTransition(self, inputs):
        self.state.run_GVT -= self.elapsed
        for port in inputs:
            for msg in inputs[port]:
                if isinstance(msg, NetworkMessage):
                    self.notifyReceive(msg.color)
                    if msg.destination not in self.state.model.local_model_ids:
                        print(("FORWARD MSG " + str(msg.uuid)))
                        dest = self.state.destinations[msg.destination]
                        msg.color = self.state.color
                        self.notifySend(dest, msg.timestamp[0], msg.color)
                        self.state.externalQueue.setdefault(self.outports[dest], []).append(msg)
                        continue
                    msg.content = {self.state.model_ids[msg.destination].ports[port]: msg.content[port] for port in msg.content}
                    if msg.timestamp <= self.state.prevtime:
                        self.revert_local(msg.timestamp)
                    self.state.messageScheduler.schedule(msg)
                elif isinstance(msg, tuple):
                    # Other kind of message
                    action, args = msg
                    if action == "receiveControl":
                        rv = getattr(self, action)(*args)
                        if isinstance(rv, tuple):
                            # Try again later
                            self.state.gvt_check = rv
                        else:
                            self.state.gvt_check = None
                    else:
                        getattr(self, action)(*args)
        # Put the return values in a queue if necessary
        self.state.simulationtime = (0, 0)
        return self.state

    def receiveAntiMessage(self, time, model_id, uuids, color):
        self.notifyReceive(color)
        print(("Received anti message for uuids " + str(uuids)))
        if model_id not in self.state.model.local_model_ids and model_id is not None:
            print("FORWARD ANTIMSG")
            self.state.externalQueue.setdefault(self.outports[self.state.destinations[model_id]], []).append(("receiveAntiMessages", [mintime, model_id, uuids, self.state.color]))
            self.notifySend(self.state.destinations[model_id], mintime[0], self.state.color)
            return
        if time <= self.state.prevtime:
            self.revert_local(time)
        self.state.messageScheduler.massUnschedule(uuids)

    def timeAdvance(self):
        if self.state.externalQueue:
            return 0.01
        elif self.state.simulationtime < self.state.terminationtime:
            return 0.1
        else:
            return INFINITY

    def outputFnc(self):
        return self.state.externalQueue

class NetworkState(object):
    def __init__(self):
        self.lst = []

    def copy(self):
        a = NetworkState()
        a.lst = list(self.lst)
        return a

class Network(AtomicDEVS):
    def __init__(self, name):
        AtomicDEVS.__init__(self, name)
        self.state = NetworkState()
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")

    def intTransition(self):
        self.state.lst = []
        return self.state

    def extTransition(self, inputs):
        msgs = inputs[self.inport]
        self.state.lst.extend(msgs)
        return self.state

    def timeAdvance(self):
        if self.state.lst:
            #return 1.0
            return 0.1
            #return 0.01
        else:
            return INFINITY

    def outputFnc(self):
        return {self.outport: self.state.lst}
