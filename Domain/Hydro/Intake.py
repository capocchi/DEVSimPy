# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        <Intake.py>

 Model:       <Intake Model>
 Author:      <Nicolai Celine (cnicolai@univ-corse.fr)>

 Created:     <2010-11-29>
-------------------------------------------------------------------------------
"""

from DomainInterface.DomainBehavior import DomainBehavior
from itertools import *
from Object import Message

#    ======================================================================    #
class Intake(DomainBehavior):
	'''	Model atomique de la mod�lisation d une prise d eau
	'''
	###
	def __init__(self):
		DomainBehavior.__init__(self)
		'''	Constructeur
		'''
		self.state = {	'status':'IDLE',
                                'contenance':0.0,
                                'sigma': INFINITY }
	###
	def extTransition(self):
            #Port d entree
            self.rainfall = self.IPorts[0]
            self.snowslide = self.IPorts[1]
            self.afflu = self.IPorts[2]

            # changement d'etat
            self.changeState('ACTIF',0)
            self.state['contenance']=0

            #R�cup�ration des donn�e de pluie
            msgRainfall = self.peek(self.rainfall)
            if(msgRainfall!=None):
                self.state['contenance'] += msgRainfall.value[0]

            #R�cup�ration des donn�es de neige
            msgSnowslide = self.peek(self.snowslide)
            if(msgSnowslide!=None):
                self.state['contenance'] += msgSnowslide.value[0]

            #Recup�ration des donn�es des affluents
            msgAfflu = self.peek(self.afflu)
            if(msgAfflu != None):
                self.state['contenance'] += msgAfflu.value[0]

	###
  	def outputFnc(self):
            if self.state['contenance'] > 0:
                msg = Message()
                msg.value = [self.state['contenance']]
                msg.time = self.timeNext

            # envoie du message sur les ports de sortie
                self.poke(self.OPorts[0],msg)

        ###
  	def intTransition(self):
            # Changement d'etat
            self.changeState()

	###
  	def timeAdvance(self):
		return self.state['sigma']
      
        ###
	def changeState( self, status = 'IDLE', sigma = INFINITY):
		self.state['status'] = status
		self.state['sigma']=sigma

                
	def __str__(self):return "Intake"
