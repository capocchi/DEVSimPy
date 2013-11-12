# -*- coding: utf-8 -*-

"""
Name: GR3J.py

Author(s): 
Version: 0.1
Last modified: 09/03/2011 
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS: port 0 Temp and port 1 Precip
"""

from DomainInterface.DomainBehavior import DomainBehavior 

class GR3J(DomainBehavior):
	"""
	"""

	def __init__(self):
		"""
		"""
		
		DomainBehavior.__init__(self)
		
		self.state = {'status':'IDLE','sigma':INFINITY}

	###
  	def intTransition(self):
		# Changement d'etat
		self.changeState()

	###
	def extTransition(self):
		
		self.msg = self.peek(self.IPorts[0])
		
		# changement d'etat
		self.changeState('ACTIF',0)
		
	###
  	def outputFnc(self):		

		### préparation de la valeur de stockage
		
		self.msg.value[0] = self.msg.value[0]*2/3.0
		self.msg.time = self.timeNext
	
		# debit
		self.poke(self.OPorts[0], self.msg)
			
	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status']=status
		self.state['sigma']=sigma

	def __str__(self):return "GR3J"