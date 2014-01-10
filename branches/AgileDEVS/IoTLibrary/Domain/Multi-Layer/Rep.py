# -*- coding: utf-8 -*-

"""
Name: Rep.py

Author(s): 
Version: 0.1
Last modified: 09/03/2011 
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS: port 0 Temp and port 1 Precip
"""

from DomainInterface.DomainBehavior import DomainBehavior 

class Rep(DomainBehavior):
	"""
	"""

	def __init__(self):
		"""
		"""
		
		DomainBehavior.__init__(self)
	
		#self.prec = None
		#self.temp = None
		
		self.state = {'status':'IDLE','sigma':INFINITY}
		
		self.msgList = [None]*10
	###
  	def intTransition(self):
		# Changement d'etat
		self.changeState()

	###
	def extTransition(self):
		
		self.msgList = self.msgList[0:len(self.IPorts)]
		
		temp = self.peek(self.IPorts[0])
		prec = self.peek(self.IPorts[1])
		
		if temp != None:
			self.msgList[0] = temp
		if prec != None:
			self.msgList[1] = prec 
		
		### tentative de sortie que si la temperature et la precipitation sont présentes
		if None not in self.msgList:
			# changement d'etat
			self.changeState('ACTIF',0)
		else:
			self.changeState()
		
	###
  	def outputFnc(self):		
		assert(None not in self.msgList)

		### préparation de la valeur de stockage
		if self.msgList[0].value[0] < 0.0:
			self.msgList[0].value[0] = self.msgList[1].value[0]
			self.msgList[0].time = self.timeNext
		
			# envoie du message sur les ports de sortie
			self.poke(self.OPorts[0], self.msgList[0])
		else:
			self.msgList[0].value[0] = 0.0
			self.msgList[0].time = self.timeNext
		
			# envoie du message sur les ports de sortie
			self.poke(self.OPorts[0], self.msgList[0])
			
	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status']=status
		self.state['sigma']=sigma

	def __str__(self):return "Rep"