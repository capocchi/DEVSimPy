#!/bin/env python
import sys
sys.path.append("../../src/")

import time

sys.setrecursionlimit(10000)

iters = int(sys.argv[1])
nrmodels = list(range(10, 150, 10))

nodes = 100
import subprocess

output = open('/tmp/output', 'w')
for statesaving in ["custom", "deepcopy", "pickleH"]:
    f = open("dist_statesaving/result_" + str(statesaving), 'w')
    for models in nrmodels:
        total = 0.0
        for _ in range(iters):
            command = "mpirun -np 3 python dist_statesaving/experiment.py %i %s" % (models, statesaving)
            start = time.time()
            subprocess.check_output(command, shell=True, stderr=output)
            total += (time.time() - start)
        f.write("%i %s\n" % (models, total/iters))
        print(("%i %s" % (models, total/iters)))
    f.close()
