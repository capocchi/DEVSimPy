import model
import logging

import sys
sys.path.append('../../src/')
from simulator import Simulator

sys.setrecursionlimit(50000)
model = model.AutoDistPHOLD(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
sim = Simulator(model)
#sim.setVerbose(None)
sim.setTerminationTime(200)
sim.setMessageCopy('custom')
sim.setStateSaving("custom")
sim.setMemoization(True)
sim.setGVTInterval(5)
#sim.setGVTInterval(30)
#sim.setShowProgress()
sim.simulate()
