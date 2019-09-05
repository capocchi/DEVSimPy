# Copyright 2015 Modelling, Simulation and Design Lab (MSDL) at 
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
The minimal PythonPDEVS simulation kernel. It only supports simple Parallel DEVS simulation, without any fancy configuration options.
While it behaves exactly the same as the normal simulation kernel with default options, it is a lot faster due to skipping all features.
"""

from collections import defaultdict

# Uncomment this part to make a completely stand-alone simulation kernel
class BaseDEVS(object):
    def __init__(self, name):
        self.name = name
        self.IPorts = []
        self.OPorts = []
        self.ports = []
        self.parent = None
        self.time_last = (0.0, 0)
        self.time_next = (0.0, 1)
        self.my_input = {}

    def addPort(self, name, is_input):
        name = name if name is not None else "port%s" % len(self.ports)
        port = Port(is_input=is_input, name=name)
        if is_input:
            self.IPorts.append(port)
        else:
            self.OPorts.append(port)
        port.port_id = len(self.ports)
        self.ports.append(port)
        port.host_DEVS = self
        return port

    def addInPort(self, name=None):
        return self.addPort(name, True)

    def addOutPort(self, name=None):
        return self.addPort(name, False)

    def getModelName(self):
        return self.name

    def getModelFullName(self):
        return self.full_name

class AtomicDEVS(BaseDEVS):
    ID = 0

    def __init__(self, name):
        BaseDEVS.__init__(self, name)
        self.elapsed = 0.0
        self.state = None
        self.model_id = AtomicDEVS.ID
        AtomicDEVS.ID += 1

    def extTransition(self, inputs):
        return self.state

    def intTransition(self):
        return self.state

    def confTransition(self, inputs):
        self.state = self.intTransition()
        return self.extTransition(inputs)

    def timeAdvance(self):
        return float('inf')

    def outputFnc(self):
        return {}

class CoupledDEVS(BaseDEVS):
    def __init__(self, name):
        BaseDEVS.__init__(self, name)
        self.component_set = []

    def addSubModel(self, model):
        model.parent = self
        self.component_set.append(model)
        return model

    def connectPorts(self, p1, p2):
        p1.outline.append(p2)
        p2.inline.append(p1)

class RootDEVS(object):
    def __init__(self, components):
        from .schedulers.schedulerAuto import SchedulerAuto as Scheduler
        self.component_set = components
        self.time_next = float('inf')
        self.scheduler = Scheduler(self.component_set, 1e-6, len(self.component_set))

class Port(object):
    def __init__(self, is_input, name=None):
        self.inline = []
        self.outline = []
        self.host_DEVS = None
        self.name = name

    def getPortname(self):
        return self.name

def directConnect(component_set):
    """
    Perform a trimmed down version of the direct connection algorithm.

    It does not support transfer functions, but all the rest is the same.

    :param component_set: the iterable to direct connect
    :returns: the direct connected component_set
    """
    new_list = []
    for i in component_set:
        if isinstance(i, CoupledDEVS):
            component_set.extend(i.component_set)
        else:
            # Found an atomic model
            new_list.append(i)
    component_set = new_list

    # All and only all atomic models are now direct children of this model
    for i in component_set:
        # Remap the output ports
        for outport in i.OPorts:
            # The new contents of the line
            outport.routing_outline = set()
            worklist = list(outport.outline)
            for outline in worklist:
                # If it is a coupled model, we must expand this model
                if isinstance(outline.host_DEVS, CoupledDEVS):
                    worklist.extend(outline.outline)
                else:
                    outport.routing_outline.add(outline)
            outport.routing_outline = list(outport.routing_outline)
    return component_set

class Simulator(object):
    """
    Minimal simulation kernel, offering only setTerminationTime and simulate.
    
    Use this Simulator instead of the normal one to use the minimal kernel.
    While it has a lot less features, its performance is much higher.
    The polymorphic scheduler is also used by default.
    """
    def __init__(self, model):
        """
        Constructor

        :param model: the model to simulate
        """
        self.original_model = model
        if isinstance(model, CoupledDEVS):
            component_set = directConnect(model.component_set)
            ids = 0
            for m in component_set:
                m.time_last = (-m.elapsed, 0)
                m.time_next = (-m.elapsed + m.timeAdvance(), 1)
                m.model_id = ids
                ids += 1
            self.model = RootDEVS(component_set)
        elif isinstance(model, AtomicDEVS):
            for p in model.OPorts:
                p.routing_outline = []
            model.time_last = (-model.elapsed, 0)
            model.time_next = (model.time_last[0] + model.timeAdvance(), 1)
            model.model_id = 0
            self.model = RootDEVS([model])
        self.setTerminationTime(float('inf'))

    def setTerminationTime(self, time):
        """
        Set the termination time of the simulation.

        :param time: simulation time at which simulation should terminate
        """
        self.setTerminationCondition(lambda t, m: time <= t[0])

    def setTerminationCondition(self, function):
        """
        Set the termination condition of the simulation.

        :param function: termination condition to execute, taking the current simulated time and the model, returning a boolean (True to terminate)
        """
        self.termination_function = function

    def simulate(self):
        """
        Perform the simulation
        """
        scheduler = self.model.scheduler
        tn = scheduler.readFirst()
        while not self.termination_function(tn, self.original_model):
            # Generate outputs
            transitioning = defaultdict(int)
            for c in scheduler.getImminent(tn):
                transitioning[c] |= 1
                outbag = c.outputFnc()
                for outport in outbag:
                    p = outbag[outport]
                    for inport in outport.routing_outline:
                        inport.host_DEVS.my_input.setdefault(inport, []).extend(p)
                        transitioning[inport.host_DEVS] |= 2

            # Perform transitions
            for aDEVS, ttype in transitioning.items():
                if ttype == 1:
                    aDEVS.state = aDEVS.intTransition()
                elif ttype == 2:
                    aDEVS.elapsed = tn[0] - aDEVS.time_last[0]
                    aDEVS.state = aDEVS.extTransition(aDEVS.my_input)
                elif ttype == 3:
                    aDEVS.elapsed = 0.
                    aDEVS.state = aDEVS.confTransition(aDEVS.my_input)
                aDEVS.time_next = (tn[0] + aDEVS.timeAdvance(), 1 if tn[0] > aDEVS.time_last[0] else tn[1] + 1)
                aDEVS.time_last = tn
                aDEVS.my_input = {}

            # Do reschedules
            scheduler.massReschedule(transitioning)
            tn = scheduler.readFirst()
        return tn[0]

    def __getattr__(self, attr):
        """
        Wrapper to inform users that they are using the minimal kernel if they zant to do some unsupported configuration option.
        """
        if attr.startswith("set"):
            raise Exception("You are using the minimal simulation kernel, which does not support any configuration except for the termination time. Please switch to the normal simulation kernel to use this option.")
        else:
            raise AttributeError()
