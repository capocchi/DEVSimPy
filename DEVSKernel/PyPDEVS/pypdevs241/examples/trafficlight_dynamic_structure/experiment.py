# Copyright 2014 Modelling, Simulation and Design Lab (MSDL) at 
# McGill University and the University of Antwerp (http://msdl.cs.mcgill.ca/)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Import code for model simulation:
from pypdevs.simulator import Simulator

# Import the model to be simulated
from model import TrafficSystem

#    ======================================================================

# 1. Instantiate the (Coupled or Atomic) DEVS at the root of the 
#  hierarchical model. This effectively instantiates the whole model 
#  thanks to the recursion in the DEVS model constructors (__init__).
#
trafficSystem = TrafficSystem(name="trafficSystem")

#    ======================================================================

# 2. Link the model to a DEVS Simulator: 
#  i.e., create an instance of the 'Simulator' class,
#  using the model as a parameter.
sim = Simulator(trafficSystem)

#    ======================================================================

# 3. Perform all necessary configurations, the most commonly used are:

# A. Termination time (or termination condition)
#    Using a termination condition will execute a provided function at
#    every simulation step, making it possible to check for certain states
#    being reached.
#    It should return True to stop simulation, or Falso to continue.
def terminate_whenStateIsReached(clock, model):
    return model.trafficLight.state.get() == "manual"
sim.setTerminationCondition(terminate_whenStateIsReached)

#    A termination time is prefered over a termination condition,
#    as it is much simpler to use.
#    e.g. to simulate until simulation time 400.0 is reached
sim.setTerminationTime(500.0)

# B. Set the use of a tracer to show what happened during the simulation run
#    Both writing to stdout or file is possible:
#    pass None for stdout, or a filename for writing to that file
sim.setVerbose(None)

# C. Set the use of Dynamic Structure DEVS, to make sure that the modelTransition
#    methods are invoked and changes are performed correctly.
sim.setDSDEVS(True)

#    ======================================================================

# 4. Simulate the model
sim.simulate()

#    ======================================================================

# 5. (optional) Extract data from the simulated model
print(("Simulation terminated with traffic light 1 in state %s" % (trafficSystem.trafficLight1.state.get())))
print(("Simulation terminated with traffic light 2 in state %s" % (trafficSystem.trafficLight2.state.get())))
