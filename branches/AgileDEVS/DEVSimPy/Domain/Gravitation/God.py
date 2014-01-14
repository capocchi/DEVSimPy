# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:          <God.py>
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
from Domain.Gravitation import astroLib

### Model class ---------------------------------------------------------------
class God(DomainBehavior):
	''' DEVS Class for Massive_Object model
	'''
	
	def __init__(self, dt=0.1):
		''' Constructor.
			Distance : mètre
			Masse: kilogramme
			Temps: seconde
			Force: newton ou m.kg.(math.pow(s, -2))
		'''
		DomainBehavior.__init__(self)

		self.setState("TIRED", INFINITY)
		#self.msg = Message()

		self.mass_objects = dict()
		# self.positions = dict()
		self.dt = dt
		self.numPorts = dict()
		
	def extTransition(self):
		''' DEVS external transition function.
		'''
		for i in xrange(len(self.IPorts)):
			msg = self.peek(self.IPorts[i])
			if msg:
				#self.msg = msg
				name = msg.value[0]
				data = msg.value[1]
				self.numPorts[name] = i
				if not name in self.mass_objects.keys():
					self.mass_objects[name] = data
		if len(self.mass_objects.keys()) == len(self.IPorts):
			### Calcul
			for name in self.mass_objects.keys():
				self.mass_objects[name] = astroLib.compute(name, self.mass_objects, self.dt)
			self.setState("WORKING", 0)

	
	def outputFnc(self):
		''' DEVS output function.
		'''
		for name in self.numPorts.keys():
			msg = Message()
			current = self.mass_objects[name]
			data = {"x": current["x"], "y": current["y"], "vx": current["vx"], "vy": current["vy"], "ax": current["ax"], "ay": current["ay"], "rayon": current["rayon"]}
			msg.value = [data, 0., 0.]
			msg.time = self.timeNext
			self.poke(self.OPorts[self.numPorts[name]], msg)
		self.mass_objects = dict()


	def intTransition(self):
		''' DEVS internal transition function.
		'''
		self.state["sigma"] = INFINITY
	
	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.state['sigma']

	def setState(self, status, sigma):
		self.state = {"state": status.upper(), "sigma": sigma}

