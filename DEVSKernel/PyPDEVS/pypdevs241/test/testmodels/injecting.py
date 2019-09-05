from pypdevs.DEVS import AtomicDEVS, CoupledDEVS
from pypdevs.simulator import Simulator

class Root(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Root")
        self.listener_A = self.addInPort("listener_A")
        self.output_A = self.addOutPort("output_A")
        self.mini = self.addSubModel(Mini())

        self.connectPorts(self.listener_A, self.mini.listener_B)
        self.connectPorts(self.mini.output_B, self.output_A)

class Mini(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Mini")
        self.listener_B = self.addInPort("listener_B")
        self.output_B = self.addOutPort("output_B")
        self.model_one = self.addSubModel(Proc("C"))
        self.model_two = self.addSubModel(Proc("D"))

        self.connectPorts(self.listener_B, self.model_one.inport)
        self.connectPorts(self.listener_B, self.model_two.inport)
        self.connectPorts(self.model_one.outport, self.output_B)

class Proc(AtomicDEVS):
    def __init__(self, name):
        AtomicDEVS.__init__(self, "Proc_%s" % name)
        self.inport = self.addInPort("listener_%s" % name)
        self.outport = self.addOutPort("output_%s" % name)
        self.state = None

    def intTransition(self):
        return None

    def extTransition(self, inputs):
        return inputs[self.inport][0]

    def outputFnc(self):
        return {self.outport: [self.state]}

    def timeAdvance(self):
        return 0.0 if self.state else float('inf')

model = Root()
sim = Simulator(model)
sim.setRealTime(True)
sim.setRealTimePorts({"input_A": model.listener_A,
                      "input_B": model.mini.listener_B,
                      "input_C": model.mini.model_one.inport,
                      "input_D": model.mini.model_two.inport,
                      "output_A": model.output_A,
                      "output_B": model.mini.output_B,
                      "output_C": model.mini.model_one.outport,
                      "output_D": model.mini.model_two.outport})
sim.setRealTimePlatformThreads()

def output_on_A(evt):
    global on_A
    on_A = evt[0]

def output_on_B(evt):
    global on_B
    on_B = evt[0]

sim.setListenPorts(model.output_A, output_on_A)
sim.setListenPorts(model.mini.output_B, output_on_B)

sim.simulate()

import time

on_A = None
on_B = None
sim.realtime_interrupt("input_A 1")
time.sleep(1)

if not (on_A == "1" and on_B == "1"):
    raise Exception("Expected input on A or B output port")
on_A = None
on_B = None

sim.realtime_interrupt("input_B 2")
time.sleep(1)

if not (on_A == "2" and on_B == "2"):
    print(on_A)
    print((type(on_A)))
    print(on_B)
    print((type(on_B)))
    raise Exception("Expected input on A and B output port")
on_A = None
on_B = None

sim.realtime_interrupt("input_C 3")
time.sleep(1)

if not (on_A == "3" and on_B == "3"):
    print(on_A)
    print(on_B)
    raise Exception("Expected input on A or B output port")
on_A = None
on_B = None

sim.realtime_interrupt("input_D 4")
time.sleep(1)

if not (on_A == None and on_B == None):
    raise Exception("Didn't expect input on A or B output port")
