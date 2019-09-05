#! /bin/env python
import time
start = time.clock()
print(("Starting at time " + str(start)))
from mpi4py import MPI

import models
import sys
from pypdevs.simulator import Simulator, loadCheckpoint

model = models.AutoDistChain(3, totalAtomics=500, iterations=1)

sim = Simulator(model)
sim.setAllowLocalReinit(True)
sim.setTerminationTime(40)
sim.setVerbose("output/reinit1")
sim1start = time.clock()
print(("Sim 1 started at " + str(sim1start)))
sim.simulate()
sim.setReinitStateAttr(model.generator.generator, "value", 2)
sim2start = time.clock()
sim.setRemoveTracers()
sim.setVerbose("output/reinit2")
print(("Sim 2 started at " + str(sim2start)))
sim.simulate()
sim.setReinitStateAttr(model.generator.generator, "value", 3)
sim3start = time.clock()
print(("Sim 3 started at " + str(sim3start)))
sim.setRemoveTracers()
sim.setVerbose("output/reinit3")
sim.simulate()
sim3stop = time.clock()

print("Total runtimes: ")
print(("Init: " + str(sim1start - start)))
print(("Sim 1: " + str(sim2start - sim1start)))
print(("Sim 2: " + str(sim3start - sim2start)))
print(("Sim 3: " + str(sim3stop - sim3start)))
