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

# Import code for model simulation, but using the minimal kernel:
from pypdevs.minimal import Simulator

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

# 3. Perform all necessary configurations, with the minimal kernel, only setTerminationTime is supported.
#    e.g. to simulate until simulation time 400.0 is reached
sim.setTerminationTime(400.0)

#    ======================================================================

# 4. Simulate the model
sim.simulate()

#    ======================================================================

# 5. (optional) Extract data from the simulated model
print(("Simulation terminated with traffic light in state %s" % (trafficSystem.trafficLight.state.get())))
