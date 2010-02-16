# -*- coding: utf-8 -*-

from DEVSKernel.DEVS import Port

class IPort(Port):
	def __init__(self):
		Port.__init__(self)
		self.name="IN"+str(self.myID)	
	def type(self):
		return "INPORT"