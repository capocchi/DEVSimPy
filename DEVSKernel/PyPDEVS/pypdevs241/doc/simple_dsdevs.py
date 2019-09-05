from pypdevs.DEVS import AtomicDEVS, CoupledDEVS
from pypdevs.simulator import Simulator

class Root(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Root")
        self.models = []
        # First model
        self.models.append(self.addSubModel(Generator()))
        # Second model
        self.models.append(self.addSubModel(Consumer(0)))
        # And connect them
        self.connectPorts(self.models[0].outport, self.models[1].inport)

    def modelTransition(self, state):
        # We are notified, so are required to add a new model and link it
        self.models.append(self.addSubModel(Consumer(1)))
        self.connectPorts(self.models[0].outport, self.models[-1].inport)

        ## Optionally, we could also remove the Consumer(0) instance as follows:
        # self.removeSubModel(self.models[1])

        # Always returns False, as this is top-level
        return False

class Generator(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "Generator")
        # Keep a counter of how many events were sent
        self.outport = self.addOutPort("outport")
        self.state = 0

    def intTransition(self):
        # Increment counter
        return self.state + 1

    def outputFnc(self):
        # Send the amount of messages sent on the output port
        return {self.outport: [self.state]}

    def timeAdvance(self):
        # Fixed 1.0
        return 1.0

    def modelTransition(self, state):
        # Notify parent of structural change if state equals 3
        return self.state == 3

class Consumer(AtomicDEVS):
    def __init__(self, count):
        AtomicDEVS.__init__(self, "Consumer_%i" % count)
        self.inport = self.addInPort("inport")

    def extTransition(self, inputs):
        for inp in inputs[self.inport]:
            print(("Got input %i on model %s" % (inp, self.name)))

sim = Simulator(Root())
sim.setTerminationTime(5)
sim.setDSDEVS(True)
sim.simulate()
