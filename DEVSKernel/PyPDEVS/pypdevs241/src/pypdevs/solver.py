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
The actual DEVS solvers containing the main DEVS implementation
"""

from collections import defaultdict

from pypdevs.DEVS import *

from pypdevs.util import *
from pypdevs.logger import *

from pypdevs.classicDEVSWrapper import ClassicDEVSWrapper

class Solver(object):
    """
    A unified DEVS solver, containing all necessary functions
    """
    def __init__(self, listeners = {}):
        """
        Constructor
        """
        self.activities = {}
        self.dsdevs_dict = {}
        self.listeners = listeners

    def atomicOutputGenerationEventTracing(self, aDEVS, time):
        """
        Wrapper for the AtomicDEVS output function, which will save event counts

        :param aDEVS: the AtomicDEVS model that generates the output
        :param time: the time at which the output must be generated
        :returns: dict -- the generated output
        """
        retval = Solver.atomicOutputGeneration(self, aDEVS, time)
        for port in retval:
            port.msg_count += len(retval[port])
        return retval

    def atomicOutputGeneration(self, aDEVS, time):
        """
        AtomicDEVS function to generate output, invokes the outputFnc function of the model.

        :param aDEVS: the AtomicDEVS model that generates the output
        :param time: the time at which the output must be generated
        :returns: dict -- the generated output
        """
        aDEVS.my_output = aDEVS.outputFnc()

        # Being here means that this model created output, so it triggered its internal transition
        # save this knowledge in the basesimulator for usage in the actual transition step
        self.transitioning[aDEVS] |= 1

        return aDEVS.my_output

    def massAtomicTransitions(self, trans, clock):
        """
        AtomicDEVS function to perform all necessary transitions, 
        does so on a collection of models for performance.

        :param trans: iterable containing all models and their requested transition
        :param clock: the time at which the transition must happen
        """
        t, age = clock
        partialmod = []
        for aDEVS in trans:
            ttype = trans[aDEVS]

            ###########
            ## Memoization and activity tracking code
            ##   Skipped in local simulation
            if not self.temporary_irreversible:
                # Memo part
                if self.memoization and len(aDEVS.memo) >= 2:
                    found = False
                    prev = aDEVS.memo.pop()
                    memo = aDEVS.memo[-1]
                    if memo.time_last == clock and prev.loadState() == aDEVS.state:
                        if ttype == 1:
                            found = True
                        elif aDEVS.my_input == memo.my_input:
                            # Inputs should be equal too
                            if ttype == 3:
                                found = True
                            elif aDEVS.elapsed == memo.elapsed and ttype == 2:
                                found = True
                    if found:
                        aDEVS.state = memo.loadState()
                        aDEVS.time_last = clock
                        aDEVS.time_next = memo.time_next
                        # Just add the copy
                        aDEVS.old_states.append(memo)
                        if self.do_some_tracing:
                            # Completely skip all these calls if no tracing, saves us a lot of function calls
                            if ttype == 1:
                                self.tracers.tracesInternal(aDEVS)
                            elif ttype == 2:
                                self.tracers.tracesExternal(aDEVS)
                            elif ttype == 3:
                                self.tracers.tracesConfluent(aDEVS)
                        aDEVS.my_input = {}
                        if self.relocation_pending:
                            # Quit ASAP by throwing an exception
                            raise QuickStopException()
                        continue
                    else:
                        aDEVS.memo = []
                activity_tracking_prevalue = aDEVS.preActivityCalculation()
            elif self.activity_tracking:
                activity_tracking_prevalue = aDEVS.preActivityCalculation()
            ###########

            # Make a copy of the message before it is passed to the user
            if self.msg_copy != 2:
                # Prevent a pass statement, which still consumes some time in CPython
                if self.msg_copy == 1:
                    # Using list comprehension inside of dictionary comprehension...
                    aDEVS.my_input = {key: 
                            [i.copy() for i in aDEVS.my_input[key]] 
                            for key in aDEVS.my_input}
                elif self.msg_copy == 0:
                    # Dictionary comprehension
                    aDEVS.my_input = {key: 
                            pickle.loads(pickle.dumps(aDEVS.my_input[key], 
                                                      pickle.HIGHEST_PROTOCOL)) 
                            for key in aDEVS.my_input}

            # NOTE ttype mappings:            (EI)
            #       1 -- Internal transition  (01)
            #       2 -- External transition  (10)
            #       3 -- Confluent transition (11)
            if ttype == 1:
                # Internal only
                aDEVS.elapsed = None
                aDEVS.state = aDEVS.intTransition()
            elif ttype == 2:
                # External only
                aDEVS.elapsed = t - aDEVS.time_last[0]
                aDEVS.state = aDEVS.extTransition(aDEVS.my_input)
            elif ttype == 3:
                # Confluent
                aDEVS.elapsed = 0.
                aDEVS.state = aDEVS.confTransition(aDEVS.my_input)
            else:
                raise DEVSException(
                    "Problem in transitioning dictionary: unknown element %s" 
                    % ttype)

            ta = aDEVS.timeAdvance()
            aDEVS.time_last = clock

            if ta < 0:
                raise DEVSException("Negative time advance in atomic model '" + \
                                    aDEVS.getModelFullName() + "' with value " + \
                                    str(ta) + " at time " + str(t))

            # Update the time, this is just done in the timeNext, as this will propagate to the basesimulator
            aDEVS.time_next = (t + ta, 1 if ta else (age + 1))

            # Save the state
            if not self.temporary_irreversible:
                partialmod.append(aDEVS)
                # But only if there are multiple kernels, since otherwise there would be no other kernel to invoke a revertion
                # This can save us lots of time for local simulation (however, all other code is written with parallellisation in mind...)
                activity = aDEVS.postActivityCalculation(activity_tracking_prevalue)
                aDEVS.old_states.append(self.state_saver(aDEVS.time_last,
                                                         aDEVS.time_next,
                                                         aDEVS.state,
                                                         activity,
                                                         aDEVS.my_input,
                                                         aDEVS.elapsed))
                if self.relocation_pending:
                    # Quit ASAP by throwing an exception
                    for m in partialmod:
                        # Roll back these models to before the transitions
                        m.time_next = m.old_states[-1].time_next
                        m.time_last = m.old_states[-1].time_last
                        m.state = m.old_states[-1].loadState()
                    self.model.scheduler.massReschedule(trans)
                    self.server.flushQueuedMessages()
                    raise QuickStopException()
            elif self.activity_tracking:
                activity = aDEVS.postActivityCalculation(activity_tracking_prevalue)
                self.total_activities[aDEVS.model_id] += activity

            if self.do_some_tracing:
                # Completely skip all these calls if no tracing, saves us a lot of function calls
                if ttype == 1:
                    self.tracers.tracesInternal(aDEVS)
                elif ttype == 2:
                    self.tracers.tracesExternal(aDEVS)
                elif ttype == 3:
                    self.tracers.tracesConfluent(aDEVS)
      
            # Clear the bag
            aDEVS.my_input = {}
        self.server.flushQueuedMessages()

    def atomicInit(self, aDEVS, time):
        """
        AtomicDEVS function to initialise the model

        :param aDEVS: the model to initialise
        """
        aDEVS.time_last = (time[0] - aDEVS.elapsed, 1)
        ta = aDEVS.timeAdvance()

        if ta < 0:
            raise DEVSException("Negative time advance in atomic model '" + \
                                aDEVS.getModelFullName() + "' with value " + \
                                str(ta) + " at initialisation")
        aDEVS.time_next = (aDEVS.time_last[0] + ta, 1)
        # Save the state
        if not self.irreversible:
            aDEVS.old_states.append(self.state_saver(aDEVS.time_last,
                                                     aDEVS.time_next,
                                                     aDEVS.state,
                                                     0.0,
                                                     {},
                                                     0.0))

        # All tracing features
        self.tracers.tracesInit(aDEVS, time)

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
            model.time_next = (model.time_next[0], model.time_next[1] + 1)
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
                # Make a set first to remove duplicates
                colliding = list(set([m.select_hierarchy[level] for m in pending]))
                chosen = model.select_hierarchy[level-1].select(
                        sorted(colliding, key=lambda i:i.getModelFullName()))
                pending = [m for m in pending 
                             if m.select_hierarchy[level] == chosen]
                level += 1
            child = pending[0]
        else:
            child = imminent[0]
        # Recorrect the timeNext of the model that will transition
        child.time_next = (child.time_next[0], child.time_next[1] - 1)

        outbag = child.my_output = ClassicDEVSWrapper(child).outputFnc()
        self.transitioning[child] = 1

        for outport in outbag:
            for inport, z in outport.routing_outline:
                payload = outbag[outport]
                if z is not None:
                    payload = [z(pickle.loads(pickle.dumps(m))) for m in payload]
                aDEVS = inport.host_DEVS
                aDEVS.my_input[inport] = list(payload)
                self.transitioning[aDEVS] = 2
                reschedule.add(aDEVS)
        # We have now generated the transitioning variable, though we need some small magic to have it work for classic DEVS
        self.transitioning = {ClassicDEVSWrapper(m): self.transitioning[m] 
                              for m in self.transitioning}
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
                if not hasattr(outport, "routing_outline"):
                    raise Exception(outport)
                for inport, z in outport.routing_outline:
                    aDEVS = inport.host_DEVS
                    if z is not None:
                        payload = [z(pickle.loads(pickle.dumps(m))) 
                                   for m in payload]
                    if aDEVS.model_id in self.model.local_model_ids:
                        # This setdefault call is responsible for our non-linear runtime in several situations...
                        aDEVS.my_input.setdefault(inport, []).extend(payload)
                        self.transitioning[aDEVS] |= 2
                    else:
                        remotes.setdefault(aDEVS.model_id, 
                                           {}).setdefault(inport.port_id, 
                                                          []).extend(payload)
        for destination in remotes:
            self.send(destination, time, remotes[destination])
        return self.transitioning

    def coupledInit(self):
        """
        CoupledDEVS function to initialise the model, calls all its _local_ children too.
        """
        cDEVS = self.model
        time_next = (float('inf'), 1)
        # This part isn't fast, but it doesn't matter, since it just inits everything, optimizing here doesn't
        # matter as it is only called once AND every element has to be initted.
        # Only local models should receive this initialisation from us
        for d in self.local:
            self.atomicInit(d, (0.0, 0))
            time_next = min(time_next, d.time_next)
        # NOTE do not immediately assign to the timeNext, as this is used in the GVT algorithm to see whether a node has finished
        cDEVS.time_next = time_next
        self.model.setScheduler(self.model.scheduler_type)
        self.server.flushQueuedMessages()

    def performDSDEVS(self, transitioning):
        """
        Perform Dynamic Structure detection of the model

        :param transitioning: iteratable to be checked for a dynamic structure transiton
        """
        #TODO setting the server is very dirty
        self.dc_altered = set()
        for m in transitioning:
            m.server = self
        iterlist = [aDEVS.parent for aDEVS in transitioning 
                                 if aDEVS.modelTransition(self.dsdevs_dict)]
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
                    #assert warning("Root DEVS returned True in the modelTransition method; ignoring")
                    continue
                if cDEVS in checked:
                    continue
                checked.add(cDEVS)
                if cDEVS.modelTransition(self.dsdevs_dict):
                    new_iterlist.append(cDEVS.parent)
            # Don't update the iterlist while we are iterating over it
            iterlist = new_iterlist
        if self.dc_altered:
            self.model.redoDirectConnection(self.dc_altered)
