# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# solvers.py --- DEVS solvers
#                     --------------------------------
#                            Copyright (c) 2013
#                          Jean-Sébastien  BOLDUC
#                             Hans  Vangheluwe
#                            Yentl Van Tendeloo
#                       McGill University (Montréal)
#                     --------------------------------
# Version 2.0                                        last modified: 30/01/13
#  - Split up the solvers to a seperate file
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

from .scheduler import Scheduler
from collections import defaultdict

# Necessary to send COPIES of messages.
try:
    import pickle as pickle
except ImportError:
    import pickle

import sys
from .DEVS import *

from .util import *
from .logger import *

#cython from message cimport Message, NetworkMessage
from .message import Message, NetworkMessage #cython-remove

##  GLOBAL VARIABLES AND FUNCTIONS
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

##  SIMULATOR CLASSES
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class Solver(object):
    def __init__(self):
        self.local = []
        self.id_fetch = {}

    def runUserCode(self, function, args=[]):
        # Run the code as often as needed
        while True:
            try:
                # This will be a transition function, so pass the input list too
                return function(*args)
            except NestingException:
                # Unlock the nested lock to allow a nested simulation, but don't release the actual simlock, to prevent other operations from interfering
                self.nestedlock.release()
                time.sleep(0.1)
                self.nestedlock.acquire()
  
    #@profile
    def atomicReceive(self, aDEVS, msg):
        # For any received message, the time {\tt t} (time at which the message
        # is sent) is the second item in the list {\tt msg}.
        t, age = msg.timestamp
        messagetype = msg.messagetype
        tn = aDEVS.timeNext[0]
        tl = aDEVS.timeLast[0]

        if messagetype == 2:
            if abs(t - tn) >= EPSILON and not self.realtime:
                raise DEVSException("Bad synchronization in atomic model '" + \
                                    aDEVS.getModelFullName() + "' on output " + \
                                    "collection; simulation time = " + str(t) + \
                                    "; model.timeNext = " + str(tn))

            # First call the output function, which (amongst other things) rebuilds
            # the output dictionary {\tt myOutput}:
            aDEVS.myOutput = {}
            # Comply with original simulator
            aDEVS.elapsed = 0.

            if self.allowNested:
                aDEVS.myOutput = self.runUserCode(aDEVS.outputFnc)
            else:
                aDEVS.myOutput = aDEVS.outputFnc()

            # Being here means that this model created output, so it triggered its internal transition
            # save this knowledge in the basesimulator for usage in the actual transition step
            self.transitioning.add(aDEVS)

            # Return the DEVS' output to the parent coupled-DEVS (rather than
            # sending $(y,\,t)$ message).
            return aDEVS.myOutput

        elif messagetype == 1:
            assert debug("TRANSITION CALLED @ " + str(t) + " (model: " + str(aDEVS.getModelFullName()) + ")")
            internal = False
            external = False
            confluent = False
            unneeded = False
            inputempty = aDEVS.myInput == {}
            imminent = abs(t - tn) <= EPSILON
            if not imminent and not inputempty:
                # External transition only
                aDEVS.elapsed = t - tl
                runfunc = aDEVS.extTransition
                external = True
                args = [aDEVS.myInput]
                assert debug("EXTERNAL")
            elif imminent and inputempty:
                # Internal transition only
                runfunc = aDEVS.intTransition
                internal = True
                args = []
                assert debug("INTERNAL")
            elif imminent and not inputempty:
                # Confluent transition
                runfunc = aDEVS.confTransition
                confluent = True
                args = [aDEVS.myInput]
                #print(str(self.name) + "--Confluent bag")
                #for i in aDEVS.myInput.keys():
                    #print(i.hostDEVS.getModelFullName() + " -- " + i.getPortName())
                assert debug("CONFLUENT")
            else:
                unneeded = True

            if unneeded:
                return
            # First unpickle the content to be read
            if self.manualCopy:
                for field in list(aDEVS.myInput.items()):
                    aDEVS.myInput[field[0]] = [i.copy() for i in field[1]]
            else:
                for field in list(aDEVS.myInput.items()):
                    aDEVS.myInput[field[0]] = pickle.loads(pickle.dumps(field[1]))
            if self.allowNested:
                aDEVS.state = self.runUserCode(runfunc, args)
            else:
                aDEVS.state = runfunc(*args)

            # Update time variables
            aDEVS.timeLast = (t, age)
            #print(str(self.name) + "--TA--")
            if self.allowNested:
                ta = self.runUserCode(aDEVS.timeAdvance)
            else:
                ta = aDEVS.timeAdvance()
            #print(str(self.name) + "--DONE TA--")

            if ta < 0:
                raise DEVSException("Negative time advance in atomic model '" + \
                                    aDEVS.getModelFullName() + "' with value " + \
                                    str(ta) + " at time " + str(t))

            # Update the time, this is just done in the timeNext, as this will propagate to the basesimulator
            age = (age + 1) if (ta == 0) else 1
            aDEVS.timeNext = (t + ta, age)
            aDEVS.elapsed = 0.

            # Save the state
            if not self.irreversible:
                # But only if there are multiple kernels, since otherwise there would be no other kernel to invoke a revertion
                # This can save us lots of time for local simulation (however, all other code is written with parallellisation in mind...)
                aDEVS.oldStates.append([aDEVS.timeLast, aDEVS.timeNext, self.savestate(aDEVS.state)])

            if internal:
                self.tracers.tracesInternal(aDEVS)
            elif external:
                self.tracers.tracesExternal(aDEVS)
            elif confluent:
                self.tracers.tracesConfluent(aDEVS)
      
            # Clear the bag
            aDEVS.myInput = {}

        elif messagetype == 3:
            if not(tl - EPSILON <= t <= tn + EPSILON) and not self.realtime:
                raise DEVSException("Bad synchronization in atomic model '" + \
                                    aDEVS.getModelFullName() + "' on message " + \
                                    "reception; simulation time = " + str(t) + \
                                    "; model.timeLast = " + str(tl) + \
                                    "; model.timeNext = " + str(tn))
      
            # Use the updateBag function, as it is possible that multiple messages arrive on a certain input port
            aDEVS.myInput = updateBag(aDEVS.myInput, msg.content)

            # Being here means that we receive an external input, so we should (at least) perform an external
            # transition, so add it for transitioning
            self.transitioning.add(aDEVS)

        elif messagetype == 0:
            aDEVS.timeLast = (t - aDEVS.elapsed, 1)
            #print(str(self.name) + "--TA--")
            if self.allowNested:
                ta = self.runUserCode(aDEVS.timeAdvance)
            else:
                ta = aDEVS.timeAdvance()
            #print(str(self.name) + "--DONE TA--")

            if ta < 0:
                raise DEVSException("Negative time advance in atomic model '" + \
                                    aDEVS.getModelFullName() + "' with value " + \
                                    str(ta) + " at time " + str(t))
            aDEVS.timeNext = (t - aDEVS.elapsed + ta, 1)
            # Save the state
            aDEVS.oldStates.append([aDEVS.timeLast, aDEVS.timeNext, self.savestate(aDEVS.state)])

            # All tracing features
            self.tracers.tracesInit(aDEVS)
        else:
            raise DEVSException("Unrecognized message on atomic model '" + \
                                aDEVS.getModelFullName() + "'")

