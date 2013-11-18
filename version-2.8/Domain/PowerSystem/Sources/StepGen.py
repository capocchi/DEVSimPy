# -*- coding: utf-8 -*-

"""
Name : StepGen.py 
Brief descritpion : Step generator atomic model 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 21/03/09
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior
from Domain.PowerSystem.Object import Message

#    ======================================================================    #
class StepGen(DomainBehavior):
	'''	Model atomique de la fonction "marche"
	'''

	###
	def __init__(self, ui=0.0, t0=0.01, uf=0.5):
		"""	Constructor.

			@param ui : initial value
			@param t0 : step time
			@param uf : final value

		"""
		DomainBehavior.__init__(self)

		# Declaration des variables d'�tat (actif tout de suite)
		self.state = {	'status': 'ACTIVE', 'sigma': 0}

		# Local copy
		self.ui=ui
		self.t0=t0
		self.uf=uf
		
		self.aux = False
		self.S = [self.ui, 0, 0]
		
	###
  	def intTransition(self):
		"""
		"""
		if (self.aux == False):
			# Changement d'�tat
			self.state = self.changeState(sigma=self.t0)
			self.aux = not self.aux
		else:
			# Changement d'�tat (IDLE pendant le temps restant jusqu'au final time d�finit dans param)
			self.state = self.changeState(sigma=FINAL_TIME-(self.timeNext-self.timeLast))
			self.S[0]=self.uf

	###
  	def outputFnc(self):
		"""
		"""
		# envoie du message le port de sortie
		self.poke(self.OPorts[0], Message(self.S, self.timeNext))

	###
  	def timeAdvance(self):
		"""
		"""
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		"""
		"""
		return { 'status':status, 'sigma':sigma}

	###
	def __str__(self):return "StepGen"
