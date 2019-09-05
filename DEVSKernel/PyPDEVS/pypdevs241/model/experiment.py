import sys
sys.path.append("../src")
from simulator import Simulator
from model import Cluster

#import stacktracer
#stacktracer.trace_start("trace.html",interval=5,auto=True) # Set auto flag to always update file!

model = Cluster(2)

sim = Simulator(model)
sim.setVerbose(None)
#sim.setTerminationTime(10.0)
sim.setStateSaving("custom")
sim.simulate()
