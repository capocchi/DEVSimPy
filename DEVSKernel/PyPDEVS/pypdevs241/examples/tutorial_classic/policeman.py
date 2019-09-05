from pypdevs.DEVS import *

class Policeman(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "policeman")
        self.out = self.addOutPort("output")
        self.state = "idle"
        self.elapsed = 0.0

    def intTransition(self):
        if self.state == "idle":
            return "working"
        elif self.state == "working":
            return "idle"

    def timeAdvance(self):
        if self.state == "idle":
            return 300
        elif self.state == "working":
            return 3600

    def outputFnc(self):
        if self.state == "idle":
            return {self.out: "go_to_work"}
        elif self.state == "working":
            return {self.out: "take_break"}
