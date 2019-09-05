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
                "green": "yellow",
                "going_manual": "manual",
                "going_auto": "red"}[state]

    def timeAdvance(self):
        state = self.state
        return {"red": 60,
                "yellow": 3,
                "green": 57,
                "manual": INFINITY,
                "going_manual": 0,
                "going_auto": 0}[state]

    def outputFnc(self):
        state = self.state
        if state == "red":
            return {self.observe: "show_green"}
        elif state == "yellow":
            return {self.observe: "show_red"}
        elif state == "green":
            return {self.observe: "show_yellow"}
        elif state == "going_manual":
            return {self.observe: "turn_off"}
        elif state == "going_auto":
            return {self.observe: "show_red"}

    def extTransition(self, inputs):
        inp = inputs[self.interrupt]
        if inp == "toManual":
            return "going_manual"
        elif inp == "toAuto":
            if self.state == "manual":
                return "going_auto"
