# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:          <Massive_Object.py>
 Model:         <describe model>
 Authors:       <Ville Timothée>
 Organization:  <Università di Corsica>
 Date:          <30-04-2013>
 License:       <Open Source>
-------------------------------------------------------------------------------
"""
	
### Specific import -----------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message
import math

### Model class ---------------------------------------------------------------
class Massive_Object(DomainBehavior):
	''' DEVS Class for Massive_Object model
	'''
	
	def __init__(self, bulk=5.972*math.pow(10, 24), rayon=6371000, ax=0, ay=0, vx=0, vy=0, x=1, y=1):
		''' Constructor.
			Distance : mètre
			Masse: kilogramme
			Temps: seconde
			Force: newton ou m.kg.(math.pow(s, -2))
		'''
		DomainBehavior.__init__(self)

		### Solar initialization
		if not bulk: bulk = 1.9891*math.pow(10, 30)		# kg
		
		self.state = {'status': 'UNDEF', 'sigma':0}

		# self.volume = (4/3)*math.pi*math.pow(self.rayon, 3)								# math.pow(km, 3)

		self.data = dict()

		self.data["M"] = bulk														# kg
		self.data["rayon"] = rayon													# km

		self.data["x"] = x
		self.data["y"] = y

		self.data["vx"] = float(vx)
		self.data["vy"] = float(vy)												# km/s

		self.data["ax"] = float(ax)
		self.data["ay"] = float(ay)												# km/s^2

		self.msg = Message()
		
	def extTransition(self):
		''' DEVS external transition function.
		'''
		for i in xrange(len(self.IPorts)):
			msg = self.peek(self.IPorts[i])
			### Si le message n'est pas nul et si le port n'a pas encore recu son message
			if msg:
				data = msg.value[0]
				self.data["x"] = data["x"]
				self.data["y"] = data["y"]
				self.data["vx"] = data["vx"]
				self.data["vy"] = data["vy"]
				self.data["ax"] = data["ax"]
				self.data["ay"] = data["ay"]

		self.state["sigma"] = 0
	
	def outputFnc(self):
		''' DEVS output function.
		'''
		self.msg.value = [self.blockModel.label, self.data, 0.]
		self.msg.time = self.timeNext
		self.poke(self.OPorts[0], self.msg)

	def intTransition(self):
		''' DEVS internal transition function.
		'''
		self.state["sigma"] = INFINITY
	
	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.state['sigma']
