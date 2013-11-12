# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AM_COM.py --- Atomic Model to represent antenna communication in a sensornode
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

import sys
import os
import copy

from random import *
	
import pyXLWriter as xl

from DomainInterface.DomainBehavior import DomainBehavior
from Tools.Message import Message

class COM(DomainBehavior):

	def __init__(self, nodeName='rien') :

	DomainBehavior.__init__(self) 

	# local copy
	self.myName = nodeName
		
	#definition des variables d'etats
	self.PHASE  = "FREE"
	self.SIGMA =INFINITY

	self.listmsg = []
	self.FiFoOut = []
	self.ERROR = 0
	self.indiceList = ["1", "2", "3", "4"]
	#self.count = 0
	#self.column1 = 0
	#self.row1 = 2
	#self.row2 = 2
	#self.column2 = 0
	#self.row3 = 2
	#self.column3 = 0
	#self.inPortList = []
	#self.outPortList = [] 
	#self.DirectionSet = []

	#for ip in range(self.iPort):
		#Iport = self.addInPort()
		#self.inPortList.append(Iport)
		
	#for op in range(self.oPort):
		#Oport = self.addOutPort()
		#self.outPortList.append(Oport)
		#self.DirectionSet.append ([None, self.outPortList[op] ,self.indiceList[op]])
		
	#self.INProcess  = self.addInPort() #from Process
	#self.OUTProcess = self.addOutPort()	


###################################################################################
####gestion des directions d'envoie des messages ; reconnaissance du prot en fonction
####de l'origine du message entrant	
	
####################################################################################

	
	def extTransition(self):

		# peek
		self.DirectionSet = []
		for ip in range(len(self.IPorts)):
			msg=self.peek(self.IPorts[ip])
			if (msg != None):
				self.DirectionSet.append([msg.sender,self.OPorts[np],np])
				self.listmsg.append(msg)
				
		self.msgProcess = self.peek(self.IPorts[4])
		
		print 'COM', self.myName, self.DirectionSet
			
		if (self.PHASE == "FREE"):
			for ip in range(len(self.listmsg)):
				if (self.listmsg[ip] != None) and (self.listmsg[ip] != self.myName):
					if (self.listmsg[ip].origin != self.myName):
						#self.listmsg.append(self.msgIn1)
						self.changeState("RECEiPT",0)
					
					else : 
						self.changeState("RECEiPT",0)
	
			self.changeState("RECEiPT",0)
			
		elif (self.PHASE == "BUSY"):
			if (self.msgProcess !=None) :
				#self.FiFoOut.append (self.listmsg[-1])
				self.changeState ("TRANSMIT",0)
 
	def outputFnc(self):
		self.i = 0					
		if (self.PHASE == "RECEiPT") :
			if (len(self.listmsg) != 0):
				self.msgProcessTo = self.listmsg.pop(0)
				self.poke(self.OPorts[4], self.msgProcessTo)
			"""else :
				self.poke(self.OUTProcess, Message ("","" ,"", 125, "OK", 0, 0, 0, 1, 2, 0, "", 90))"""
		
		elif (self.PHASE =="TRANSMIT") :
			if (self.msgProcess.typ == "OK"): 
				for self.i in range(len(self.DirectionSet)) :
					if (self.msgProcess.destination== self.DirectionSet[self.i][0]):
						self.msgProcess.lkq = randrange (50, 100)
						self.poke(self.DirectionSet[self.i][1], self.msgProcess )
			elif (self.msgProcess.typ != "OK"): 
				for self.i in range(len(self.DirectionSet)) :
					if (self.msgProcess.destination == self.DirectionSet[self.i][0]) and (self.msgProcess .destination != ""):
						self.msgProcess.lkq = randrange (50, 100)
						self.poke(self.DirectionSet[self.i][1], self.msgProcess )
						break
					elif (self.msgProcess.destination == "") and (self.msgProcess.typ == "WhiteFlag"):
						for ds in range(len(self.DirectionSet)):
							if (self.msgProcess.Port == self.DirectionSet[ds][2]):
								self.msgProcess.lkq = randrange (50, 100)
								self.poke(self.DirectionSet[ds][1], self.msgProcess)	
						break	
					elif (self.msgProcess.destination != self.DirectionSet[self.i][0]) and (self.msgProcess.destination != "") and (self.msgProcess.typ == "ACK"):
						if (self.msgProcess.sender == self.DirectionSet[self.i][0]):
							self.msgProcess.lkq = randrange (50, 100)
							self.msgProcess.hop = 0
							self.poke(self.DirectionSet[self.i][1],self.msgProcess)

	def intTransition(self):				
		if (self.PHASE == "RECEiPT"):
			self.changeState("BUSY",INFINITY)
		elif (self.PHASE == "TRANSMIT"):
			self.changeState()	
			
	def changeState (self, phase ="FREE", sigma=INFINITY):
		self.PHASE = phase
		self.SIGMA = sigma
	
	def __str__(self):
		return (self.myName, len(self.listmsg), "COM", self.PHASE, self.ERROR, self.DirectionSet)

	def timeAdvance(self):
		return self.SIGMA
