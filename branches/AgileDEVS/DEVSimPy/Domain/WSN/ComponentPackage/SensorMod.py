# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AM_Networh..py --- Atomic Model to represent network mangement in a sesnornode
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

from DEVSKernel.DEVS import CoupledDEVS
from Tools.Generator import GeneratorEnv
from Tools.Message import Message
from  ComponentPackage.AM_COM import COM 
from  ComponentPackage.AM_Battery import Battery 
from  ComponentPackage.AM_Memory import Memory 
from  ComponentPackage.AM_Flash import Flash 
from  ComponentPackage.AM_Processor  import Processor 
from  ComponentPackage.AM_SensorBoard  import SensorBoard 
from RoutingPackage.AM_Net import Net



###################################################################################################################
class Node(CoupledDEVS) :
	
 def __init__(self, Nome= 'rien', iPort=0, oPort=0): #affectation d'un nom pour pouvoir reperer les noeuds durant la simulation
	CoupledDEVS.__init__(self)
	self.SIGMA =__INFINITY__
	
	# local copy
	self.Name = Nome
	self.iPort=iPort
	self.oPort=oPort
	
	#cretation  port
	self.inPortList = [None, None, None, None]
	self.outPortList = [None, None, None, None] 
 	for ip in range(self.iPort):
		self.inPortList[ip] = self.addInPort()
	for op in range(self.oPort):
		self.outPortList[op] = self.addOutPort()


	self.GeneratorEnv	= self.addSubModel(GeneratorEnv())

	self.Com	= self.addSubModel(COM(self.Name, self.iPort, self.oPort))
	self.Process	= self.addSubModel(Processor(self.Name))
	self.Battery	= self.addSubModel(Battery(self.Name))
	self.Memory	= self.addSubModel(Memory(self.Name))
	self.Net	= self.addSubModel(Net(self.Name, self.iPort, self.oPort ))
	self.Flash	= self.addSubModel(Flash(self.Name))
	self.SensorBoard	= self.addSubModel(SensorBoard(self.Name))
	
	#declare EIC
	#self.connectPorts(self.COM.OUT2, self.Process.IN1)
	#self.connectPorts(self.Generator.OUT1, self.COM.IN1)
	#self.connectPorts(self.Generator.OUT1, self.COM.IN1)
	#self.connectPorts(self.IN3, self.Process.IN3)
	#self.connectPorts(self.IN4, self.Process.IN4)
	
	#declare IC
	
	#for i in range(self.iPort):
		#self.connectPorts(self.IPorts[i], self.Com.IPorts[i])
		
	for ip in range(self.iPort):
		self.connectPorts(self.inPortList[ip], self.Com.inPortList[ip])
	self.connectPorts(self.Process.OUT1, self.Com.INProcess)
	self.connectPorts(self.Process.OUT2, self.SensorBoard.IN1)
	self.connectPorts(self.Process.OUT3,self.Net.IN1) 
	self.connectPorts(self.Process.OUT4, self.Flash.IN1)
	self.connectPorts(self.Process.OUT5, self.Memory.IN1)
	self.connectPorts(self.Process.OUT6, self.Battery.IN1)
	self.connectPorts(self.Com.OUTBattery, self.Battery.IN2)
	self.connectPorts(self.Com.OUTProcess, self.Process.IN1)
	self.connectPorts(self.Battery.OUT1, self.Process.IN2)
	self.connectPorts(self.SensorBoard.OUT1, self.Process.IN3)
	self.connectPorts(self.SensorBoard.OUT2, self.Battery.IN3)
	self.connectPorts(self.Memory.OUT1, self.Process.IN4)
	self.connectPorts(self.Net.OUT1,self.Process.IN5)	
	self.connectPorts(self.Flash.OUT1, self.Process.IN6)
	self.connectPorts(self.GeneratorEnv.OUT1, self.SensorBoard.IN2)
	
	
	#declare EOC
	for ip in range(self.iPort):
		self.connectPorts(self.Com.outPortList[ip], self.outPortList[ip])

##################################################################################################################

