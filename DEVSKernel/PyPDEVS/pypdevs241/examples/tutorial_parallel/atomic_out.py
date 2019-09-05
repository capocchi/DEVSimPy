### Model
from pypdevs.DEVS import *

class TrafficLightWithOutput(AtomicDEVS):
	def __init__(self):
		AtomicDEVS.__init__(self, "Light")
		self.state = "green"
		self.observe = self.addOutPort("observer")

	def intTransition(self):
		state = self.state
		return {"red": "green",
			"yellow": "red",
			"green": "yellow"}[state]

	def timeAdvance(self):
		state = self.state
		return {"red": 60,
			"yellow": 3,
			"green": 57}[state]

	def outputFnc(self):
		state = self.state
		if state == "red":
			v = "green"
		elif state == "yellow":
			v = "red"
		elif state == "green":
			v = "yellow"
		return {self.observe: [v]}

### Experiment
from pypdevs.simulator import Simulator

model = TrafficLightWithOutput()
sim = Simulator(model)

sim.setVerbose()
sim.setTerminationTime(500)

sim.simulate()