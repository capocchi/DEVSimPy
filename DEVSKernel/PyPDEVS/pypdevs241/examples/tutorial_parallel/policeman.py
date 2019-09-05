from pypdevs.DEVS import *

class Policeman(AtomicDEVS):
	def __init__(self):
		AtomicDEVS.__init__(self, "policeman")
		self.out = self.addOutPort("output")
		self.state = "idle"

	def intTransition(self):
		if self.state == "idle":
			return "working"
		elif self.state == "working":
			return "idle"

	def timeAdvance(self):
		if self.state == "idle":
			return 20
		elif self.state == "working":
			return 360

	def outputFnc(self):
		if self.state == "idle":
			return {self.out: ["manual"]}
		elif self.state == "working":
			return {self.out: ["auto"]}