#!/bin/env python
import sys
sys.path.append("../../src/")

import time

sys.setrecursionlimit(10000)

tests = ["AT", "CACR", "NO", "CA"]
loads = list(range(5000, 45000, 5000))

iters = int(sys.argv[1])

for relocator in tests:
    f = open("dist_activity_citylayout/results_%s" % relocator, 'w')
    for load in loads:
        total = 0.0
        for _ in range(iters):
            command = "mpirun -np 3 python dist_activity_citylayout/test_city_%s.py %s" % (relocator, load)
            output = open("/tmp/output", 'w')
            import subprocess
            start = time.time()
            subprocess.call(command, shell=True, stdout=output)
            output.close()
            total += (time.time() - start)
        f.write("%s %s\n" % (load, total/iters))
        print(("%s %s" % (load, total/iters)))
    f.close()
