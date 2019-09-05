import sys
import random
schedulers = ["setSchedulerHeapSet", "setSchedulerMinimalList", "setSchedulerPolymorphic"]
maxsize = 200
factors = list(range(1, 50))
sys.path.append("../../src/")
from simulator import Simulator
import time
iters = int(sys.argv[1])

def runFunc(scheduler):
  f = open("seq_poly/" + str(scheduler), 'w')
  for factor in factors:
    from model import StaticModel
    total = 0.0
    for _ in range(iters):
        random.seed(1)
        model = StaticModel(maxsize, factor)
        sim = Simulator(model)
        sim.setMessageCopy('none')
        getattr(sim, scheduler)()
        sim.setTerminationTime(1000)
        start = time.time()
        sim.simulate()
        del sim
        total += (time.time() - start)
    f.write("%s %s\n" % (factor, total/iters))
    print(("%s %s" % (factor, total/iters)))
  f.close()

def runFunc_DYN(scheduler):
    iters = 1
    f = open("seq_poly/%s_dynamic" % scheduler, 'w')
    from model import DynamicModel
    random.seed(1)
    model = DynamicModel(maxsize)
    sim = Simulator(model)
    sim.setMessageCopy('none')
    getattr(sim, scheduler)()
    termtime = 0
    while termtime < 10000:
        termtime += 1000
        sim.setTerminationTime(termtime)
        start = time.time()
        sim.simulate()
        f.write("%s %s\n" % (termtime - 1000, time.time() - start))
        print(("%s %s" % (termtime - 1000, time.time() - start)))
    del sim
    f.close()

list(map(runFunc, schedulers))
#map(runFunc_DYN, schedulers)
"""
from multiprocessing import Pool
p = Pool(3)
p.map(runFunc, schedulers)
p = Pool(3)
p.map(runFunc_DYN, schedulers)
"""
