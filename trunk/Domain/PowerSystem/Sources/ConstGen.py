# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ConstGen.py --- Constant atomic model.
#                     --------------------------------
#                        	 Copyright (c) 2010
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/02/10
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

#    ======================================================================    #
class ConstGen(DomainBehavior):
	"""	Constant atomic model.
	"""

	###
	def __init__(self, v=1.0):
		"""	Constructor.
		"""
		DomainBehavior.__init__(self)

		# State variables
		self.state = {	'status': 'ACTIVE', 'sigma':0}

		# Local copy
		self.v = v
		
	###
  	def intTransition(self):
		self.state = self.changeState()

	###
  	def outputFnc(self):
		
		L=[self.v,0,0]

		# envoie du message le port de sortie
		for i in range(len(self.OPorts)):
			self.poke(self.OPorts[i], Message(L,self.timeNext))

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		return { 'status':status, 'sigma':sigma}

	###
	def __str__(self):return "ConstGen"
