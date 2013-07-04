# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AM_BaseStation.py --- Atomic Model to represent origin of network.
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
from Tools.Message import Message

class BaseStation(AtomicDEVS):

 
 def __init__(self):
	 AtomicDEVS.__init__(self)
	 self.myName = "BaseStation"
	 self.PHASE = "FREE"
	 self.SIGMA = 0
	 self.GO = 50
	 self.OUT1 = self.addOutPort()
	 self.IN1 = self.addInPort()
	 self.msgIn1 = Message()
	 
 def extTransition(self):
	self.msgIn1 = self.peek(self.IN1) 
	if (self.msgIn1 != None) & (self.PHASE == "FREE")  & (self.GO == 0) :
		self.changeState ("OK",0,1)
			
 def outputFnc(self):
	 if (self.PHASE == "FREE") & (self.GO == 50) :
	 	self.poke(self.OUT1,  Message ("BS","" ,"", 125, "WhiteFlag", 0, 0, 0, 1, 2, 0, "", 90))
	 elif (self.PHASE == "OK") & (self.GO == 1) :
	 	self.poke(self.OUT1,  Message ("BS","" ,"", 125, "OK", 0, 0, 0, 1, 2, 0, "", 90))
  	 elif (self.PHASE == "BUSY") & (self.GO == 2) :
	 	self.poke(self.OUT1,  Message ("BS","" ,"", 125, "WhiteFlag", 0, 0, 0, 1, 2, 0, "", 90))
 
 def intTransition(self):
	if (self.PHASE =="FREE")  & (self.GO == 50)   : 
		self.changeState()
	elif (self.PHASE =="BUSY") & (self.GO == 0)  : 
		self.changeState ("FREE", __INFINITY__,0)
	elif (self.PHASE == "WF"): 
		self.changeState ("BUSY",self.SIGMA+4,2)
	elif (self.PHASE == "OK") & (self.GO == 1)  :
		self.changeState ("WF",__INFINITY__,0)
	elif (self.PHASE =="BUSY") & (self.GO == 2)  :
		self.changeState ("WF",__INFINITY__,0)
	 
 def changeState (self, phase ="FREE", sigm=__INFINITY__, go = 0):
	self.PHASE = phase
	self.SIGMA = sigm
	self.GO = 0
	 
 def timeAdvance(self):
	return self.SIGMA
		
 def __str__(self):
	 return ("BASESTATION", self.PHASE,  self.GO, self.msgIn1.typ)
		
####################################################################################################################
class GeneratorEnv(AtomicDEVS):

 
 
 def __init__(self):
	 AtomicDEVS.__init__(self)
	 self.SIGMA =__INFINITY__
	 self.OUT1 = self.addOutPort()
	 self.myName = ""	
 
 def outputFnc(self):
	 self.poke(self.OUT1,  Message("" , "", 0, "", 0, 75, 58, 12, 2, 1))
  
 def intTransition(self):
	 self.SIGMA = __INFINITY__
	 
 def timeAdvance(self):
  	 return self.SIGMA
		
 def __str__(self):
	 return ("GENERATOREnv",self.myName)