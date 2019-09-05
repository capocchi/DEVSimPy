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

# Import code for DEVS model representation:
from pypdevs.infinity import *
from pypdevs.DEVS import *

#    ======================================================================    #

class TrafficLightMode:

  """Encapsulates the system's state
  """

  ###
  def __init__(self, current="red"):
    """Constructor (parameterizable).
    """
    self.set(current)

  def set(self, value="red"):
    self.__colour=value

  def get(self):
    return self.__colour

  def __str__(self):
    return self.get()

class TrafficLight(AtomicDEVS):
  """A traffic light 
  """
  
  ###
  def __init__(self, name=None):
    """Constructor (parameterizable).
    """
    
    # Always call parent class' constructor FIRST:
    AtomicDEVS.__init__(self, name)
    
    # STATE:
    #  Define 'state' attribute (initial sate):
    self.state = TrafficLightMode("red") 

    # PORTS:
    #  Declare as many input and output ports as desired
    #  (usually store returned references in local variables):
    self.INTERRUPT = self.addInPort(name="INTERRUPT")
    self.OBSERVED = self.addOutPort(name="OBSERVED")

  ###
  def extTransition(self, inputs):
    """External Transition Function."""
    
    # Compute the new state 'Snew' based (typically) on current
    # State, Elapsed time parameters and calls to 'self.peek(self.IN)'.
    #input = self.peek(self.INTERRUPT)
    input = inputs[self.INTERRUPT][0]

    state = self.state.get()

    if input == "toManual":
      if state == "manual":
       # staying in manual mode
       return TrafficLightMode("manual")
      if state in ("red", "green", "yellow"):
       return TrafficLightMode("manual")
      else:
       raise DEVSException(\
        "unknown state <%s> in TrafficLight external transition function"\
        % state)
    
    if input == "toAutonomous":
      if state == "manual":
        return TrafficLightMode("red")
      else:
       raise DEVSException(\
        "unknown state <%s> in TrafficLight external transition function"\
        % state) 

    raise DEVSException(\
      "unknown input <%s> in TrafficLight external transition function"\
      % input) 

  ###
  def intTransition(self):
    """Internal Transition Function.
    """

    state = self.state.get()

    if state == "red":
      return TrafficLightMode("green")
    elif state == "green":
      return TrafficLightMode("yellow")
    elif state == "yellow":
      return TrafficLightMode("red")
    else:
      raise DEVSException(\
        "unknown state <%s> in TrafficLight internal transition function"\
        % state)
  
  ###
  def outputFnc(self):
    """Output Funtion.
    """
   
    # A colourblind observer sees "grey" instead of "red" or "green".
 
    # BEWARE: ouput is based on the OLD state
    # and is produced BEFORE making the transition.
    # We'll encode an "observation" of the state the
    # system will transition to !

    # Send messages (events) to a subset of the atomic-DEVS' 
    # output ports by means of the 'poke' method, i.e.:
    # The content of the messages is based (typically) on current State.
 
    state = self.state.get()

    if state == "red":
      return {self.OBSERVED: ["grey"]}
    elif state == "green":
      return {self.OBSERVED: ["yellow"]}
      # NOT return {self.OBSERVED: ["grey"]}
    elif state == "yellow":
      return {self.OBSERVED: ["grey"]}
      # NOT return {self.OBSERVED: ["yellow"]}
    else:
      raise DEVSException(\
        "unknown state <%s> in TrafficLight external transition function"\
        % state)
    
  ###
  def timeAdvance(self):
    """Time-Advance Function.
    """
    
    # Compute 'ta', the time to the next scheduled internal transition,
    # based (typically) on current State.
    
    state = self.state.get()

    if state == "red":
      return 3
    elif state == "green":
      return 2
    elif state == "yellow":
      return 1
    elif state == "manual":
      return INFINITY 
    else:
      raise DEVSException(\
        "unknown state <%s> in TrafficLight time advance transition function"\
        % state)

#    ======================================================================    #

class TrafficLightSystem(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "System")
        self.light = self.addSubModel(TrafficLight("Light"))
        self.observed = self.addOutPort(name="observed")
        self.connectPorts(self.light.OBSERVED, self.observed)

def my_function(event):
    print(("Observed the following event: " + str(event)))

from pypdevs.simulator import Simulator

model = TrafficLightSystem()
sim = Simulator(model)
sim.setRealTime()
sim.setListenPorts(model.observed, my_function)
sim.simulate()

import time
while 1:
    time.sleep(0.1)
