# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AM_Net.py --- Atomic Model to represent network mangement in a sesnornode
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
for spath in [os.pardir+os.sep+'Library']:
	if not spath in sys.path: sys.path.append(spath)
	
from Tools.Message import Message

	
from DEVSKernel.DEVS import AtomicDEVS

class Net(AtomicDEVS):

 def __init__(self) :
 
	AtomicDEVS.__init__(self) 
	#definition des variables d'etats
	self.PHASE  = "FREE"
	self.SIGMA = __INFINITY__
	self.myName = ""
	
 	
	self.IN1  = self.addInPort() # message venant de process
	self.OUT1 = self.addOutPort() #message vers process
	self.newneighbor = ["","", 0,"newneigbor",0,1000000]
   	self.neighbor1  =["","",0,"neigbor1",0,1000000] # name,parent, link quality, nom, frequency, hop
	self.neighbor2 = ["","",0,"neigbor2",0,1000000]
	self.neighbor3 = ["","",0,"neigbor3",0,1000000]
	self.FiFo = []
	#self.msgout = Message()

 def extTransition(self):
	self.msg  = self.peek(self.IN1) # collecte des messages en entrée 
	if (self.msg != None) & (self.PHASE == "FREE"):
		if (self.msg.typ == "router"):
			self.changeState("BUSY", 0)
			self.msg.destination = self.neighbor1[0]
			self.msg.hierarchy = self.neighbor1[2]
			self.FiFo.append(self.msg)
		elif (self.msg.typ == "Update"):
			self.changeState("BUSY", 0)
			self.upDatelk (self.msg)
		elif (self.msg.typ == "WhiteFlag"):
			self.msg.hop +=1
			self.upDatelk (self.msg)
			self.msg.typ = "ACK"
			self.msg.destination = self.msg.origin
			self.msg.origin = self.myName 
			self.msg.parent = self.neighbor1[0]
			self.changeState("BUSY",0)
			self.FiFo.append(self.msg)
		elif (self.msg.typ == "ACK"):
			self.msg.hop +=1
			self.changeState("BUSY",0)
			self.upDatelk (self.msg)
			self.msg.typ = "OK"
			self.msg.destination = self.msg.origin 
			self.msg.origin = self.myName
			self.FiFo.append(self.msg)
		elif (self.msg.typ == "OK"):
			self.msg.destination = self.msg.origin
			self.msg.origin = self.myName
			self.msg.typ = "OK"
			self.FiFo.insert(1,self.msg)
			self.changeState("BUSY",0)
		elif (self.msg.typ == ""):
			self.changeState("BUSY",0)
			
	elif (self.msg == None) & (self.PHASE == "FREE") & ((len(self.DirectionSet)) != 0) :	
		self.changeState("VIDE",self.SIGMA+0.01)
	
			
 def upDatelk (self,msge = Message()):
	self.msag = msge
	if (self.msag.origin == self.neighbor1[0]):
		self.neighbor1[4] +=1		# mise à jour de la fréquence
	elif (self.msag.origin == self.neighbor2[0]):
		self.neighbor2[4] +=1
	elif (self.msag.origin == self.neighbor3[0]):
		self.neighbor3[4] +=1
	elif (self.msag.origin != self.neighbor1[0]) or (self.msag.origin[0] != self.neighbor2) or (self.msag.origin[0] != self.neighbor3):#test de la table
		if (self.msag.hop < self.neighbor1[5]) : # nouvel arrivant classé par sa connetivité
			self.newneighbor[0] = self.msag.origin
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor1"
			self.newneighbor[5] = self.msag.hop-1
			self.data11 = copy.copy(self.neighbor1)
			self.data1 = copy.copy(self.newneighbor)
			self.neighbor1 = copy.copy(self.newneighbor)
			self.data22 = copy.copy(self.neighbor2)
			self.neighbor2 = copy.copy(self.data11)
			self.data33 = copy.copy(self.neighbor3)
			self.neighbor3 = copy.copy(self.data22)
		elif (self.msag.hop == self.neighbor1[5]) & (self.msag.lkq > self.neighbor1[2]):
			self.newneighbor[0] = self.msag.origin
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor1"
			self.newneighbor[5] = self.msag.hop-1
			self.data11 = copy.copy(self.neighbor1)
			self.data1 = copy.copy(self.newneighbor)
			self.neighbor1 = copy.copy(self.newneighbor)
			self.data22 = copy.copy(self.neighbor2)
			self.neighbor2 = copy.copy(self.data11)
			self.data33 = copy.copy(self.neighbor3)
			self.neighbor3 = copy.copy(self.data22)
		elif (self.msag.hop < self.neighbor2[5]):
			self.newneighbor[0] = self.msag.origin
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor2"
			self.newneighbor[5] = self.msag.hop-1
			self.data22 = copy.copy(self.neighbor2)
			self.neighbor2 = copy.copy(self.newneighbor)
			self.data33 = copy.copy(self.neighbor3)
			self.neighbor3 = copy.copy(self.data22)
		elif (self.msag.hop == self.neighbor2[5]) & (self.msag.lkq > self.neighbor2[2]):
			self.newneighbor[0] = self.msag.origin
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor2"
			self.newneighbor[5] = self.msag.hop-1
			self.data22 = copy.copy(self.neighbor2)
			self.neighbor2 = copy.copy(self.newneighbor)
			self.data33 = copy.copy(self.neighbor3)
			self.neighbor3 = copy.copy(self.data22)
		elif (self.msag.hop < self.neighbor3[5]):
			self.newneighbor[0] = self.msag.origin
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor3"
			self.newneighbor[5] = self.msag.hop-1
	 		self.neighbor3 = copy.copy(self.newneighbor)
		elif (self.msag.hop == self.neighbor3[5]) & (self.msag.lkq > self.neighbor3[2]):
			self.newneighbor[0] = self.msag.origin
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor3"
			self.newneighbor[5] = self.msag.hop -1
	 		self.neighbor3 = copy.copy(self.newneighbor)

		
 def timeAdvance(self):
   	return self.SIGMA


 def outputFnc(self):
	if (self.PHASE == "BUSY"):
		#self.FiFo.append(Message (self.myName,"" ,"", 125, "WhiteFlag", 0, 0, 0, 1, 2, 0, "", 90))
		self.msgout = self.FiFo.pop(0)
		if (self.msgout.typ == "ACK"):
			self.msgWF0 = copy.copy(self.msgout)
			self.msgWF0.typ = "WhiteFlag"
			self.msgWF0.destination =""
			#self.msgWF1 = copy.copy(self.msgout)
			#self.msgWF1.typ = "WhiteFlag"
			#self.msgWF1.destination =""
			#self.msgWF2 = copy.copy(self.msgout)
			#self.msgWF2.typ = "WhiteFlag"		
			#self.msgWF2.destination =""			
			self.FiFo.append(self.msgWF0)
			#self.FiFo.append(self.msgWF1)
			#self.FiFo.append(self.msgWF2)
			self.poke(self.OUT1, self.msgout)
		elif (self.msgout.typ != "ACK"): 
			self.poke(self.OUT1, self.msgout)
	elif (self.PHASE == "VIDE"):
		self.msgout = self.FiFo.pop(0)
		if (self.msgout == None) & (len(self.FiFo) == 0) :
			self.poke(self.OUT1,  Message (self.myName,"" ,"", 125, "WhiteFlag", 0, 0, 0, 1, 2, 0, "", 90))
		else :
			self.poke(self.OUT1, self.msgout)	
 def intTransition(self):
	if (self.PHASE == "BUSY"):
		self.changeState()
	if (self.PHASE == "VIDE"):
		self.changeState()
		
 def changeState (self, phase="FREE", sigma=__INFINITY__):
	self.PHASE = phase
	self.SIGMA = sigma
		
 def __str__(self):
  return (self.myName,"Net",len(self.FiFo), self.PHASE, self.neighbor1, self.neighbor2, self.neighbor3)

###################################