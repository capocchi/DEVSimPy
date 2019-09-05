import sys
import random
schedulers = ["setSchedulerSortedList", "setSchedulerActivityHeap", "setSchedulerMinimalList", "setSchedulerHeapSet", "setSchedulerPolymorphic"]
sys.path.append("../../src/")
sizes = list(range(10, 200, 10))
from simulator import Simulator
import time
iters = int(sys.argv[1])

def runFunc(param):
        scheduler, randomta = param
        f = open("seq_devstone/%s_%s" % (scheduler, randomta), 'w')
        for size in sizes:
            from model import DEVStone
            total = 0.0
            for _ in range(iters):
                random.seed(1)
                model = DEVStone(3, size, randomta)
                sim = Simulator(model)
                sim.setMessageCopy('none')
                getattr(sim, scheduler)()
                sim.setTerminationTime(1000)
                start = time.time()
                sim.simulate()
                total += (time.time() - start)
            f.write("%s %s\n" % (size, total/iters))
            print(("%s %s" % (size, total/iters)))
        f.close()

allprocs = []
for scheduler in schedulers:
    for randomta in [True, False]:
        allprocs.append([scheduler, randomta])

list(map(runFunc, allprocs))
"""
from multiprocessing import Pool
p = Pool(3)
p.map(runFunc, allprocs)
"""
