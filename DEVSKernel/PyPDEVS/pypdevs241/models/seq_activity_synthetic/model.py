import sys
sys.path.append("../../src/")
from DEVS import *


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
        ta_counter = 0
        for i in range(size):
            self.addSubModel(Generator(i, 1.0 if ta_counter < actives else float('inf')))
            ta_counter += 1
