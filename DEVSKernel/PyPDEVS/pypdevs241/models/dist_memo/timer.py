#!/bin/env python
import sys
sys.path.append("../../src/")

import time

sys.setrecursionlimit(10000)

loads = list(range(10000, 100000, 5000))
iters = int(sys.argv[1])

import subprocess
output = open('/tmp/output', 'w')

for memo in [True, False]:
    f = open("dist_memo/result_%s" % (memo), 'w')
    for load in loads:
        val = str(load)
        for _ in range(iters):
            command = "mpirun -np 2 python dist_memo/model.py %i %s"
            command = (command % (load, memo))
            start = time.time()
            subprocess.check_output(command, shell=True, stderr=output)
            val += " %s" % (round(time.time() - start, 2))
        f.write("%s\n" % (val))
        print(val)
    f.close()
