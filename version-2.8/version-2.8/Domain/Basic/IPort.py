# -*- coding: utf-8 -*-

"""
Name : IPort.py
Brief description : Basic DEVS input port
Authors : Laurent CAPOCCHI
Version : 1.0
Last modified : 12/02/10
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS
"""

from DEVSKernel.PyDEVS.DEVS import Port

class IPort(Port):
	def __init__(self):
		Port.__init__(self)
		self.name="IN"+str(self.myID)
	def type(self):
		return "INPORT"