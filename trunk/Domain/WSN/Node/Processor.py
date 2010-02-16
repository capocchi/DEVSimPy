# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AM_Processor..py --- Atomic Model to represent processor in a sesnornode
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

try:
	from PSDomain.PSDomainBehavior import PSDomainBehavior
except ImportError:
	import sys,os
	for spath in [os.pardir+os.sep]:
		if not spath in sys.path: sys.path.append(spath)
	from PSDomain.PSDomainBehavior import PSDomainBehavior

from Message import *

class Processor(PSDomainBehavior):

 def __init__(self, myName=None) :

	PSDomainBehavior.__init__(self)
	
	# local copy
	self._myName = myName
	print "Ok Proc"
 #definition des variables d'etats
	self.PHASE  = "FREE"
	self.GO = 0
	self.SIGMA = __INFINITY__
	self.Activity = 0
	

 #creation de port
	self.IN1  = self.addInPort() # provenant de COM
	self.IN2  = self.addInPort() # provenant de Battery
	self.IN3  = self.addInPort() # sensorboard
	self.IN4  = self.addInPort() # Memory
	self.IN5  = self.addInPort() # Net
	self.IN6  = self.addInPort() # Flash
	self.OUT1 = self.addOutPort() # vers COM
	self.OUT2 = self.addOutPort() # vers Sensorboard
	self.OUT3 = self.addOutPort() # vers Net
	self.OUT4 = self.addOutPort() # vers Flash
	self.OUT5 = self.addOutPort() # vers Memory
	self.OUT6 = self.addOutPort() # versBattery


 def extTransition(self):
	print "entre dans Proc"
	self.msg  = self.peek(self.IN1) # collecte des messages en entr�e 
	self.msg2 = self.peek(self.IN2)
	self.msg3 = self.peek(self.IN3)
	self.msg4 = self.peek(self.IN4)
	self.msg5 = self.peek(self.IN5)
	self.msg6 = self.peek(self.IN6)
	if (self.msg != None) & (self.PHASE == "FREE"):# provenant de COM
		if (self.msg.typ == "router"):
			self.changeState("BUSY",1, 0) # un message arrive de COM on l'oriente vers NET
			self.Activity += 1
		elif (self.msg.typ == "BSCollect"):
			self.changeState("BUSY",2, 0) # un message arrive de COM on l'oriente vers SB
			self.Activity += 1
		elif (self.msg.typ == "ChangeID") :
			self.changeState("BUSY",3, 0) # un message arrive de COM on l'oriente vers Flash
			self.Activity += 1
		elif (self.msg.typ == "MemCollect") : ## un message arrive de COM on l'oriente vers Memory
			self.changeState("BUSY",4, 0)
			self.Activity += 1
		elif (self.msg.typ == "Update"): ## un message arrive de COM pour une mise � jour
			self.changeState("BUSY",11, 0)
			self.Activity += 1
		elif (self.msg.typ == "WhiteFlag") :  ## un message arrive de COM pour d�couverte du r�seau
			self.changeState("BUSY",12, 0)
			self.Activity += 1
		elif (self.msg.typ == "ACK"): ## un message arrive de COM pour d�couverte du r�seau
			self.changeState("BUSY",13, 0)
			self.Activity += 1
		elif (self.msg.typ == "OK"): ## un message arrive de COM pour d�couverte du r�seau
			self.changeState("BUSY",14, 0)
			self.Activity += 1
		elif (self.msg.typ == ""): ## un message arrive de COM pour d�couverte du r�seau
			self.changeState("BUSY",15, 0)
			self.Activity += 1
	elif (self.msg2 != None) & (self.PHASE == "FREE"):# provenant de Battery
		self.Activity += 1
		self.changeState("DEAD",11, 0)	 # un message arrive de Battery  on l'oriente vers COM
	elif (self.msg3 != None) & (self.PHASE == "FREE"):# sensorboard
		 if (self.msg3.typ == "stock"):
		 	self.changeState("BUSY",5, 0) # un message arrive de SB on l'oriente vers Memory
		 	self.Activity += 1
		 elif(self.msg3.typ == "Alert"): # # un message arrive de SB on l'oriente vers NET
		 	self.changeState("BUSY",6, 0)
		 	self.Activity += 1
		 elif(self.msg3.typ == "Send"): # # un message arrive de SB on l'oriente vers NET
		 	self.changeState("BUSY",7, 0)
		 	self.Activity += 1
	elif(self.msg4 != None) & (self.PHASE == "FREE"):# Memory 
		 self.changeState ("BUSY",8, 0) # un message arrive de Memory  on l'oriente vers NET
		 self.Activity += 1
	elif(self.msg5 != None) & (self.PHASE == "FREE"):# Net
		 self.changeState ("BUSY",9, 0) # un message arrive de Net on l'oriente vers COM
		 self.Activity += 1
	elif(self.msg6 != None) & (self.PHASE == "FREE"):# Flash
		 self.changeState ("BUSY",10, 0) # �a d�pend � voir
		 self.Activity += 1	 	 
		 
 def timeAdvance(self):
   return self.SIGMA
 
 def outputFnc(self):
	print "sorti Proc"
	if (self.PHASE == "BUSY") & (self.GO == 1) :# vers Net
		self.msg.conso = 0.8		
		self.poke(self.OUT3, self.msg)		# determine la consommation d'energie pour chaque action r�alis�e
		self.poke(self.OUT6, self.msg.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 2) : # vers SensorBoard
		self.msg.conso = 0.8		
		self.poke(self.OUT2, self.msg)	
		self.poke(self.OUT6, self.msg.conso) # vers SensorBoard
	elif (self.PHASE == "DEAD") & (self.GO == 11): # vers COM
		self.msg2.typ = "dead"
		self.poke(self.OUT1, self.msg2)
	elif (self.PHASE == "BUSY") & (self.GO == 3):
		self.msg.conso = 0.8		
		self.poke(self.OUT4, self.msg) 	     # vers Flash
		self.poke(self.OUT6, self.msg.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 4):# vers Memory
		self.msg.typ == "collectData"
		self.msg.conso = 0.8
		self.poke(self.OUT6, self.msg.conso)
		self.poke(self.OUT5, self.msg)	
	elif (self.PHASE == "BUSY") & (self.GO == 5):# vers Memory
		self.msg3.typ = "updata"
		self.msg3.conso = 0.8
		self.poke(self.OUT6, self.msg3.conso)
		self.poke(self.OUT5, self.msg3)
	elif (self.PHASE == "BUSY") & (self.GO == 6):#vers Net
		self.msg3.conso = 0.8		
		self.poke(self.OUT3, self.msg3)
		self.poke(self.OUT6, self.msg3.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 7): #vers Net
		self.msg4.conso = 0.8		
		self.poke(self.OUT3, self.msg3)
		self.poke(self.OUT6, self.msg3.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 8): # vers memory
		self.msg4.conso = 0.8		
		self.poke(self.OUT3, self.msg4)
		self.poke(self.OUT6, self.msg4.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 9): # vers COM
		self.msg5.conso = 0.8
		self.poke(self.OUT1, self.msg5)
		self.poke(self.OUT6, self.msg5.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 11) :# vers Net
		self.msg.conso = 0.8 			
		self.poke(self.OUT3, self.msg)		# determine la consommation d'energie pour chaque action r�alis�e
		self.poke(self.OUT6, self.msg.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 12) :# vers Net
		self.msg.conso = 0.8 	
		self.poke(self.OUT3, self.msg)		#
		self.poke(self.OUT6, self.msg.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 13) :# vers Net
		self.msg.conso = 0.8 			
		self.poke(self.OUT3, self.msg)		#
		self.poke(self.OUT6, self.msg.conso)
	elif (self.PHASE == "BUSY") & (self.GO == 14) :# vers Net
		self.msg.conso = 0.8 			
		self.poke(self.OUT3, self.msg)		#
		self.poke(self.OUT6, self.msg.conso)
 	elif (self.PHASE == "BUSY") & (self.GO == 15) :# vers Net
		self.poke(self.OUT3, self.msg)		#
 def intTransition(self):
	if (self.PHASE == "BUSY"):
		self.changeState()
	else:
		self.changeState("DEAD", 500, __INFINITY__)

 def changeState (self, phase="FREE",go = 0, sigma=__INFINITY__):
	self.PHASE = phase
	self.GO = go
	self.SIGMA = sigma
	
 def __str__(self):
  	return "Processor"
 
