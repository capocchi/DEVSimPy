# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        Rep2.py

 Model:       Rep2 Model
 Author:      L. Capocchi (capocchi@univ-corse.fr), J.F. Santucci (santucci@univ-corse.fr), C. Nicolai (cnicolai@univ-corse.fr)

 Created:     2011-05-25
-------------------------------------------------------------------------------
"""

from DomainInterface.DomainBehavior import DomainBehavior

#    ======================================================================    #
class Rep2(DomainBehavior):
	"""	Atomic model of Rep2 which drive the comsuption and the Figari dam depending on d1 ,d2, C1, C2 
	"""
	###
	def __init__(self):

            DomainBehavior.__init__(self)

            self.msgQ = None
            self.msgC2 = None
            self.d1 = None
            self.d2 = None
            
            self.state = { 'status':'IDLE', 'sigma': INFINITY }

	def extTransition(self):

		#Recuperation du numero de Q et C2
		msgQ, msgC2, d1, d2 = map(self.peek, self.IPorts)
		
		if msgQ != None:
			self.msgQ = msgQ
		
		if msgC2 != None:
			self.msgC2 = msgC2
		
		if d1 != None:
			self.d1 = d1
		
		if d2 != None:
			self.d2 = d2
		
		# changement d etat que lorsque Q et C2 sont different de None
		if self.msgQ != None and self.msgC2 != None and self.d1 != None and self.d2 != None:
			self.changeState('ACTIF',0)

	###
	def outputFnc(self):
		assert(self.msgQ != None and self.msgC2 != None)
		
		s = self.msgQ.time
		
		self.msgQ.time = self.timeNext
		self.msgC2.time = self.timeNext

		self.poke(self.OPorts[0], self.msgC2)
		
		### Si hiver
		if s < self.d2 or s > self.d1:
			self.msgQ.value[0] = float(self.msgQ.value[0]) - float(self.msgC2.value[0])
			self.poke(self.OPorts[1], self.msgQ)

		self.msgQ = None
		self.msgC2 = None
		
	###
  	def intTransition(self):
		# Changement d'etat
		self.changeState()

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState(self, status='IDLE', sigma=INFINITY):
		self.state['status'] = status
		self.state['sigma'] = sigma

	def __str__(self):return "Rep2"