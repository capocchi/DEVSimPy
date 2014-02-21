# Add the directory where pydevs lives to Python's import path
import sys
import os.path
sys.path.append(os.path.expanduser('../'))
from simulator import *

# Import code for model simulation:
from trafficLightModel import *

trafficSystem = TrafficSystem(name="trafficSystem")
sim = Simulator(trafficSystem)

refs = realTimeInputPortReferences = {"INTERRUPT":trafficSystem.trafficLight.INTERRUPT}

sim.simulate(termination_time=999, 
             realTimeInputPortReferences=refs,
             realtime=True,
             generatorfile="input",
             verbose=True,
             subsystem="python")
