import sys
sys.path.append("../../src/")
from DEVS import *

import random

class Generator(AtomicDEVS):
    def __init__(self, num, ta):
        AtomicDEVS.__init__(self, "Generator" + str(num))
        self.state = None
        self.ta = ta
    
    def timeAdvance(self):
        return self.ta

class StaticModel(CoupledDEVS):
    def __init__(self, size, actives):
        CoupledDEVS.__init__(self, "Root")
        random.seed(1)
        tas = [round(random.random(), 3) for _ in range(int(size/actives+1))]
        ta_counter = 0
        for i in range(size):
            self.addSubModel(Generator(i, tas[0]))
            if ta_counter >= actives:
                ta_counter = 0
                tas.pop(0)
            else:
                ta_counter += 1

class DynamicGenerator(AtomicDEVS):
    def __init__(self, num, nexttype):
        AtomicDEVS.__init__(self, "Generator" + str(num))
        self.state = (nexttype, True, round(random.uniform(4.00, 6.00), 4))
        self.nexttype = nexttype

    def intTransition(self):
        if self.state[0] - self.timeAdvance() <= 0:
            return (self.nexttype, not self.state[1], self.state[2])
        else:
            return (self.state[0] - self.timeAdvance(), self.state[1], self.state[2])
    
    def timeAdvance(self):
        if self.state[1]:
            return min(1.0, self.state[0])
        else:
            return min(self.state[2], self.state[0])

class DynamicModel(CoupledDEVS):
    def __init__(self, size):
        CoupledDEVS.__init__(self, "Root")
        random.seed(1)
        for i in range(size):
            self.addSubModel(DynamicGenerator(i, 2000))