#    ===================================================================    #

    #@profile
    def processExt(self, t, cDEVS, Y):
        """
        Define the processing of external events once and for all, this is a small slow-down due to an extra
        function call, but it is a lot more maintainable, certainly now that this function's size has exploded
        """
        #TODO this is very high-cost code, optimisations should go here!
        assert debug("At processExt")
        #elems = {}
        elems = defaultdict(lambda : defaultdict(list))

        # All output ports
        assert debug("Should send messages to Y = " + str(Y))
        for outport in Y:
            assert debug("Port " + outport.getPortName() + " is connected to outports: " + str(outport.outLine))
            assert debug("  and to inports: " + str(outport.inLine))
            assert debug("at coupled model " + str(cDEVS.getModelFullName()))
            # For each of them, select the output component of it
            for inport in outport.outLine:
                # Now fetch the model that receives this message
                # A defaultdict, so the values will always be there
                # Do an extend instead of an assignment, as the inport might already have some values on it
                elems[inport.hostDEVS.model_id][inport].extend(Y[outport])

        assert debug("Got elements: " + str(elems))
        for i in elems:
            assert debug("Searching for " + str(i) + " in " + str(self.id_fetch))
            comp = self.id_fetch[i][3]
            assert debug("Should send data to " + str(comp.getModelFullName()))
            # Fetch this model's complete input
            X = elems[i]
            # Send this model it's input
            # Don't update the age, as we are only passing it through
            assert debug("Sending data...")
            assert debug("  data: (t: " + str(t) + ") " + str(X))
            assert debug("  model: " + str(comp))
            if isinstance(comp, RemoteCDEVS):
                assert debug("REMOTE to " + comp.remote_location)
                comp.send(Message(t, 3, X))
            else:
                # Send immediately to ourselves with the new ID, this is a lot faster
                # Though it breaks the transparent network communication
                assert debug("NO REMOTE")
                self.send(comp.model_id, Message(t, 3, X))

    #@profile
    def coupledReceive(self, cDEVS, msg):
        # For any received message, the time {\tt t} (time at which the message 
        # is sent) is the second item in the list {\tt msg}.
        messagetype = msg.messagetype

        # $(@,\,t)$ message --- trigger output functions
        # returns $(y,\,t)$ message for parent coupled-DEVS:
        if messagetype == 2:
            if ((msg.timestamp[0] - cDEVS.timeNext[0]) > EPSILON) and (not self.realtime):
                raise DEVSException("Bad synchronization in coupled model '" + \
                                    cDEVS.getModelFullName() + "' on output " + \
                                    "generation; simulation time = " + str(msg.timestamp[0]) + \
                                    "; model.timeNext = " + str(cDEVS.timeNext[0]))

            cDEVS.timeLast = msg.timestamp
            immChildren = cDEVS.scheduler.getImminent(msg.timestamp, EPSILON)
            outbag = {}
            for child in immChildren:
                # No need to use the updateBag, since no two children will poke on the same ports
                if isinstance(child, RemoteCDEVS):
                    child.send(msg)
                elif isinstance(child, AtomicDEVS):
                #else:
                    Y = self.send(child.model_id, msg)
                    outbag.update(Y)

            self.processExt(msg.timestamp, cDEVS, outbag)

            #TODO is this code still needed?
            myOutput = {}
            for p in cDEVS.OPorts:
                for pi in p.inLine:
                    try:
                        #TODO why a break after the first item?
                        myOutput[p] = outbag[pi]
                        break
                    except KeyError:
                        pass
            cDEVS.myOutput = myOutput
            return cDEVS.myOutput
        
        elif messagetype == 3:
            self.processExt(msg.timestamp, cDEVS, msg.content)

        elif messagetype == 0:
            # Rebuild event-list and update time variables, by sending the
            # initialization message to all the children of the coupled-DEVS. Note
            # that the event-list is not sorted here, but only when the list of
            # {\sl imminent children\/} is needed. Also note that {\tt None} is
            # defined as bigger than any number in Python (stands for $+\infty$).
            cDEVS.timeLast = (0.0, 1)
            cDEVS.timeNext = (float('inf'), 1)
            cDEVS.scheduler = Scheduler(self.id_fetch)
            # This part isn't fast, but it doesn't matter, since it just inits everything, optimizing here doesn't
            # matter as it is only called once AND every element has to be initted.
            for d in cDEVS.componentSet:
                if not isinstance(d, RemoteCDEVS):
                    self.send(d.model_id, msg)
                    cDEVS.timeNext = min(cDEVS.timeNext, d.timeNext)
                    cDEVS.timeLast = max(cDEVS.timeLast, d.timeLast)
                    self.id_fetch[d.model_id][0] = d.timeNext
                    cDEVS.scheduler.schedule(d)
        else:
            # messagetype 1 is not defined as this is done directly at the basesimulator
            raise DEVSException("Unrecognized message on coupled model '" + \
                                cDEVS.getModelFullName() + "'")

    def setID_fetch(self, dct):
        self.id_fetch = dct
