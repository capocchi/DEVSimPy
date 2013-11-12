# -*- coding: utf-8 -*-

"""
Name: STO.py

Author(s): 
Version: 0.1
Last modified: 09/03/2011 
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior 

class STO(DomainBehavior):
	"""
	"""

	def __init__(self):
		"""
		"""
		DomainBehavior.__init__(self)
		
		self.stock = [0.0,0.0,0.0]
		
		self.state = {'status':'IDLE','sigma':INFINITY}

	###
  	def intTransition(self):
		# Changement d'etat
		self.changeState()

	###
	def extTransition(self):
		
		msg = None
		for i,port in enumerate(self.IPorts):
			msg = self.peek(port)
			
			if msg != None:
				
				### write
				if i == 0:
					self.stock = msg.value
				
				### read
				self.msg = msg
				self.msg.value = self.stock

				# changement d'etat
				self.changeState('ACTIF',0)
		
	###
  	def outputFnc(self):		
		assert(self.msg!=None)

		self.msg.time=self.timeNext
		# envoie du message sur les ports de sortie
		self.poke(self.OPorts[0], self.msg)

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status']=status
		self.state['sigma']=sigma

	def __str__(self):return "STO"


