# -*- coding: utf-8 -*-

"""
Name : AM_BaseStation.py
Brief descritpion : Atomic Model to represent origin of network.
Author(s) :Thierry Antoine-Santoni
Version :  1.0                                        
Last modified : 
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

__CLOCK__	= 0

import sys, os
import copy

from DomainInterface.DomainBehavior import DomainBehavior
from Message import Message

import pyXLWriter as xl

#    ======================================================================    #
class BaseStation(DomainBehavior):
	""" class description....
	
	"""
	def __init__(self, Node = 0):
		"""	
			constructor
			
			@param Node = node name
		"""
		
		DomainBehavior.__init__(self)
		
		self.myName = "BaseStation"
		self.PHASE = "IDLE"
		self.SIGMA = 0	 

		self.nodes = Node
		self.nodeList = []
		
		self.msgIn1 = Message()
		
		self.FiFo = []
		
		self.row = 2
		self.column = 0
		self.count = 0

		# results file
		self.fileName = "Generator.xls"
		self.file = file(self.fileName, "w")
		
	def extTransition(self):
		
		self.msgIn1 = self.peek(self.IPorts[0])
		self.msgFiFo = copy.copy(self.msgIn1)
		if (self.msgFiFo.origin != self.msgFiFo.parent) :
			self.FiFo.append ( [self.msgFiFo.origin, self.msgFiFo.sender, self.msgFiFo.typ, self.msgFiFo.parent , self.count, self.timeLast, self.timeNext])

		#open file
		self.file = file(self.fileName, "wb")
		self.workbook = xl.Writer(self.file)
		self.worksheet = self.workbook.add_worksheet('Results')
		self.worksheet.set_column([0, 20], 20)

		self.heading = self.workbook.add_format(bold = 0.1,
						color = 'black',
						size = 10,
						merge = 1,
						align = 'vcenter' )
		self.headings = ('Origin', 'Sender','Message_Typ', 'Parent', 'COMPTEUR', 'timeLast', 'timeNext')
		self.worksheet.write_row('A1', self.headings, self.heading)

		# write file
		for i in range(len(self.FiFo)):
			self.worksheet.write_row('A'+str(i+2),self.FiFo[i], self.heading)

		#close file
		self.workbook.close()

		self.row+=1
		self.count+=1
		self.i = 0
		self.j = 0
		
		print "BASESTATION", self.PHASE, self.count
		
		if (self.msgIn1 != None) and (self.PHASE == "IDLE"):
			if (self.msgIn1.typ == "ACK"):
				self.msgIn1.typ = "OK"

				self.msgIn1.destination = self.msgIn1.sender
				self.msgIn1.origin = "BS"
				self.msgIn1.sender = "BS"
				self.changeState ("OK",0.004)
			elif (self.msgIn1.typ == "WhiteFlag"):
				self.msgIn1.typ = "Update"
				self.msgIn1.destination = self.msgIn1.sender
				self.msgIn1.origin = "BS"
				self.msgIn1.sender = "BS"			
				self.msgIn1.hop = 0
				self.changeState ("BUSY", 0.004)
					
	def outputFnc(self):
		if (self.PHASE == "FREE"):
			self.poke(self.OPorts[0],  Message(["BS","BS" ,"BS","", 125, "WhiteFlag", 0, 0, 0, 1, 2, 0, "", 100,""], self.timeNext))
		elif (self.PHASE == "OK"):
			self.poke(self.OPorts[0],  self.msgIn1)
		elif (self.PHASE == "BUSY"):
			self.poke(self.OPorts[0], self.msgIn1)

	def intTransition(self):
		if (self.SIGMA == __CLOCK__) and (self.PHASE == "IDLE") :
			self.changeState("FREE", 0)
			__CLOCK__+0.004
		elif (self.PHASE =="FREE"): 
			self.changeState("IDLE", INFINITY)
		elif (self.PHASE == "OK"): 
			self.changeState ("IDLE", INFINITY) #self.SIGMA+1
		elif (self.PHASE == "BUSY"): 
			self.changeState ("IDLE", INFINITY)
	  
	def changeState (self, phase ="FREE", sigm=INFINITY):
		self.PHASE = phase
		self.SIGMA = sigm
	  
	def timeAdvance(self):
		return self.SIGMA
		
	def __str__(self):
		return ("BASESTATION",len(self.FiFo), self.PHASE,self.msgIn1.typ)