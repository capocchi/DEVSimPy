# -*- coding: utf-8 -*-

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

__MINUTE__	 = 60

import sys, os
import copy
from random import *

from DomainInterface.DomainBehavior import DomainBehavior

class COM(DomainBehavior):

	def __init__(self) :

		DomainBehavior.__init__(self) 

		#definition des variables d'etats
		self.PHASE  = "FREE"
		self.SIGMA =INFINITY
		self.myName = ""
		self.FiFoIn = []
		self.FiFoOut =  []

		###################################################################################
		####gestion des directions d'envoie des messages ; reconnaissance du port en fonction
		####de l'origine du message entrant	

		####################################################################################
		self.DIRECTION = ""
		self.DIRECTION2 = ""
		self.DIRECTION3 = ""
		self.DIRECTION4 = ""
		self.DirectionSet = [[self.DIRECTION],[self.DIRECTION2], [self.DIRECTION3], [self.DIRECTION4]]
	
	def extTransition(self):
		
		self.msgIn1 = self.peek(self.IPorts[0]) # provenant exterieur
		self.msgIn2 = self.peek(self.IPorts[1]) # provenant exterieur
		self.msgIn3 = self.peek(self.IPorts[2]) # provenant exterieur
		self.msgIn4 = self.peek(self.IPorts[3]) # provenant exterieur
		self.msgProcessFrom = self.peek(self.IPorts[4])
		
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
			self.changeState("RECEiPT",0)
		elif (self.PHASE == "BUSY"):
			self.FiFoOut.append(self.msgProcessFrom)
			self.changeState ("TRANSMIT",0)
 
	def outputFnc(self):
		if (self.PHASE == "RECEiPT") :
			self.msgProcessTo = self.FiFoIn.pop(0)
			self.poke(self.OPorts[4], self.msgProcessTo)
		elif (self.PHASE =="TRANSMIT") : 
			if (self.msgProcessFrom.typ == "ACK"):
				self.msgProcessFrom = self.FiFoOut.pop(0)
				self.msgWF0 = copy.copy.msgProcessFrom
				self.msgWF0.typ = "WhiteFlag"
				self.msgWF1 = copy.copy.msgProcessFrom
				self.msgWF1.typ = "WhiteFlag"
				self.msgWF2 = copy.copy.msgProcessFrom
				self.msgWF2.typ = "WhiteFlag"
				if (self.msgProcessFrom.destination == self.DirectionSet[0,0]):
					self.poke(self.DirectionSet[0,0], self.msgProcessFrom)			
					self.msgWF0.destination = self.DirectionSet[1,0]
					self.msgWF1.detination = self.DirectionSet[2,0]	
					self.msgWF2.destination = self.DirectionSet[3,0]
				elif (self.msgProcessFrom.destination == self.DirectionSet[1,0]):
					self.poke(self.DirectionSet[1,0], self.msgProcessFrom)		
					self.msgWF0.destination = self.DirectionSet[0,0]
					self.msgWF1.detination = self.DirectionSet[2,0]	
					self.msgWF2.destination = self.DirectionSet[3,0]
				elif (self.msgProcessFrom.destination == self.DirectionSet[2,0]):
					self.poke(self.DirectionSet[2,0], self.msgProcessFrom)						
					self.msgWF0.destination = self.DirectionSet[0,0]
					self.msgWF1.detination = self.DirectionSet[1,0]	
					self.msgWF2.destination = self.DirectionSet[3,0]
				elif (self.msgProcessFrom.destination == self.DirectionSet[3,0]):
					self.poke(self.DirectionSet[3,0], self.msgProcessFrom)		
					self.msgWF0.destination = self.DirectionSet[0,0]
					self.msgWF1.detination = self.DirectionSet[1,0]	
					self.msgWF2.destination = self.DirectionSet[2,0]		
				self.FiFoOut.insert(0,self.msgWF0)
				self.FiFoOut.insert(1,self.msgWF1)
				self.FiFoOut.insert(2,self.msgWF2)
			elif (self.msgProcessFrom.typ != "ACK"): 
				for i in self.DirectionSet :
					if (self.msgProcessFrom.destination == self.DirectionSet[i,0]):
						self.msgProcessFrom = self.FiFoIn.pop(0)
						self.poke(i[1], self.msgProcessFrom)
						break			

	def intTransition(self):
		if (self.PHASE == "RECEiPT"):
			self.changeState("BUSY",INFINITY)
		elif (self.PHASE == "TRANSMIT"):
			self.changeState()	
		
	def changeState (self, phase ="FREE", sigma=INFINITY, go = 0):
		self.PHASE = phase
		self.SIGMA = sigma
		self.GO = go
	
	def __str__(self):
		return (self.myName, "COM", self.PHASE, self.DirectionSet,self.FiFoIn, self.FiFoOut)

	def timeAdvance(self):
		return self.SIGMA
