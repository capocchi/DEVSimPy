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
from random import *
for spath in [os.pardir+os.sep+'Library']:
	if not spath in sys.path: sys.path.append(spath)

import pyXLWriter as xl

global workbook
global worksheet
global heading, headings



workbook = xl.Writer("Net_Node.xls")
worksheet = workbook.add_worksheet('Results')
worksheet2 = workbook.add_worksheet('Results2')
worksheet3 = workbook.add_worksheet('Results3')
worksheet4 = workbook.add_worksheet('Results4')
worksheet.set_column([0, 24], 20)
worksheet2.set_column([0, 24], 20)
worksheet3.set_column([0, 24], 20)
worksheet4.set_column([0, 24], 20)
heading = workbook.add_format(bold = 0.1,
                               color = 'black',
                               size = 10,
                               merge = 1,
				align = 'vcenter' )
headings = ('Origin', 'Message_Typ')
worksheet.write_row('A1', headings, heading)	
worksheet2.write_row('A1', headings, heading)	
worksheet3.write_row('A1', headings, heading)	
worksheet4.write_row('A1', headings, heading)		
from Tools.Message import Message	
from DEVSKernel.DEVS import AtomicDEVS

class Net(AtomicDEVS):

 def __init__(self, nodeName=None, iPort=0, oPort=0 ) :
 
	AtomicDEVS.__init__(self) 
	#definition des variables d'etats
	self.PHASE  = "FREE"
	self.SIGMA = __INFINITY__
	self.myName =nodeName
	self.iPort=iPort
	self.oPort=oPort
 	self.outPortList = ["1", "2", "3", "4"]
	self.IN1  = self.addInPort() # message venant de process
	self.OUT1 = self.addOutPort() #message vers process
	
	self.newneighbor = ["","", 0,"newneigbor",0,1000000,""]
   	self.neighbor1  =["","",0,"neigbor1",0,1000000,""] # name,parent, link quality, nom, frequency, hop, port
	self.neighbor2 = ["","",0,"neigbor2",0,1000000,""]
	self.neighbor3 = ["","",0,"neigbor3",0,1000000,""]
	self.neighbor4= ["","",0,"neigbor4",0,1000000,""]
	self.FiFo = []
	self.FiFobis = []
	self.count = 0
	self.column = 0
	self.row = 2
	self.counter = 0
	self.row2 = 2
	self.counter2 = 0
	self.row3 = 2
	self.counter3 = 0
	self.row4 = 2
	self.counter4 = 0
	self.voisin = [[self.neighbor1], [self.neighbor2], [self.neighbor3], [self.neighbor4]]
	
 def extTransition(self):
	self.msg  = self.peek(self.IN1) # collecte des messages en entrée 
	self.i = 0
	self.j = 0
	self.counting = 0
	print 'Net', self.myName, self.voisin
	if (self.msg != None) & (self.PHASE == "FREE"):
		if (self.msg.typ == "router"):
			self.changeState("BUSY", 0)
			self.msg.destination = self.neighbor1[0]
			self.msg.hierarchy = self.neighbor1[2]
			self.msg.sender = self.myName
			self.FiFo.append(self.msg)
		elif (self.msg.typ == "Update"):
			if (self.msg.destination == self.myName) :
				self.changeState("BUSY", 0)
				self.upDatelk (self.msg)
			else :
				self.msg.sender = self.myName
				self.FiFo.insert(0,self.msg)
				self.changeState("BUSY", 0)
		elif (self.msg.typ == "WhiteFlag"):
			#self.msg.TraceBack[self.msg.hop] = self.myName
			self.upDatelk (self.msg)
			self.msgACK = Message()
			self.msg.hop +=1
			self.msg.Port = ""
			self.msgACK.origin = self.msg.origin
			self.msg.sender = self.myName
			self.msgACK.hop = self.msg.hop
			self.msgACK.typ = "ACK"
			self.msgACK.parent = self.myName
			self.msgACK.destination =self.neighbor1[0]
			self.msgACK.sender = self.myName
			self.msg.destination =""
			self.changeState("BUSY",0)
			self.FiFo.append(self.msgACK)
			for ip in range(self.iPort):	
				self.msgWF = copy.copy(self.msg)
				self.msgWF.Port = self.outPortList[ip]
				self.FiFo.append(self.msgWF)
			for ip in range(self.iPort):	
				self.msgWF = copy.copy(self.msg)
				self.msgWF.origin = self.myName
				self.msgWF.Port = self.outPortList[ip]
				self.FiFo.append(self.msgWF)

		elif (self.msg.typ == "ACK"):
			if (self.msg.destination == self.myName):
				self.upDatelk (self.msg)
				self.msg.hop +=1
				self.msg.destination = self.neighbor1[0]
				self.msg.sender = self.myName				
				self.FiFo.insert(0,self.msg)
				self.changeState("BUSY",0)
				self.changeState("BUSY",0)
			else :
				self.msg.hop +=1
				self.msg.destination = self.neighbor1[0]
				self.msg.sender = self.myName				
				self.FiFo.insert(0,self.msg)
				self.changeState("BUSY",0)
		elif (self.msg.typ == "OK"):
			if (self.msg.destination == self.myName):
				self.changeState("BUSY",0)
			else :
				self.msg.origin = self.myName
				self.msg.sender = self.myName				
				self.FiFo.insert(0,self.msg)
				self.changeState("BUSY",0)	
		
	
	
			
 def upDatelk (self,msge = Message()):
	self.msag = msge
	if (self.msag.sender == self.neighbor1[0]):
		self.neighbor1[4] +=1		# mise à jour de la fréquence
	elif (self.msag.sender == self.neighbor2[0]):
		self.neighbor2[4] +=1
	elif (self.msag.sender == self.neighbor3[0]):
		self.neighbor3[4] +=1
	elif (self.msag.sender== self.neighbor4[0]):
		self.neighbor4[4] +=1
	elif (self.msag.sender != self.neighbor1[0]) or (self.msag.sender[0] != self.neighbor2) or (self.msag.sender[0] != self.neighbor3) or (self.msag.sender[0] != self.neighbor4):#test de la table
		if (self.msag.hop < self.neighbor1[5]) : # nouvel arrivant classé par sa connetivité
			self.newneighbor[0] = self.msag.sender
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor1"
			self.newneighbor[5] = self.msag.hop-1
			self.newneighbor[6] = "1"
			self.data11 = copy.copy(self.neighbor1)
			self.data1 = copy.copy(self.newneighbor)
			self.neighbor1 = copy.copy(self.newneighbor)
			self.data22 = copy.copy(self.neighbor2)
			self.neighbor2 = copy.copy(self.data11)
			self.data33 = copy.copy(self.neighbor3)
			self.neighbor3 = copy.copy(self.data22)
			self.data44 = copy.copy(self.neighbor4)
			self.neighbor4 = copy.copy(self.data33)
		elif (self.msag.hop == self.neighbor1[5]) & (self.msag.lkq > self.neighbor1[2]):
			self.newneighbor[0] = self.msag.sender
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor1"
			self.newneighbor[5] = self.msag.hop-1
			self.newneighbor[6] = "1"
			self.data11 = copy.copy(self.neighbor1)
			self.data1 = copy.copy(self.newneighbor)
			self.neighbor1 = copy.copy(self.newneighbor)
			self.data22 = copy.copy(self.neighbor2)
			self.neighbor2 = copy.copy(self.data11)
			self.data33 = copy.copy(self.neighbor3)
			self.neighbor3 = copy.copy(self.data22)
			self.data44 = copy.copy(self.neighbor4)
			self.neighbor4 = copy.copy(self.data33)
		elif (self.msag.hop < self.neighbor2[5]):
			self.newneighbor[0] = self.msag.sender
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor2"
			self.newneighbor[5] = self.msag.hop-1
			self.newneighbor[6] = "2"
			self.data22 = copy.copy(self.neighbor2)
			self.neighbor2 = copy.copy(self.newneighbor)
			self.data33 = copy.copy(self.neighbor3)
			self.neighbor3 = copy.copy(self.data22)
		elif (self.msag.hop == self.neighbor2[5]) & (self.msag.lkq > self.neighbor2[2]):
			self.newneighbor[0] = self.msag.sender
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor2"
			self.newneighbor[5] = self.msag.hop-1
			self.newneighbor[6] = "2"
			self.data22 = copy.copy(self.neighbor2)
			self.neighbor2 = copy.copy(self.newneighbor)
			self.data33 = copy.copy(self.neighbor3)
			self.neighbor3 = copy.copy(self.data22)
			self.data44 = copy.copy(self.neighbor4)
			self.neighbor4 = copy.copy(self.data33)
		elif (self.msag.hop < self.neighbor3[5]):
			self.newneighbor[0] = self.msag.sender
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor3"
			self.newneighbor[5] = self.msag.hop-1
			self.newneighbor[6] = "3"
	 		self.data33 = copy.copy(self.neighbor3)
			self.neighbor3 = copy.copy(self.newneighbor)
			self.data44 = copy.copy(self.neighbor4)
			self.neighbor4 = copy.copy(self.data33)
		elif (self.msag.hop == self.neighbor3[5]) & (self.msag.lkq > self.neighbor3[2]):
			self.newneighbor[0] = self.msag.sender
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor3"
			self.newneighbor[5] = self.msag.hop -1
			self.newneighbor[6] = "3"
	 		self.data33 = copy.copy(self.neighbor3)
			self.neighbor3 = copy.copy(self.newneighbor)
			self.data44 = copy.copy(self.neighbor4)
			self.neighbor4 = copy.copy(self.data33)
		elif (self.msag.hop < self.neighbor4[5]):
			self.newneighbor[0] = self.msag.sender
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor4"
			self.newneighbor[5] = self.msag.hop-1
			self.newneighbor[6] = "3"
			self.neighbor4 =  copy.copy(self.newneighbor)
		elif (self.msag.hop == self.neighbor3[5]) & (self.msag.lkq > self.neighbor3[2]):
			self.newneighbor[0] = self.msag.sender
			self.newneighbor[1] = self.msag.parent
			self.newneighbor[2] = self.msag.lkq
			self.newneighbor[3] = "neighbor4"
			self.newneighbor[5] = self.msag.hop -1
			self.newneighbor[6] = "4"
			self.neighbor4 =  copy.copy(self.newneighbor)

	self.voisin = [[self.neighbor1], [self.neighbor2], [self.neighbor3], [self.neighbor4]]	
	
 def timeAdvance(self):
   	return self.SIGMA


 def outputFnc(self):
	if (self.PHASE == "BUSY"):
		if (len(self.FiFo) != 0):
			self.msgout = self.FiFo.pop(0)
			self.poke(self.OUT1, self.msgout)
		"""else : 
			self.helpMessage = Message()
			self.helpMessage.Port = randrange(0,3)
			self.helpMessage.typ = "OK"
			self.poke(self.OUT1, self.helpMessage )"""
 def intTransition(self):
	if (self.PHASE == "BUSY"):
		self.changeState()
	if (self.PHASE == "VIDE"):
		self.changeState()
		
 def changeState (self, phase="FREE", sigma=__INFINITY__):
	self.PHASE = phase
	self.SIGMA = sigma
		
 def __str__(self):
  return (self.myName,"Net",len(self.FiFo), self.neighbor1, self.neighbor2, self.neighbor3, self.neighbor4, self.count)

###################################