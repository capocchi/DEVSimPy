### Model
from pypdevs.DEVS import *

from trafficlight import TrafficLight
from policeman import Policeman

class TrafficLightSystem(CoupledDEVS):
	def __init__(self):
		CoupledDEVS.__init__(self, "system")
		self.light = self.addSubModel(TrafficLight())
		self.police = self.addSubModel(Policeman())
		self.connectPorts(self.police.out, self.light.interrupt)

### Experiment
from pypdevs.simulator import Simulator
sim = Simulator(TrafficLightSystem())
sim.setVerbose()
sim.setTerminationTime(1000)
sim.simulate()