# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AM_Flash.py --- Atomic Model to represent flash memory or buffer in a sesnornode
#                     --------------------------------
#                       Copyright (c) 2005
#                       Thierry Antoine-Santoni
#                      	University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 27/10/06
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
#  GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
__INFINITY__ = 10000000000000
__MINUTE__	 = 60

import sys, os
for spath in [os.pardir+os.sep+'Library']:
	if not spath in sys.path: sys.path.append(spath)
	
from DEVSKernel.DEVS import AtomicDEVS
from Tools import *

class Flash(AtomicDEVS):

 def __init__(self, nodeName=None) :
 
	AtomicDEVS.__init__(self) 
	
	# local copy
	self.myName = nodeName
	
 #definition des variables d'etats
	self.PHASE  = "FREE"
	self.SIGMA = __INFINITY__
#declaration de variables de gestion routage
	self.ID = "123"
#creation de port
	self.IN1  = self.addInPort() # message venant de l'exterieur
	self.OUT1 = self.addOutPort() #message vers un noeud
 
 def extTransition(self):
	
	self.msg  = self.peek(self.IN1) # collecte des mesages en entrée 
	if (self.msg != None) & (self.PHASE == "FREE"):
		self.changeState("BUSY", 0)


 def timeAdvance(self):
   return self.SIGMA
 
 def outputFnc(self):
	if (self.PHASE == "BUSY"):
		self.msg.ndid = self.ID
		self.poke(self.OUT1, self.msg)
			
 def intTransition(self):
	if (self.PHASE == "BUSY"):
		self.changeState()
		
 def changeState (self, phase="FREE", sigma=__INFINITY__):
	self.PHASE = phase
	self.SIGMA = sigma
 
 def __str__(self):
 	return (self.myName,"Flash", self.PHAS)

########################################################