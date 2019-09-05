import random
import sys
sys.path.append("../../../src/")
sys.path.append("../../src/")

from DEVS import AtomicDEVS, CoupledDEVS

class Node(AtomicDEVS):
    def __init__(self, nr, load):
        AtomicDEVS.__init__(self, "Node" + str(nr))
        self.state = None
        self.load = load

    def intTransition(self):
        for _ in range(self.load):
            pass
        return self.state

    def extTransition(self, inputs):
        return self.state

    def timeAdvance(self):
        return 1.0

    def outputFnc(self):
        return {}

class ExchangeModel(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "Exchange")
        self.state = None
        self.inport = self.addInPort("in")
        self.outport = self.addOutPort("out")

    def intTransition(self):
        return self.state

    def extTransition(self, inputs):
        return self.state

    def timeAdvance(self):
        return 1.0

    def outputFnc(self):
        return {self.outport: [None]}

class NodeGrid(CoupledDEVS):
    def __init__(self, load):
        CoupledDEVS.__init__(self, "Grid")
        for i in range(800):
            self.addSubModel(Node(i, load))

class DualGrid(CoupledDEVS):
    def __init__(self, load):
        CoupledDEVS.__init__(self, "Root")
        grid1 = self.addSubModel(NodeGrid(load), 0)
        grid2 = self.addSubModel(NodeGrid(load), 1)
        grid1_node = self.addSubModel(ExchangeModel(), 0)
        grid2_node = self.addSubModel(ExchangeModel(), 1)
        self.connectPorts(grid1_node.outport, grid2_node.inport)
        self.connectPorts(grid2_node.outport, grid1_node.inport)

if __name__ == "__main__":
    random.seed(1)
    from simulator import Simulator
    model = DualGrid(int(sys.argv[1]))
    sim = Simulator(model)
    sim.setTerminationTime(100)
    #sim.setVerbose(True)
    sim.setMessageCopy('none')
    sim.setStateSaving('assign')
    sim.setGVTInterval(5)
    memo = True if sys.argv[2] == "True" else False
    sim.setMemoization(memo)
    sim.setSchedulerSortedList()
    sim.simulate()
