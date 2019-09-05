#!/bin/env python
import sys
sys.path.append("../../src/")

import time

sys.setrecursionlimit(10000)

loads = list(range(5000, 30000, 1000))
termination_time = 200
iters = int(sys.argv[1])

import subprocess
output = open('/tmp/output', 'w')
for nodes, models in [(5, 150), (50, 900)]:
    for relocator in [True, False]:
        f = open("dist_activity_synthetic/result_%i_%s" % (nodes, relocator), 'w')
        for load in loads:
            f.write(str(load))
            for _ in range(iters):
                command = "mpirun -np %i -machinefile ~/machines python dist_activity_synthetic/movingcircle.py %i %i %i %s"
                command = (command % (nodes, models, load, termination_time, relocator))
                start = time.time()
                subprocess.check_output(command, shell=True, stderr=output)
                f.write(" %s" % (time.time() - start))
                print(("%i %s" % (load, time.time() - start)))
            f.write("\n")
        f.close()
    f = open("dist_activity_synthetic/result_%i_local" % nodes, 'w')
    for load in loads:
        f.write(str(load))
        for _ in range(iters):
            command = "python dist_activity_synthetic/movingcircle.py %i %i %i False"
            command = (command % (models, load, termination_time))
            start = time.time()
            subprocess.check_output(command, shell=True, stderr=output)
            f.write(" %s" % (time.time() - start))
            print(("%i %s" % (load, time.time() - start)))
        f.write("\n")
    f.close()

for relocator in [True, False]:
    load = 10000
    models = 1500
    termination_time = 200
    f = open("dist_activity_synthetic/result_nodes_%s" % relocator, 'w')
    for nodes in range(3, 50):
        for _ in range(iters):
            command = "mpirun -np %i -machinefile ~/machines python dist_activity_synthetic/movingcircle.py %i %i %i %s"
            command = (command % (nodes, models, load, termination_time, relocator))
            start = time.time()
            subprocess.check_output(command, shell=True, stderr=output)
            f.write(" %s" % (time.time() - start))
            print(("%i %s" % (nodes, time.time() - start)))
        f.write("\n")
        f.close()
    f = open("dist_activity_synthetic/result_nodes_local", 'w')
    f.write("1")
    for _ in range(iters):
        command = "python dist_activity_synthetic/movingcircle.py %i %i %i False"
        command = (command % (models, load, termination_time))
        start = time.time()
        subprocess.check_output(command, shell=True, stderr=output)
        f.write(" %s" % (time.time() - start))
        print(("1 %s" % (time.time() - start)))
    f.write("\n")
    f.close()

for relocator in [True, False]:
    try:
        import os
        os.remove("activity-log")
    except OSError:
        pass
    # Put the load rather high, to create a nice 'bad' distribution
    subprocess.check_output("mpirun -np 3 -machinefile ~/machines python dist_activity_synthetic/movingcircle.py 100 30000 400 " + str(relocator), shell=True, stderr=output)
    import shutil
    shutil.move("activity-log", "dist_activity_synthetic/activity-log_" + str("AT" if relocator else "NO"))
