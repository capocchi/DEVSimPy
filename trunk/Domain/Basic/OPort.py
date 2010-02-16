# -*- coding: utf-8 -*-

from DEVSKernel.DEVS import Port
	
class OPort(Port):
	def __init__(self):
		Port.__init__(self)
		self.name="OUT"+str(self.myID)	
	def type(self):
		return "OUTPORT"