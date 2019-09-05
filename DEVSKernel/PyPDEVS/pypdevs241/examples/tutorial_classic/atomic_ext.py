### Model
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY

class TrafficLight(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "Light")
        self.state = "green"
        self.elapsed = 0.0
        self.observe = self.addOutPort("observer")
        self.interrupt = self.addInPort("interrupt")

    def intTransition(self):
        state = self.state
        return {"red": "green",
            "yellow": "red",
            "green": "yellow"}[state]

    def timeAdvance(self):
        state = self.state
        return {"red": 60,
            "yellow": 3,
            "green": 57,
            "manual": INFINITY}[state]

    def outputFnc(self):
        state = self.state
        if state == "red":
            return {self.observe: "show_green"}
        elif state == "yellow":
            return {self.observe: "show_red"}
        elif state == "green":
            return {self.observe: "show_yellow"}

    def extTransition(self, inputs):
        inp = inputs[self.interrupt]
        if inp == "manual":
            return "manual"
        elif inp == "auto":
            if self.state == "manual":
                return "red"

### Experiment
from pypdevs.simulator import Simulator

model = TrafficLight()
sim = Simulator(model)

sim.setVerbose()
sim.setTerminationTime(500)
sim.setClassicDEVS()

sim.simulate()
