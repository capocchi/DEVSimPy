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
from scipy.constants import codata
from Domain.Gravitation.singleton import Singleton

### Model class ---------------------------------------------------------------
class Massive_Object(DomainBehavior):
	''' DEVS Class for Massive_Object model
	'''
	
	def __init__(self, bulk=1.9891*math.pow(10, 30), rayon=696342., vx=108.5, vy=108.5, x=0, y=0, dt=0.1):
		''' Constructor.
			Distance : mètre
			Masse: kilogramme
			Temps: seconde
			Force: newton ou m.kg.(math.pow(s, -2))
		'''
		DomainBehavior.__init__(self)

		### Solar initialization
		if not bulk: bulk = 1.9891*math.pow(10, 30)		# kg
		
		self.state = {'status': 'FREE', 'sigma':0}
		self.bulk = bulk																# kg
		self.rayon = rayon																# km
		self.vx = float(vx)																# km/s
		self.vy = float(vy)																# km/s
		self.volume = (4/3)*math.pi*math.pow(self.rayon, 3)								# math.pow(km, 3)
		self.dt = dt
		self.x = x
		self.y = y
		self.flag = False

		self.vxt = 0
		self.vyt = 0

		self.count = []

		self.isPrimary = False

		self.god = Singleton()
		self.god.instanceNum += 1

		self.initFlag = True
		self.msg = Message()
		
	def extTransition(self):
		''' DEVS external transition function.
		'''
		if self.count == []:
			[self.count.append(False) for i in xrange(len(self.IPorts))]
		for i in xrange(len(self.IPorts)):
			msg = self.peek(self.IPorts[i])
			### Si le message n'est pas nul et si le port n'a pas encore recu son message
			if msg and self.count[i] == False:
				M = msg.value[0]
				x = msg.value[1]
				y = msg.value[2]
				self.speed_vectors(M, x, y)
				self.count[i] = True
		### Si le modèle a recu un message sur chaque ports
		if False not in self.count:
			self.flag = True
	
	def outputFnc(self):
		''' DEVS output function.
		'''
		### Si ce modèle est le premier à s'activer
		# if self.isPrimary and not self.flag:
		# 	### Send directly once
		# 	self.msg.value = [self.bulk, self.x, self.y]
		# 	self.msg.time = self.timeNext
		# 	self.poke(self.OPorts[0], self.msg)
		if self.isPrimary and self.flag:
			### Send nothing
			self.position_computing()
			self.reset_vectors()
		# elif not self.isPrimary:
		# 	### Send old position once
		# 	self.msg.value = [self.bulk, self.x, self.y]
		# 	self.msg.time = self.timeNext
		# 	self.poke(self.OPorts[0], self.msg)
		self.msg.value = [self.bulk, self.x, self.y]
		self.msg.time = self.timeNext
		self.poke(self.OPorts[0], self.msg)

	def intTransition(self):
		''' DEVS internal transition function.
		'''
		# if self.initFlag:
		# 	[self.count.append(False) for i in xrange(len(self.IPorts))]
		# 	print self.count

		self.god.changePrimary(self)
		if self.god.primary == self:
			self.isPrimary = True
		else:
			self.isPrimary = False
		### Calcul de la nouvelle position
		# self.position_computing(self.flag)
		# ### Si on a recu tout les messages attendus
		# if self.flag:
		# 	# self.god.activations += 1
		# 	### Remise à zero des variables
		# 	self.reset_vectors()

		self.state["sigma"] = self.dt
	
	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.state['sigma']
		
	def finish(self, msg):
		''' Additional function which is lunched just before the end of the simulation.
		'''
		pass


	def get_distance(self, x, y):
		r = math.sqrt(math.pow(x - self.x, 2)) + math.sqrt(math.pow(y - self.y, 2))
		r = r * math.pow(10, 3) 
		return r

	# def gravitational_field(self, M, x, y):
	# 	G = codata.value('Newtonian constant of gravitation')
	# 	r = self.get_distance(x, y)
	# 	return G*M/math.pow(r, 2)

	def speed_vectors(self, M, x, y):
		G = codata.value('Newtonian constant of gravitation')

		if self.initFlag:
			dt_vit = self.dt / 2
		else:
			dt_vit = self.dt

		r3 = math.pow(self.get_distance(x, y), 3)

		ax = -G * M * self.x / (r3)
		ay = -G * M * self.y / (r3)

		self.vxt += ax * dt_vit
		self.vyt += ay * dt_vit

		self.initFlag = False

	def position_computing(self):
		self.vx += self.vxt
		self.vy += self.vyt
		self.x = self.x + self.vx * self.dt
		self.y = self.y + self.vy * self.dt

	def reset_vectors(self):
		self.count = []
		[self.count.append(False) for i in xrange(len(self.IPorts))]
		self.vxt = 0
		self.vyt = 0
		self.flag = False
