# -*- coding: utf-8 -*-

"""
Name : dam.py 
Brief descritpion : Dam atomic model 
Author(s) : L. Capocchi (capocchi@univ-corse.fr), J.F. Santucci (santucci@univ-corse.fr)
Version :  1.0
Last modified : 2011.06.01
GENERAL NOTES AND REMARKS:
		For each week, dam send three messages: leak for comsuption (0.0 or positive real), its content (H) and the overflowing (0.0 or positive real)
GLOBAL VARIABLES AND FUNCTIONS:
	WEEKS : number of week in order to control initalization of dam
"""


from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

class dam(DomainBehavior):
	"""
	"""

	def __init__(self, content=0.0, capacity=0.0):
		"""
			@content : initial water content of the dam (m3)
			@capacity : capacity of the dam (m3)
		"""
		DomainBehavior.__init__(self)

		### local copy
		self.content = content
		self.capacity = capacity
		
		assert(self.content <= self.capacity)
		
		self.state = {	'status': 'INFORM', 
						'sigma':0,
						'flowOpen':0.0
						}
		
		### overflowing quantity
		self.overflowing = 0.0
		self.init_content = self.content
		
		### current week
		self.week = 0
		
		### output messages
		self.msgGain = Message()
		self.msgConsumption = None
		
	def extTransition(self):

		msgGain, msgConsumption = map(self.peek, self.IPorts)
		
		#Gain
		if(msgGain != None):
			self.msgGain = msgGain
			gain = float(self.msgGain.value[0])
			self.week = msgGain.value[1]
			
			### overflowing test
			if gain+self.content < self.capacity:
				self.content += gain
				if self.content < 0:
					self.debugger("Error : negative value (content : %f, gain : %f)"%(self.content,gain))
				self.overflowing = 0.0
				self.state['status'] == "INFORM"
				self.debugger(" %s: filling of Dam %s!"%(str(self.msgGain.time),str(gain)))
			else:
				### full overflowing 
				if self.content == self.capacity:
					self.overflowing = gain
				### partial overflowing
				else:
					### quantity for completing dam
					a = self.capacity - self.content
					self.content = self.capacity
					self.overflowing = gain - a
					
				self.debugger("%s: overflowing !"%(str(self.msgGain.time)))
				self.state['status'] == "OVERFLOWING"
			
		#Consumption
		if(msgConsumption != None):
			self.msgConsumption = msgConsumption
			consumption = float(self.msgConsumption.value[0])
			self.week = self.msgConsumption.value[1]
			
			### consumption test
			if consumption > 0:
				self.state['flowOpen'] = consumption
				self.content -= self.state['flowOpen']
				self.overflowing = 0.0
				
				if  self.content < 0 :
					self.content = 0.0
					self.debugger("%s: empty Dam!"%(str(self.msgConsumption.time)))
				else:
					self.debugger("%s: comsuption from Dam !"%(str(self.msgConsumption.time)))
					
				self.state['status'] = "LEAK"
			
		self.state['sigma'] = 0
		
	def outputFnc(self):
	
		if self.state['status'] == "LEAK":
			self.msgConsumption.time = self.timeNext
			self.msgConsumption.value[0] = self.state['flowOpen']
		else:
			self.msgConsumption = Message([0.0, self.week, 0.0], self.timeNext)
		
		
		self.msgGain.value = [self.content, self.week, 0.0]
		self.msgGain.time = self.timeNext
		
		self.poke(self.OPorts[0], self.msgConsumption)
		self.poke(self.OPorts[1], self.msgGain)
		self.poke(self.OPorts[2], Message([self.overflowing, self.week, 0.0], self.timeNext))
                
	def intTransition(self):
		
		if self.week == 52 and self.timeNext != 0:
			### overflowing quantity
			self.overflowing = 0.0
			self.debugger("avant %f"%self.content)
			self.content = self.init_content
			self.debugger("apres %f"%self.content)
			
		self.state['sigma'] = INFINITY
        
	def timeAdvance(self): return self.state['sigma']
		
	def __str__(self): return "Dam"