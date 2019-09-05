import sys
import random
schedulers = ["setSchedulerSortedList", "setSchedulerActivityHeap", "setSchedulerMinimalList", "setSchedulerHeapSet"]
sys.path.append("../../src/")
sizes = list(range(10, 71, 1))
from simulator import Simulator
iters = max(int(sys.argv[1]), 20)
import time

def runFunc(scheduler):
    f = open("seq_activity_firespread/" + str(scheduler), 'w')
    for size in sizes:
        from model import FireSpread
        total = 0.0
        for _ in range(iters):
            model = FireSpread(size, size)
            sim = Simulator(model)
            sim.setMessageCopy('none')
            getattr(sim, scheduler)()
            sim.setTerminationTime(150)
            start = time.time()
            sim.simulate()
            total += (time.time() - start)
        # Take the square of size, as we have this many cells instead of only 'size' cells
        f.write("%s %s\n" % (size*size, total/iters))
        print(("%s -- %s %s" % (scheduler, size*size, total/iters)))
    f.close()

list(map(runFunc, schedulers))
"""
from multiprocessing import Pool
p = Pool(4)
p.map(runFunc, schedulers)
"""
