# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        <Pump.py>

 Model:       <Pump Model>
 Author:      <Nicolai Celine (cnicolai@univ-corse.fr)>

 Created:     <2011-02-26>
-------------------------------------------------------------------------------
"""

from DomainInterface.DomainBehavior import DomainBehavior
from itertools import *
from Object import Message

#    ======================================================================    #
class Intake(DomainBehavior):
	'''	Model atomique de la modelisation du pompage
	'''
	###
	def __init__(self,status='ACTIF',pump=0.0):
		DomainBehavior.__init__(self)
		'''	Constructeur
		'''
		DomainBehavior.__init__(self)

		self.state = {	'status':status,
                                'contenance':0.0,
                                'pump': pump,
                                'sigma': INFINITY }
	###
	def extTransition(self):
            #Input Ports
                self.debit = self.IPorts[0]

            #Recuperation debit
                msg = self.peek(self.debit)
                if(msg!=None):
                    debit = msg.value[0]
                    if debit > 0:
                        self.state['content'] += debit
	###
  	def outputFnc(self):
        
         #Input Ports
            self.demandeDebit = self.OPorts[0]
            self.envoieDebit = self.OPorts[1]

            msg = Message()
            if self.state['status'] == 'ACTIF':
                if self.state['contenance'] > 0:
                    msg.value = [self.state['contenance']]
                    msg.time = self.timeNext
                    # envoie du message sur les ports de sortie
                    self.poke(self.envoieDebit, self.msg)
                    self.state['contenance'] = 0
                else:
                    msg.value = [self.state['pump']]
                    msg.time = self.timeNext
                    self.poke(self.demandeDebit,msg)


        ###
  	def intTransition(self):
          # Changement d'etat
            self.changeState()


	###
  	def timeAdvance(self):
		return self.state['sigma']
        ###

        def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status']=status
		self.state['sigma']=sigma


	def __str__(self):return "Pump"
