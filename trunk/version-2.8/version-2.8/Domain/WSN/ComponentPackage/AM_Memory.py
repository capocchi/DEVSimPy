# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AM_Memory..py --- Atomic Model to represent Memory in a sesnornode
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
	
from DEVSKernel.DEVS import AtomicDEVS
from Tools import *


class Memory(AtomicDEVS):

 def __init__(self, nodeName=None) :
 
	AtomicDEVS.__init__(self) 
	
	# local copy
	self.myName = nodeName
	
 #definition des variables d'etats
	self.PHASE  = "FREE"
	self.SIGMA =__INFINITY__
	
#declaration de variables de gestion routage
	self.newdata = [1,10,10,10,0]
	self.data1 = [1,3,8,6,1]
	self.data2 = [1,3,8,6,2]
	self.data3 = [1,3,8,6,3]
	self.data4 = [1,3,8,6,4]
	self.data11 = []
	self.data22 = []
	self.data33 = []
	self.data44 = []
 #creation de port
	self.IN1  = self.addInPort() # message venant de Process
	self.OUT1 = self.addOutPort() #message vers Process


 def extTransition(self):
	self.msg  = self.peek(self.IN1) # collecte des mesages en entrée 
	if (self.msg != None) & (self.PHASE == "FREE"):
		if (self.msg.typ == "updata"):
			self.changeState ("BUSY",1, 0)
		elif (self.msg.typ == "MemCollect"):
			self.changeState ("BUSY",2, 0)
 

 	
	
 def timeAdvance(self):
   return self.SIGMA
 
 def outputFnc(self):
	if (self.PHASE == "BUSY") & (self.GO == 1):
		self.newData()
		self.upData()
	elif (self.PHASE == "BUSY") & (self.GO == 2):
		self.collectData()
  		self.poke(self.OUT1, self.msg)
		
 def collectData ():
	if (self.msg.hierarchy == self.data1[4]):
		self.msg.Temp = self.data1[0]
		self.msg.humidity = self.data1[1]
		self.msg.pressure = self.data1[2]
		self.msg.GPS = self.data1[3]
	elif (self.msg.hierarchy == self.data2[4]):
		self.msg.Temp = self.data2[0]
		self.msg.humidity = self.data2[1]
		self.msg.pressure = self.data2[2]
		self.msg.GPS = self.data2[3]
	elif (self.msg.hierarchy == self.data3[4]):
		self.msg.Temp = self.data3[0]
		self.msg.humidity = self.data3[1]
		self.msg.pressure = self.data3[2]
		self.msg.GPS = self.data3[3]
	elif (self.msg.hierarchy == self.data4[4]):
		self.msg.Temp = self.data4[0]
		self.msg.humidity = self.data4[1]
		self.msg.pressure = self.data4[2]
		self.msg.GPS = self.data4[3]
	
	

 def newData ():
	self.newdata [0] = self.msg.Temp
	self.newdata [1] = self.msg.humidity
	self.newdata [2] = self.msg.pressure
	self.newdata [3] = self.msg.GPS
	
 
 
 def upData (self):
	 self.data11 = copy.copy(self.data1)
	 self.data1 = copy.copy(self.newdata)
	 self.data22 = copy.copy(self.data2)
	 self.data2 = copy.copy(self.data11)
	 self.data33 = copy.copy(self.data3)
	 self.data3 = copy.copy(self.data22)
	 self.data44 = copy.copy(self.data4)
	 self.data4 = copy.copy(self.data33)

 
 def intTransition(self):
	 if (self.PHASE == "BUSY"):
	 	self.changeState()
 
 
 def changeState (self, phase="FREE",go = 0, sigma=__INFINITY__):
	self.PHASE = phase
	self.GO = go
	self.SIGMA = sigma
 
 
 
 def __str__(self):
  return (self.myName,"Memory", self.PHASE, self.data1, self.data2, self.data3, self.data4)
 