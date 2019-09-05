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

# Create a simulator with your model
model = Model()
sim = Simulator(model)

# Some of the most common options
# Enable verbose tracing
sim.setVerbose("output")

# End the simulation at simulation time 200
sim.setTerminationTime(200)
# Or use a termination condition to do the same
#def cond(model, time):
#    return time >= 200
#sim.setTerminationCondition(cond)

# If you want to reinit it later
sim.setAllowLocalReinit(True)

# Finally simulate it
sim.simulate()

# Now possibly use the altered model by accessing the model attributes

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!! Only possible in local simulation, distributed simulation requires !!!
# !!!           another configuration option to achieve this.            !!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# You might want to rerun the simulation (for whatever reason)
# Just call the simulate method again, all configuration from before will be
# used again. Altering configuration options is possible (to some extent)
sim.simulate()

# Or if you want to alter a specific attribute
sim.setReinitState(model.generator, GeneratorState())
sim.setReinitStateAttr(model.generator, "generated", 4)
sim.setReinitAttributes(model.generator, "delay", 1)

# Now run it again
sim.simulate()
