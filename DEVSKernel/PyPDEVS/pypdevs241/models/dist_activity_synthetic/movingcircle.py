import random
import sys
sys.path.append("../../src/")

from DEVS import AtomicDEVS, CoupledDEVS

from mpi4py import MPI

class CircleNodeState(object):
    def __init__(self):
        self.event = None
        self.queue = []
        self.nr = 0
        self.generated = 0

    def copy(self):
        a = CircleNodeState()
        a.event = self.event
        a.queue = list(self.queue)
        a.nr = self.nr
        a.generated = self.generated
        return a

    def __hash__(self):
        return self.event + sum(self.queue)

    def __eq__(self, other):
        # For memoization
        if self.event == other.event and self.queue == other.queue and self.nr == other.nr and self.generated == other.generated:
            return True
        else:
            return False

    def __str__(self):
        return "%s (%s)" % (self.event, self.queue)

class CircleNode(AtomicDEVS):
    def __init__(self, nr, count, multiplier):
        AtomicDEVS.__init__(self, "CircleNode" + str(nr))
        self.inport = self.addInPort("input")
        self.outport = self.addOutPort("output")
        self.state = CircleNodeState()
        #self.state.event = random.randint(2, 100)
        self.state.nr = nr
        self.state.generated = 0
        self.state.event = nr
        self.count = count
        self.multiplier = multiplier

    def intTransition(self):
        if 0.6 * self.count < self.state.nr < 0.7 * self.count:
            for _ in range(self.state.nr*self.multiplier):
                pass
        if self.state.queue:
            self.state.event = self.state.queue.pop()
        else:
            self.state.event = None
        self.state.generated += 1
        if self.state.generated == 10:
            self.state.nr = (self.state.nr + 1) % self.count
            self.state.generated = 0
        return self.state

    def extTransition(self, inputs):
        if self.state.event is None:
            self.state.event = inputs[self.inport][0]
        else:
            self.state.queue.append(inputs[self.inport][0])
        return self.state

    def timeAdvance(self):
        if self.state.event is None:
            return float('inf')
        else:
            #return self.state.event
            return 1.0

    def outputFnc(self):
        return {self.outport: [self.state.event]}

class MovingCircle(CoupledDEVS):
    def __init__(self, count, multiplier):
        import math
        CoupledDEVS.__init__(self, "Circle")
        nodes = []
        try:
            from mpi4py import MPI
            pernode = float(count) / MPI.COMM_WORLD.Get_size()
        except ImportError:
            pernode = float(count)
        for i in range(count):
            nodes.append(self.addSubModel(CircleNode(i, count, multiplier), math.floor(i/pernode)))
        for index in range(len(nodes)):
            self.connectPorts(nodes[index-1].outport, nodes[index].inport)

if __name__ == "__main__":
    random.seed(1)
    from simulator import Simulator
    model = MovingCircle(int(sys.argv[1]), int(sys.argv[2]))
    sim = Simulator(model)
    sim.setTerminationTime(int(sys.argv[3]))
    #sim.setVerbose(True)
    sim.setMessageCopy('none')
    sim.setStateSaving('custom')
    sim.setGVTInterval(1 if int(argv[1]) < 500 else 5)
    from allocator import MyAllocator
    sim.setInitialAllocator(MyAllocator())
    #sim.setDrawModel(True, 'model.dot', True)
    if sys.argv[4] == "True":
        sim.setActivityRelocatorBasicBoundary(1.1)
    sim.setMemoization(True)
    sim.setSchedulerSortedList()
    #sim.setActivityTracking(True)
    #sim.setShowProgress()
    sim.simulate()
