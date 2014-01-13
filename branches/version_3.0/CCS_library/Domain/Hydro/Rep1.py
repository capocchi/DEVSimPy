# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        Rep1.py

 Model:       Rep1 Model
 Author:      L. Capocchi (capocchi@univ-corse.fr), J.F. Santucci (sanutcci@univ-corse.fr), C. Nicolai (cnicolai@univ-corse.fr)

 Created:     2011-04-25
-------------------------------------------------------------------------------
"""

from DomainInterface.DomainBehavior import DomainBehavior

#    ======================================================================    #
class Rep1(DomainBehavior):
	'''	Model atomique de la modelisation du Rep1
	'''
	###
	def __init__(self):

            DomainBehavior.__init__(self)

            self.state = {'status':'IDLE', 'sigma':INFINITY}

            self.msgQ = None
            self.msgC1 = None

	def extTransition(self):

		#Recuperation du numero de Q et C1
		msgQ, msgC1 = map(self.peek, self.IPorts)
			
		if msgQ != None:
			self.msgQ = msgQ
		
		if msgC1 != None:
			self.msgC1 = msgC1
		
		# changement d etat que lorsque Q et C2 sont different de None
		if self.msgQ != None and self.msgC1 != None:
			self.changeState('ACTIF',0)
	###
  	def outputFnc(self):
		
		assert(self.msgQ != None and self.msgC1 != None)
		
		self.msgQ.time = self.timeNext
		self.msgC1.time = self.timeNext
		
		self.msgQ.value[0] -= float(self.msgC1.value[0])
		
		if self.msgQ.value[0] < 0:
			self.msgQ.value[0] = 0.0

		self.poke(self.OPorts[0], self.msgQ)
		self.poke(self.OPorts[1], self.msgC1)
		
		self.msgQ = None
		self.msgC1 = None

	###
  	def intTransition(self):
		# Changement d'etat
		self.changeState()

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status'] = status
		self.state['sigma'] = sigma

	def __str__(self):return "Rep1"
