# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AM_COM.py --- Atomic Model to represent antenna communication in a sesnornode
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
import copy
from random import *

try:
	from PSDomain.PSDomainBehavior import PSDomainBehavior
except ImportError:
	import sys,os
	for spath in [os.pardir+os.sep]:
		if not spath in sys.path: sys.path.append(spath)
	from PSDomain.PSDomainBehavior import PSDomainBehavior

from Message import *

class COM(PSDomainBehavior):

 def __init__(self) :
 
	PSDomainBehavior.__init__(self)
	print "ok"
 	#definition des variables d'etats
	self.PHASE  = "FREE"
	self.SIGMA =__INFINITY__
	self.myName = ""
	self.FiFoIn = []
	self.FiFoOut =  []

 	#creation de port
	self.IN1  = self.addInPort() # message venant de l'exterieur
	self.IN2  = self.addInPort() # message venant de l'esterieur
	self.IN3  = self.addInPort() # message venant de l'exterieur
	self.IN4  = self.addInPort() # message venan tde l'exterieur
	self.INProcess  = self.addInPort() #from Process
	self.OUT1 = self.addOutPort() # message vers un noeud
	self.OUT2 = self.addOutPort() # message vers un noeud
	self.OUT3 = self.addOutPort() # message vers un autre noeud
	self.OUT4 = self.addOutPort() # message vers un noeud
	self.OUTProcess = self.addOutPort()
###################################################################################
####gestion des directions d'envoie des messages ; reconnaissance du prot en fonction
####de l'origine du message entrant	
	
	self.DIRECTION = ""
	self.DIRECTION2 = ""
	self.DIRECTION3 = ""
	self.DIRECTION4 = ""
####################################################################################
	self.OUTBattery = self.addOutPort() 
	self.DirectionSet = [[self.DIRECTION],[ self.DIRECTION2], [self.DIRECTION3], [self.DIRECTION4,]]
	
 def extTransition(self):
	print "entree de COM"
	self.msgIn1 = self.peek(self.IN1) # provenant exterieur
	self.msgIn2 = self.peek(self.IN2) # provenant exterieur
	self.msgIn3 = self.peek(self.IN3) # provenant exterieur
	self.msgIn4 = self.peek(self.IN4) # provenant exterieur
	self.msgProcessFrom =self.peek(self.INProcess)	
	if (self.PHASE == "FREE"):
		if (self.msgIn1 != None) :
			self.DIRECTION = self.msgIn1.origin
			self.FiFoIn.append (self.msgIn1)
		elif (self.msgIn2 != None):
			self.DIRECTION2 = self.msgIn2.origin
			self.FiFoIn.append (self.msgIn2)
		elif (self.msgIn3 != None):
			self.DIRECTION3 = self.msgIn3.origin
			self.FiFoIn.append (self.msgIn3)
		elif (self.msgIn4 != None):	
			self.DIRECTION4= self.msgIn4.origin
			self.FiFoIn.append (self.msgIn4)
		self.changeState("RECEiPT",0.04)
	elif (self.PHASE == "BUSY"):
		self.FiFoOut.append(self.msgProcessFrom)
		self.changeState ("TRANSMIT",0.04)
 
 def outputFnc(self):
	
	self.i = 0
	if (self.PHASE == "RECEiPT") :
		self.msgProcessTo = self.FiFoIn.pop(0)
		self.poke(self.OUTProcess, self.msgProcessTo)
		print "sortie de Com"
	elif (self.PHASE =="TRANSMIT") : 
		if (self.msgProcessFrom.typ == "ACK"):
			self.msgProcessFrom = self.FiFoOut.pop(0)
			self.msgWF0 = copy.deepcopy(self.msgProcessFrom)
			self.msgWF0.typ = "WhiteFlag"
			self.msgWF1 = copy.deepcopy(self.msgProcessFrom)
			self.msgWF1.typ = "WhiteFlag"
			self.msgWF2 = copy.deepcopy(self.msgProcessFrom)
			self.msgWF2.typ = "WhiteFlag"
			if (self.msgProcessFrom.destination == self.DirectionSet[0][0]):
				self.poke(self.DirectionSet[0,0], self.msgProcessFrom)			
				self.msgWF0.destination = self.DirectionSet[1][0]
				self.msgWF1.detination = self.DirectionSet[2][0]	
				self.msgWF2.destination = self.DirectionSet[3][0]
			elif (self.msgProcessFrom.destination == self.DirectionSet[1][0]):
				self.poke(self.DirectionSet[1,0], self.msgProcessFrom)		
				self.msgWF0.destination = self.DirectionSet[0][0]
				self.msgWF1.detination = self.DirectionSet[2][0]	
				self.msgWF2.destination = self.DirectionSet[3][0]
			elif (self.msgProcessFrom.destination == self.DirectionSet[2][0]):
				self.poke(self.DirectionSet[2][0], self.msgProcessFrom)						
				self.msgWF0.destination = self.DirectionSet[0][0]
				self.msgWF1.detination = self.DirectionSet[1][0]	
				self.msgWF2.destination = self.DirectionSet[3][0]
			elif (self.msgProcessFrom.destination == self.DirectionSet[3][0]):
				self.poke(self.DirectionSet[3][0], self.msgProcessFrom)		
				self.msgWF0.destination = self.DirectionSet[0][0]
				self.msgWF1.detination = self.DirectionSet[1][0]	
				self.msgWF2.destination = self.DirectionSet[2][0]		
			self.FiFoOut.insert(0,self.msgWF0)
			self.FiFoOut.insert(1,self.msgWF1)
			self.FiFoOut.insert(2,self.msgWF2)
		elif (self.msgProcessFrom.typ != "ACK"): 
			for self.i in self.DirectionSet :
				print self.i
				if (self.msgProcessFrom.destination == self.DirectionSet[self.i][0]):
					self.msgProcessFrom = self.FiFoIn.pop(0)
					self.poke(self.i[1], self.msgProcessFrom)
					break
		
 def intTransition(self):
	if (self.PHASE == "RECEiPT"):
		self.changeState("BUSY",__INFINITY__)
	elif (self.PHASE == "TRANSMIT"):
		self.changeState()	
		
 def changeState (self, phase ="FREE", sigma=__INFINITY__, go = 0):
	self.PHASE = phase
	self.SIGMA = sigma
	self.GO = go
	
 def __str__(self):
	 return "COM"
	#return (self.myName, "COM", self.PHASE, self.DirectionSet,self.FiFoIn, self.FiFoOut)
 
 def timeAdvance(self):
   return self.SIGMA
####################################################################################################################