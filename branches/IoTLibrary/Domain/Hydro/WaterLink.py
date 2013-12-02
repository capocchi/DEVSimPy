
# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        <WaterLink.py>

 Model:       <canalisation and "lachure" Model>
 Author:      <Nicolai Celine (cnicolai@univ-corse.fr)>

 Created:     <2010-11-29>
-------------------------------------------------------------------------------
"""

from DomainInterface.DomainBehavior import DomainBehavior
from itertools import *
from Object import Message

#    ======================================================================    #
class WaterLink(DomainBehavior):
	'''	Model atomique de la modelisation de canaux et de lachure
	'''

	###
	def __init__(self, p=100.0):
		'''	Constructeur

			@p : pourcent of leak 
		'''
		DomainBehavior.__init__(self)

		self.state = {	'status':'IDLE', 'sigma': INFINITY}

		
		self.p=p	# y=debit*(p/100)

	###
  	def intTransition(self):
		# Changement d etat
		self.changeState()

	###
	def extTransition(self):
		# recuperation du message sur le port d entre
		self.msg = self.peek(self.IPorts[0])

		# changement d etat
		self.changeState('ACTIF',0)

	###
  	def outputFnc(self):
	
                self.msg.value[0] *= float(self.p/100.0)
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

	def __str__(self):return "WaterLink"