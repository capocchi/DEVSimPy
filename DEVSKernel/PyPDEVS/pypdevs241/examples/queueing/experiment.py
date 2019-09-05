from pypdevs.simulator import Simulator
import random

# Import the model we experiment with
from system import QueueSystem

# Configuration:
# 1) number of customers to simulate
num = 500
# 2) average time between two customers
time = 30.0
# 3) average size of customer
size = 20.0
# 4) efficiency of processors (products/second)
speed = 0.5
# 5) maximum number of processors used
max_processors = 10
# End of configuration

# Store all results for output to file
values = []
# Loop over different configurations
for i in range(1, max_processors):
    # Make sure each of them simulates exactly the same workload
    random.seed(1)
    # Set up the system
    procs = [speed] * i
    m = QueueSystem(mu=1.0/time, size=size, num=num, procs=procs)

    # PythonPDEVS specific setup and configuration
    sim = Simulator(m)
    sim.setClassicDEVS()
    sim.simulate()

    # Gather information for output
    evt_list = m.collector.state.events
    values.append([e.queueing_time for e in evt_list])

# Write data to file
with open('output.csv', 'w') as f:
    for i in range(num):
        f.write("%s" % i)
        for j in range(len(values)):
            f.write(", %5f" % (values[j][i]))
        f.write("\n")
