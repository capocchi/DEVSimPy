# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Gain.py --- Generateur de la fonction sinus
#                     --------------------------------
#                        	 Copyright (c) 20079
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 08/05/09
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
from itertools import *

#    ======================================================================    #
class Gain(DomainBehavior):
	'''	Model atomique de la fonction gain
	'''

	###
	def __init__(self, k=1):
		'''	Constructeur
		'''
		DomainBehavior.__init__(self)

		# Declaration des variables d'etat (actif tout de suite)
		self.state = {	'status':	'IDLE', 'sigma': INFINITY}

		# Local copy
		self.k=k	# Gain y=k*x (QSS1/3)
		
	###
  	def intTransition(self):
		# Changement d'etat
		self.changeState()

	###
	def extTransition(self):
		# recuperation du message sur le port d'entre
		self.msg = self.peek(self.IPorts[0])

		# changement d'etat
		self.changeState('ACTIF',0)
		
	###
  	def outputFnc(self):
		assert(self.msg!=None)
		
		self.msg.value=list(imap(lambda x: self.k*x,self.msg.value))
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

	def __str__(self):return "Gain"
