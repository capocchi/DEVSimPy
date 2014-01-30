# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# trafficLightExperiment.py --- simple Traffic Light example experiment
#                       --------------------------------
#                              October 2005
#                             Hans Vangheluwe 
#                         McGill University (Montréal)
#                       --------------------------------
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

# Add the directory where pypdevs lives to Python's import path
import sys
import os.path
sys.path.append(os.path.expanduser('../src/'))

# Import code for model simulation:
from infinity import INFINITY
from simulator import *

#    ======================================================================

# Import the model to be simulated
from trafficLightModel import *

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

# 3. Run the simulator on the model until a termination_condition is met.
#  sim.simulate(termination_condition= ..., verbose= ...)
#

# Some typical termination_condition functions
#

# A. Simulate forever. 
#    The termination_condition function never returns True.
#
def terminate_never(model, clock):
  return False

#sim.simulate(termination_condition=terminate_never, 
#             verbose=True)

# B. Simulate until a specified end_time is reached.
#    When the end_time is reached/exceeded, the 
#    termination_condition function returns True.
#
def terminate_whenEndTimeReached(model, clock, end_time=999):
  if clock >= end_time:
    return True
  else:
    return False

#sim.simulate(termination_condition=terminate_whenEndTimeReached, 
#             verbose=True)

# C. Simulate until a specified end_state is reached.
#    When the end_state is reached, the 
#    termination_condition function returns True.
#
def terminate_whenStateIsReached(model, clock, end_state="manual"):
  trafficLight = model.getSubModel(name="trafficLight")
  if trafficLight.state.get() == end_state:
    return True
  else:
    return False

#sim.simulate(termination_condition=terminate_whenStateIsReached, 
#             verbose=True)

# D. Simulate until a specific time, faster alternative of B

sim.simulate(termination_time=999.0, 
             verbose=True)

#    ======================================================================
