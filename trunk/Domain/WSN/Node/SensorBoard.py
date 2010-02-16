# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AM_Sensorboard..py --- Atomic Model to represent sensor and sensing activity in a sesnornode
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

class SensorBoard(AtomicDEVS):

 def __init__(self, nodeName=None) :
 
	AtomicDEVS.__init__(self) 
	
	# local copy
	self.myName = nodeName
	
 #definition des variables d'etats
	self.PHASE  = "FREE"
	self.SIGMA = __INFINITY__
	
#declaration de variables de gestion routage
	self.newdata = [0,0,0,0,0]
	self.data1 = [22,33,18,26,10]
	self.data2 = [1,3,8,6,2]
	self.data3 = [1,3,8,6,3]
	self.data4 = [1,3,8,6,4]

 #creation de port
	self.IN1  = self.addInPort() # process
	self.IN2  = self.addInPort() # message venant du générateur de l'environnement
	self.OUT1 = self.addOutPort() # message vers process
	self.OUT2 = self.addOutPort() # message vers battery


 def extTransition(self):
	
	self.msg  = self.peek(self.IN1) # collecte des mesages en entrée 
	self.msg2  = self.peek(self.IN2) # collecte des mesages en entrée 
	if (self.msg != None) & (self.PHASE == "FREE"):
		if (self.msg.typ == "BSCollect"):
			self.changeState("BUSY",1, 0)
	elif (self.msg2 != None) & (self.PHASE == "FREE"):
		if (self.msg2.Temp > 60 ) or (self.msg2.humidity < 45) or (self.msg2.pressure > 110):                       #< >  < > 
			self.changeState("BUSY",2, 0)
		else :
			self.changeState("BUSY", 3, 0)

 
 def timeAdvance(self):
  	return self.SIGMA


 
 def outputFnc(self):
	if (self.PHASE == "BUSY") & (self.GO == 1):
		self.collectData()
		self.poke(self.OUT1, self.msg)
		self.msg.conso = 5
		self.poke(self.OUT2, self.msg.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 2):
		self.msg2.typ = "Alert"		
		self.poke(self.OUT1, self.msg2)
		self.msg2.conso = 5
		self.poke(self.OUT2, self.msg2.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 3):
		self.msg2.typ = "stock"
		self.poke(self.OUT1, self.msg2)
		self.msg2.conso = 5
		self.poke(self.OUT2, self.msg2.conso)
	elif (self.SIGMA == 2):
		self.collectData ()
		self.poke(self.OUT1,self.Message())
		self.msg.conso = 5
		self.poke(self.OUT2, self.msg.conso)

 
 def intTransition(self):
	 if (self.PHASE == "BUSY"):
	 	self.changeState()
			
 
 def changeState (self, phase="FREE",go = 0, sigma=__INFINITY__):
	self.PHASE = phase
	self.GO = go
	self.SIGMA = sigma
 		
 def collectData (self):
	self.msg.Temp = self.data1 [0]
	self.msg.humidity = self.data1 [1]
	self.msg.pressure = self.data1 [2]
	self.msg.GPS = self.data1 [3] 

 	
 def __str__(self):
 	 return (self.myName,"SensorBoard", self.PHASE, self.GO)