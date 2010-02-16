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
	
import pyXLWriter as xl
	
from DEVSKernel.DEVS import AtomicDEVS
from Tools import *

class Battery(AtomicDEVS):


 def __init__(self, nodeName=None) :
 
	AtomicDEVS.__init__(self) 
	
	# results file
	self.fileName="Battery.xls"
	self.file = file(self.fileName, "wb")
	# local copy
	self.myName = nodeName
	self.FiFo = []
 #definition des variables d'etats
	self.PHASE  = "FREE"
	self.SIGMA =__INFINITY__

#declaration de variable de'énergie
	self.Count = 0
	
	self.Conso = 0
	self.TOTAL = 3000
	self.BatteryLT = 0
	self.value = 0
	self.timeProcess = 0.00004
	self.timeCOM = 0.001
	self.timeSB = 0.00004
	self.timeMemory = 0.00001
	#creation de port
	self.IN1  = self.addInPort() # message venant de Process
	self.IN2  = self.addInPort() # message veant de COM
	self.IN3  = self.addInPort() # message venat de SensorBoard
	self.IN4  = self.addInPort() #message venat de Memory
	self.IN5  = self.addInPort()
	self.OUT1 = self.addOutPort() #vers Porcess
	
 def extTransition(self):
	
	self.msg  = self.peek(self.IN1) # collecte des mesages en entrée 
	self.msg2  = self.peek(self.IN2)
	self.msg3  = self.peek(self.IN3)
	self.msg4  = self.peek(self.IN4)
	self.msg5 = self.peek(self.IN5)
	#open file
	self.file = file(self.fileName, "wb")
	self.workbook = xl.Writer(self.file)
	
	self.worksheet = self.workbook.add_worksheet('ConsoEnergy')

	self.worksheet.set_column([0, 20], 20)

	
	self.heading = self.workbook.add_format(bold = 0.1,
					color = 'black',
					size = 10,
					merge = 1,
					align = 'vcenter' )
	self.headings = ('Node', 'Conso')
	
	self.worksheet.write_row('A1', self.headings, self.heading)		
	
	if (self.msg != None) :
		self.ConsoProcess = self.msg
		self.TOTAL = self.TOTAL - (self.ConsoProcess*self.timeProcess)
		self.changeState("BUSY",__INFINITY__)
		self.value = self.calculBatterylife(self.TOTAL)
		self.FiFo.append ([self.myName, self.TOTAL])
	elif (self.msg2!= None) :
		self.ConsoCOM  = self.msg2
		self.TOTAL = self.TOTAL - (self.ConsoCOM*self.timeCOM)
		self.changeState("BUSY",__INFINITY__)
		self.value = self.calculBatterylife(self.TOTAL)
		self.FiFo.append ([self.myName, self.TOTAL])
	elif (self.msg3 != None) :
		self.ConsoSB  = self.msg3
		self.TOTAL = self.TOTAL - (self.ConsoSB*self.timeSB)
		self.changeState("BUSY",__INFINITY__)
		self.value = self.calculBatterylife(self.TOTAL)
		self.FiFo.append ([self.myName, self.TOTAL])
	elif (self.msg4 != None) :
		self.ConsoMemory  = self.msg4
		self.TOTAL = self.TOTAL - (self.ConsoMemory*self.timeMemory)
		self.changeState("BUSY",__INFINITY__)
		self.value = self.calculBatterylife(self.TOTAL)
		self.FiFo.append ([self.myName, self.TOTAL])
	elif (self.msg5 != None) :
		self.Conso  = self.msg5
		self.changeState("BUSY",__INFINITY__)
		self.value = self.calculBatterylife(self.TOTAL)
		self.FiFo.append ([self.myName, self.TOTAL])
	for i in range(len(self.FiFo)):
		if (self.FiFo[i][1] == "node1"):
			self.worksheet.write_row('A'+str(i+2),self.FiFo[i], self.heading)
	self.workbook.close()
		
 def timeAdvance(self):
   return self.SIGMA
 
 def outputFnc(self):
	if (self.TOTAL == 0):
		self.poke(self.OUT1, self.msg)
		
 def intTransition(self):
	if (self.PHASE == "BUSY"):
		self.changeState("FREE", __INFINITY__)	
 
 def changeState (self, phase="FREE", sigma=__INFINITY__):
	self.PHASE = phase
	self.SIGMA = sigma 
	
 def calculBatterylife(self, total):
	self.BatteryLT = (((total / 0.2369) /24)/30)

 def __str__(self):
	return (self.myName,"Battery", self.PHASE, self.TOTAL, self.BatteryLT, self.FiFo)