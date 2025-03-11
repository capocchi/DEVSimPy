# -*- coding: Latin-1 -*-
"""
The actual DEVS solvers containing the main DEVS implementation
"""

from collections import defaultdict

from .DEVS import *

from .util import *
from .logger import *

from .classicDEVSWrapper import ClassicDEVSWrapper

class Solver(object):
    """
    A unified DEVS solver, containing all necessary functions
    """
    def __init__(self):
        """
        Constructor
        """
        self.activities = {}
        self.dsdevsdict = {}

    def atomicOutputGenerationEventTracing(self, aDEVS, time):
        """
        Wrapper for the AtomicDEVS output function, which will save event counts

        :param aDEVS: the AtomicDEVS model that generates the output
        :param time: the time at which the output must be generated
        :returns: dict -- the generated output
        """
        retval = Solver.atomicOutputGeneration(self, aDEVS, time)
        for port in retval:
            port.msgcount += len(retval[port])
        return retval

    def atomicOutputGeneration(self, aDEVS, time):
        """
        AtomicDEVS function to generate output, invokes the outputFnc function of the model.

        :param aDEVS: the AtomicDEVS model that generates the output
        :param time: the time at which the output must be generated
        :returns: dict -- the generated output
        """
        aDEVS.myOutput = aDEVS.outputFnc()

        # Being here means that this model created output, so it triggered its internal transition
        # save this knowledge in the basesimulator for usage in the actual transition step
        self.transitioning[aDEVS] |= 1

        return aDEVS.myOutput

    def massAtomicTransitions(self, trans, clock):
        """
        AtomicDEVS function to perform all necessary transitions, does so on a collection of models for performance.

        :param trans: iterable containing all models and their requested transition
        :param clock: the time at which the transition must happen
        """
        t, age = clock
        partialmod = []
        for aDEVS in trans:
            ttype = trans[aDEVS]
            #assert debug("TRANSITION CALLED @ " + str(t) + " (model: " + str(aDEVS.getModelFullName()) + ")")

            ###########
            ## Memoization and activity tracking code
            ##   Skipped in local simulation
            if not self.temporaryIrreversible:
                # Memo part
                if self.memoization and len(aDEVS.memo) >= 2:
                    found = False
                    prev = aDEVS.memo.pop()
                    memo = aDEVS.memo[-1]
                    if memo.timeLast == clock and prev.loadState() == aDEVS.state:
                        if ttype == 1:
                            found = True
                        elif aDEVS.myInput == memo.myInput:
                            # Inputs should be equal too
                            if ttype == 3:
                                found = True
                            elif aDEVS.elapsed == memo.elapsed and ttype == 2:
                                found = True
                    if found:
                        aDEVS.state = memo.loadState()
                        aDEVS.timeLast = clock
                        aDEVS.timeNext = memo.timeNext
                        # Just add the copy
                        aDEVS.oldStates.append(memo)
                        if self.doSomeTracing:
                            # Completely skip all these calls if no tracing, saves us a lot of function calls
                            if ttype == 1:
                                self.tracers.tracesInternal(aDEVS)
                            elif ttype == 2:
                                self.tracers.tracesExternal(aDEVS)
                            elif ttype == 3:
                                self.tracers.tracesConfluent(aDEVS)
                        aDEVS.myInput = {}
                        if self.relocationPending:
                            # Quit ASAP by throwing an exception
                            raise QuickStopException()
                        continue
                    else:
                        aDEVS.memo = []
                activityTrackingPreValue = aDEVS.preActivityCalculation()
            elif self.activityTracking:
                activityTrackingPreValue = aDEVS.preActivityCalculation()
            ###########

            # Make a copy of the message before it is passed to the user
            if self.msgCopy != 2:
                # Prevent a pass statement, which still consumes some time in CPython
                if self.msgCopy == 1:
                    # Using list comprehension inside of dictionary comprehension...
                    aDEVS.myInput = {key: [i.copy() for i in aDEVS.myInput[key]] for key in aDEVS.myInput}
                elif self.msgCopy == 0:
                    # Dictionary comprehension
                    aDEVS.myInput = {key: pickle.loads(pickle.dumps(aDEVS.myInput[key], pickle.HIGHEST_PROTOCOL)) for key in aDEVS.myInput}

            # NOTE ttype mappings:            (EI)
            #       1 -- Internal transition  (01)
            #       2 -- External transition  (10)
            #       3 -- Confluent transition (11)
            if ttype == 1:
                # Internal only
                aDEVS.state = aDEVS.intTransition()
            elif ttype == 2:
                # External only
                aDEVS.elapsed = t - aDEVS.timeLast[0]
                aDEVS.state = aDEVS.extTransition(aDEVS.myInput)
            elif ttype == 3:
                # Confluent
                aDEVS.elapsed = 0.
                aDEVS.state = aDEVS.confTransition(aDEVS.myInput)
            else:
                raise DEVSException("Problem in transitioning dictionary: unknown element " + str(ttype))

            ta = aDEVS.timeAdvance()
            aDEVS.timeLast = clock

            if ta < 0:
                raise DEVSException("Negative time advance in atomic model '" + \
                                    aDEVS.getModelFullName() + "' with value " + \
                                    str(ta) + " at time " + str(t))

            # Update the time, this is just done in the timeNext, as this will propagate to the basesimulator
            aDEVS.timeNext = (t + ta, 1 if ta else (age + 1))

            # Save the state
            if not self.temporaryIrreversible:
                partialmod.append(aDEVS)
                # But only if there are multiple kernels, since otherwise there would be no other kernel to invoke a revertion
                # This can save us lots of time for local simulation (however, all other code is written with parallellisation in mind...)
                #TODO this was switched to before the quickstop check, might prevent some problems?
                aDEVS.oldStates.append(self.state_saver(aDEVS.timeLast, aDEVS.timeNext, aDEVS.state, aDEVS.postActivityCalculation(activityTrackingPreValue), aDEVS.myInput, aDEVS.elapsed))
                if self.relocationPending:
                    # Quit ASAP by throwing an exception
                    for m in partialmod:
                        # Roll back these models to before the transitions
                        m.timeNext = m.oldStates[-1].timeNext
                        m.timeLast = m.oldStates[-1].timeLast
                        m.state = m.oldStates[-1].loadState()
                    self.model.scheduler.massReschedule(trans)
                    self.server.flushQueuedMessages()
                    raise QuickStopException()
            elif self.activityTracking:
                self.totalActivities[aDEVS.model_id] += (aDEVS.postActivityCalculation(activityTrackingPreValue))

            if self.doSomeTracing:
                # Completely skip all these calls if no tracing, saves us a lot of function calls
                if ttype == 1:
                    self.tracers.tracesInternal(aDEVS)
                elif ttype == 2:
                    self.tracers.tracesExternal(aDEVS)
                elif ttype == 3:
                    self.tracers.tracesConfluent(aDEVS)

            # Clear the bag
            aDEVS.myInput = {}
        self.server.flushQueuedMessages()

    def atomicInit(self, aDEVS):
        """
        AtomicDEVS function to initialise the model

        :param aDEVS: the model to initialise
        """
        aDEVS.timeLast = (aDEVS.elapsed, 1)
        ta = aDEVS.timeAdvance()

        if ta < 0:
            raise DEVSException("Negative time advance in atomic model '" + \
                                aDEVS.getModelFullName() + "' with value " + \
                                str(ta) + " at initialisation")
        aDEVS.timeNext = (aDEVS.elapsed + ta, 1)
        # Save the state
        if not self.irreversible:
            aDEVS.oldStates.append(self.state_saver(aDEVS.timeLast, aDEVS.timeNext, aDEVS.state, 0.0, {}, 0.0))

        # All tracing features
        self.tracers.tracesInit(aDEVS)

    def coupledOutputGenerationClassic(self, time):
        """
        CoupledDEVS function to generate the output, calls the atomicDEVS models where necessary. Output is routed too.

        :param time: the time at which output should be generated
        :returns: the models that should be rescheduled
        """
        cDEVS = self.model
        imminent = cDEVS.scheduler.getImminent(time)
        if not imminent:
            # For real time simulation, when a model is interrupted
            return self.transitioning
        reschedule = set(imminent)
        for model in imminent:
            model.timeNext = (model.timeNext[0], model.timeNext[1] + 1)
        # Return value are the models to reschedule
        # self.transitioning are the models that must transition
        if len(imminent) > 1:
            # Perform all selects
            imminent.sort()
            pending = imminent
        
            level = 1
            while len(pending) > 1:
                # Take the model each time, as we need to make sure that the selectHierarchy is valid everywhere
                model = pending[0]
                # This is not the fastest piece of code...
                chosen = model.selectHierarchy[level-1].select(sorted(list(set([m.selectHierarchy[level] for m in pending])), key=lambda i:i.getModelFullName()))
                pending = [m for m in pending if m.selectHierarchy[level] == chosen]
                level += 1
            child = pending[0]
        else:
            child = imminent[0]
        # Recorrect the timeNext of the model that will transition
        child.timeNext = (child.timeNext[0], child.timeNext[1] - 1)

        outbag = child.myOutput = ClassicDEVSWrapper(child).outputFnc()
        self.transitioning[child] = 1

        for outport in outbag:
            for inport, z in outport.routingOutLine:
                payload = outbag[outport]
                if z is not None:
                    payload = [z(pickle.loads(pickle.dumps(m))) for m in payload]
                aDEVS = inport.hostDEVS
                aDEVS.myInput[inport] = list(payload)
                self.transitioning[aDEVS] = 2
                reschedule.add(aDEVS)
        # We have now generated the transitioning variable, though we need some small magic to have it work for classic DEVS
        self.transitioning = {ClassicDEVSWrapper(m): self.transitioning[m] for m in self.transitioning}
        return reschedule

    def coupledOutputGeneration(self, time):
        """
        CoupledDEVS function to generate the output, calls the atomicDEVS models where necessary. Output is routed too.

        :param time: the time at which output should be generated
        :returns: the models that should be rescheduled
        """
        cDEVS = self.model
        remotes = {}
        for child in cDEVS.scheduler.getImminent(time):
            outbag = self.atomicOutputGeneration(child, time)
            for outport in outbag:
                payload = outbag[outport]
                for inport, z in outport.routingOutLine:
                    aDEVS = inport.hostDEVS
                    if z is not None:
                        payload = [z(pickle.loads(pickle.dumps(m))) for m in payload]
                    if aDEVS.model_id in self.model.local_model_ids:
                        # This setdefault call is responsible for our non-linear runtime in several situations...
                        aDEVS.myInput.setdefault(inport, []).extend(payload)
                        self.transitioning[aDEVS] |= 2
                    else:
                        remotes.setdefault(aDEVS.model_id, {}).setdefault(inport.port_id, []).extend(payload)
        for destination in remotes:
            self.send(destination, time, remotes[destination])
        return self.transitioning

    def coupledInit(self):
        """
        CoupledDEVS function to initialise the model, calls all its _local_ children too.
        """
        cDEVS = self.model
        timeNext = (float('inf'), 1)
        # This part isn't fast, but it doesn't matter, since it just inits everything, optimizing here doesn't
        # matter as it is only called once AND every element has to be initted.
        # Only local models should receive this initialisation from us
        for d in self.local:
            self.atomicInit(d)
            timeNext = min(timeNext, d.timeNext)
        # NOTE do not immediately assign to the timeNext, as this is used in the GVT algorithm to see whether a node has finished
        cDEVS.timeNext = timeNext
        self.model.setScheduler(self.model.schedulerType)
        self.server.flushQueuedMessages()

    def performDSDEVS(self, transitioning):
        """
        Perform Dynamic Structure detection of the model

        :param transitioning: iteratable to be checked for a dynamic structure transiton
        """
        #TODO setting the server is very dirty
        for m in transitioning:
            m.server = self
        iterlist = [aDEVS.parent for aDEVS in transitioning if aDEVS.modelTransition(self.dsdevsdict)]
        # Contains all models that are already checked, to prevent duplicate checking.
        # This was not necessary for atomic models, as they are guaranteed to only be called
        # once, as they have no children to induce a structural change on them
        checked = set()
        while iterlist:
            new_iterlist = []
            for cDEVS in iterlist:
                cDEVS.server = self
                if cDEVS is None:
                    # Problematic
                    assert warning("Root DEVS returned True in the modelTransition method; ignoring")
                    continue
                if cDEVS in checked:
                    continue
                checked.add(cDEVS)
                if cDEVS.modelTransition(self.dsdevsdict):
                    new_iterlist.append(cDEVS.parent)
            # Don't update the iterlist while we are iterating over it
            iterlist = new_iterlist
        # We possibly undid the direct connection, so do it again
        self.model.directConnect()
