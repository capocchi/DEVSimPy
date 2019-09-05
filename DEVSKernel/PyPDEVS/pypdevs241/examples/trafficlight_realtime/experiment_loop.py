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

from pypdevs.simulator import Simulator
from trafficLightModel import *
model = TrafficLight(name="trafficLight")

refs = {"INTERRUPT": model.INTERRUPT}
sim = Simulator(model)
sim.setRealTime(True)
sim.setRealTimeInputFile(None)
sim.setRealTimePorts(refs)
sim.setVerbose(None)
sim.setRealTimePlatformGameLoop()
sim.simulate()

import time
while 1:
    before = time.time()
    sim.realtime_loop_call()
    time.sleep(0.1 - (before - time.time()))
    print(("Current state: " + str(model.state.get())))
