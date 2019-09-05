import sys
import random
schedulers = ["sim.setSchedulerActivityHeap()", "sim.setSchedulerCustom('schedulerH', 'SchedulerH')"]
scheds = {0: "activityHeap", 1: "heap"}
actives = list(range(0, 1000, 10))
sys.setrecursionlimit(10000)
sys.path.append("../../src/")
from simulator import Simulator
import time
iters = max(int(sys.argv[1]), 20)

def runFunc(param):
    schedulername, scheduler = param
    f = open("seq_activity_synthetic/" + str(scheds[schedulername]), 'w')
    for active in actives:
        from model import StaticModel
        total = 0.0
        for _ in range(iters):
            random.seed(1)
            model = StaticModel(1000, active)
            sim = Simulator(model)
            sim.setMessageCopy('none')
            exec(scheduler)
            sim.setTerminationTime(100)
            start = time.time()
            sim.simulate()
            del sim
            total += (time.time() - start)
        f.write("%s %s\n" % (active, total/iters))
        print(("%s %s" % (active, total/iters)))
    f.close()

list(map(runFunc, enumerate(schedulers)))
"""
from multiprocessing import Pool
p = Pool(3)
p.map(runFunc, enumerate(schedulers))
"""
