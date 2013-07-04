# -*- coding: utf-8 -*-

"""
Name: DRIV.py

Author(s): 
Version: 0.1
Last modified: 09/03/2011 
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS: port 0 Temp and port 1 Precip
"""

from DomainInterface.DomainBehavior import DomainBehavior 

class DRIV(DomainBehavior):
	"""
	"""

	def __init__(self,rule=""):
		"""
		"""
		
		DomainBehavior.__init__(self)
			
		self.state = {'status':'IDLE','sigma':INFINITY}
		
		### conversion rule
		self.conv_rule = rule
		### conversion process
		self.conv_value = None
		### list des msg sur les ports de result
		self.msgList=[None]*10
		
		self.conv_msg = None
		self.req_msg = None
		
	###
  	def intTransition(self):
		# Changement d'etat
		self.changeState()

	###
	def extTransition(self):
		
		self.msgList = self.msgList[0:len(self.IPorts)-2]
		
		self.req_msg = self.peek(self.IPorts[0])
		self.conv_msg = self.peek(self.IPorts[1])
		
		#self.debugger("req"+str(self.req_msg))
		#self.debugger("conv"+str(self.conv_msg))

		### si request alors on demande au sto les valeurs
		if self.req_msg != None:
			self.changeState('REQ',0.0)
		elif self.conv_msg != None:
			###TODO faire regle de conv avec eval proprement
			self.conv_value = self.conv_msg.value[0]
			self.changeState('CONV',0)	
			#self.conv_value = eval(str(self.conv_rule)+"%"+str(conv.value[0]))
		else:
				
			for i in range(2,len(self.IPorts)):
				msg = self.peek(self.IPorts[i])
				if msg != None:
					self.msgList[i-2] = msg
			
			if None not in self.msgList:
				self.changeState('INPUTS',0.0)
			else:
				self.changeState()

			#self.debugger("list"+str(self.msgList))
			
			
	###
  	def outputFnc(self):
		
		if self.state["status"] == 'REQ':
			self.req_msg.value[0] = "give me"
			self.req_msg.time = self.timeNext
			self.poke(self.OPorts[0], self.req_msg)
		elif self.state["status"] == 'CONV':
			self.conv_msg.value[0] = self.conv_value
			self.conv_msg.time = self.timeNext
			self.poke(self.OPorts[1], self.conv_msg)
		elif self.state["status"] == 'INPUTS':
			for i,msg in enumerate(self.msgList):
				self.poke(self.OPorts[2+i], msg)
			self.msgList=[None]*len(self.IPorts)
	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status']=status
		self.state['sigma']=sigma

	def __str__(self):return "DRIV"