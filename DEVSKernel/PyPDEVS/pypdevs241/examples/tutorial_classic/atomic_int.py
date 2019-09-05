### Model
from pypdevs.DEVS import *

class TrafficLightAutonomous(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "Light")
        self.state = "green"
        self.elapsed = 0.0

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

### Experiment
from pypdevs.simulator import Simulator

model = TrafficLightAutonomous()
sim = Simulator(model)

sim.setVerbose()
sim.setTerminationTime(500)
sim.setClassicDEVS()

sim.simulate()
