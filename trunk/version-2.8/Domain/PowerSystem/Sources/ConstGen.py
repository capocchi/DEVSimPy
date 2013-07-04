# -*- coding: utf-8 -*-

"""
Name : ConstGen.py 
Brief descritpion : Constant generator atomic model 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 21/03/09
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior
from Domain.PowerSystem.Object import Message

#    ======================================================================    #
class ConstGen(DomainBehavior):
	"""	Constant atomic model.
	"""

	###
	def __init__(self, v=1.0):
		"""	Constructor.

			@param v : constante value
		"""
		DomainBehavior.__init__(self)

		# State variables
		self.state = {'status':'ACTIVE', 'sigma':0}

		# Local copy
		self.v = v
		
	###
	def intTransition(self):
		"""
		"""
		self.state = self.changeState()

	###
	def outputFnc(self):
		"""
		"""
		# envoie du message le port de sortie
		for i in xrange(len(self.OPorts)):
			self.poke(self.OPorts[i], Message([self.v, 0.0, 0.0], self.timeNext))

	###
	def timeAdvance(self):
		"""
		"""
		return self.state['sigma']

	###
	def changeState(self, status ='IDLE', sigma=INFINITY):
		"""
		"""
		return {'status':status, 'sigma':sigma}

	###
	def __str__(self):return "ConstGen"