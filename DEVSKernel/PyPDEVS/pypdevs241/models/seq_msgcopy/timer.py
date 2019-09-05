import sys
import random
sys.path.append("../../src/")
sizes = list(range(10, 200, 10))
from simulator import Simulator
import time
iters = int(sys.argv[1])

def runFunc(param):
        f = open("seq_msgcopy/%s" % (param), 'w')
        for size in sizes:
            from model import DEVStone
            total = 0.0
            for _ in range(iters):
                random.seed(1)
                model = DEVStone(3, size, False)
                sim = Simulator(model)
                sim.setMessageCopy(param)
                sim.setSchedulerHeapSet()
                sim.setTerminationTime(1000)
                start = time.time()
                sim.simulate()
                total += (time.time() - start)
            f.write("%s %s\n" % (size, total/iters))
            print(("%s %s" % (size, total/iters)))
        f.close()

allprocs = []
for msgcopy in ['none', 'pickle', 'custom']:
    allprocs.append(msgcopy)

list(map(runFunc, allprocs))
"""
from multiprocessing import Pool
p = Pool(3)
p.map(runFunc, allprocs)
"""
