# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AM_Battery.py --- Atomic Model to represent battery in a sesnornode
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

class Battery(AtomicDEVS):


 def __init__(self, nodeName=None) :
 
	AtomicDEVS.__init__(self) 
	
	# local copy
	self.myName = nodeName
	
 #definition des variables d'etats
	self.PHASE  = "FREE"
	self.SIGMA =__INFINITY__
	
#declaration de variable de'énergie
	self.TOTAL = 100
	#creation de port
	self.IN1  = self.addInPort() # message venant de Process
	self.IN2  = self.addInPort() # message veant de COM
	self.IN3  = self.addInPort() # message venat de SensorBoard
	self.IN4  = self.addInPort()
	self.IN5  = self.addInPort()
	self.OUT1 = self.addOutPort() #vers Porcess
	
 def extTransition(self):
	
	self.msg  = self.peek(self.IN1) # collecte des mesages en entrée 
	self.msg2  = self.peek(self.IN2)
	self.msg3  = self.peek(self.IN3)
	self.msg4  = self.peek(self.IN4)
	self.msg5 = self.peek(self.IN5)
	if (self.msg != None) & (self.PHASE == "FREE"):
		self.TOTAL -= self.msg
		self.changeState("BUSY",__INFINITY__)
	elif (self.msg2!= None) & (self.PHASE == "FREE"):
		self.TOTAL -= self.msg2
		self.changeState("BUSY",__INFINITY__)
	elif (self.msg3 != None) & (self.PHASE == "FREE"):
		self.TOTAL -= self.msg3
		self.changeState("BUSY",__INFINITY__)
	elif (self.msg4 != None) & (self.PHASE == "FREE"):
		self.TOTAL -= self.msg4
		self.changeState("BUSY",__INFINITY__)
	elif (self.msg5 != None) & (self.PHASE == "FREE"):
		self.TOTAL -= self.msg5
		self.changeState("BUSY",__INFINITY__)		
 
 
 def timeAdvance(self):
   return self.SIGMA
 
 def outputFnc(self):
	if (self.TOTAL == 0):
		self.poke(self.OUT1, self.msg)
 def intTransition(self):
	if (self.PHASE == "BUSY"):
		self.changeState()	
 
 def changeState (self, phase="FREE", sigma=__INFINITY__):
	self.PHASE = phase
	self.SIGMA = sigma
 
 def __str__(self):
	return (self.myName,"Battery", self.PHASE, self.TOTAL)