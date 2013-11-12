# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        waterPowerStation.py

 Model:       waterPowerStation Model
 Author:       Bastien POGGI (bpoggi@univ-corse.fr)

 Created:     2010.10.10
-------------------------------------------------------------------------------
"""

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

class waterPowerStation(DomainBehavior):
	"""
	This class model a water power station that product electricity
	"""

	def __init__(self, powerPerFlow=0.20, flow=0, levelWaterFall=1.0):

		DomainBehavior.__init__(self)

		self.state = {  'status': 'OFF',
						'sigma' : INFINITY,
						'power' : powerPerFlow,
						'flow' : flow,
						'levelWaterFall' : levelWaterFall
						}

		self.msg = None
		
	def extTransition(self):
		
		self.msg = self.peek(self.IPorts[0])
		
		self.state['flow'] = float(self.msg.value[0])
		
		self.debugger("%f"%self.state['flow'])
		
		self.state['status'] = "ON"
		self.state['sigma'] = 0

	def outputFnc(self):
		assert(self.msg != None)
		
	#		MegaWatt = self.returnPowerWithFlow(self.state['flow'])
		self.msg.time = self.timeNext
		self.msg.value[0] = self.returnPowerBrut(self.state['flow'], self.state['levelWaterFall'])
		self.poke(self.OPorts[0], self.msg)

	def intTransition(self):
		self.state['status'] = "OFF"
		self.state['sigma'] = INFINITY

	def timeAdvance(self):
		return self.state['sigma']

	def __str__(self):
		return "waterPowerStation"

	#Internal Function
	def returnPowerWithFlow(self,flow):
		"""
		This function convert a flow in mWH
		"""
		return flow * self.state['power']

	def returnPowerBrut(self,flow,levelWaterFall,G=9.81):
		"""
		@param flow : liter/second
		@param level : the level of the waterfall
		@param G : m/s2
		@return : the power in KW
		"""
		return flow * G * levelWaterFall

	def returnPowerNet(self):
		pass