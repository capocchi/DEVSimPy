### Model
from pypdevs.DEVS import *

from trafficlight import TrafficLight
from policeman import Policeman

def convert_police2light(evt):
    if evt == "take_break":
        return "toAuto"
    elif evt == "go_to_work":
        return "toManual"

class TrafficLightSystem(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "system")
        self.light = self.addSubModel(TrafficLight())
        self.police = self.addSubModel(Policeman())
        self.connectPorts(self.police.out, self.light.interrupt, convert_police2light)

    def select(self, imm):
        if self.police in imm:
            return self.police
        else:
            return self.light

### Experiment
from pypdevs.simulator import Simulator
sim = Simulator(TrafficLightSystem())
sim.setVerbose()
sim.setTerminationTime(1000)
sim.setClassicDEVS()
sim.simulate()
