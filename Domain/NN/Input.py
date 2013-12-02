"""
	This model represents the input layer of an artificiel neural network
	@author: Samuel TOMA
	@organization: University of Corsica
	@contact: toma@univ-corse.fr
	@since: 2010.12.10
	@version: 1.3
"""
	
### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.NN.Object import Message

import numpy

###import random
###import math

### Model class ----------------------------------------------------------------
class Input(DomainBehavior):
	""" Input Layer model

		3 input ports:
			- to stop simulation depending to the error manager
			- Learning input
			- Test input
		Number of output depends of the input number
		
	"""
	
	def __init__(self):
		""" Construtor
		"""
		
		DomainBehavior.__init__(self)

		self.state = {'status': 'Idle', 'sigma':INFINITY}
		#self.mode = "training"
		self.dt = INFINITY
		self.current_pattern = 0
		self.current_validation_pattern = 0
		self.training_patterns = []
		self.validation_patterns = []
		
	def extTransition(self):
		
		for port, msg in self.peek_all():
			i = port.myID
			if i == 0:
				self.current_pattern = 0
				self.state = {'status': 'IDLE', 'sigma':INFINITY}
			elif i == 1:
				self.training_patterns.append(msg.value[0])
				self.dt = 1.0/len(self.training_patterns)
				self.state = {'status': 'ACTIVE', 'sigma':self.dt}
			elif i == 2:
				self.validation_patterns.append(msg.value[0])
				self.state = {'status': 'ACTIVE', 'sigma':self.dt}
			
	def outputFnc(self):
		for i in xrange(len(self.training_patterns[self.current_pattern])):
			#self.msg.value = [	float(self.training_patterns[self.current_pattern][i]),
							#float(self.validation_patterns[self.current_validation_pattern][i]) if self.validation_patterns != [] else 0.0,
							#0.0]
			#self.msg.time = self.timeNext
			
			msg = Message([	float(self.training_patterns[self.current_pattern][i]),
							float(self.validation_patterns[self.current_validation_pattern][i]) if self.validation_patterns != [] else 0.0,
							0.0], self.timeNext)
			self.poke(self.OPorts[i], msg)

	def intTransition(self):

		self.current_pattern += 1
		if self.current_pattern >= len(self.training_patterns):
			self.current_pattern = 0
			
		self.current_validation_pattern += 1
		if self.current_validation_pattern >= len(self.validation_patterns):
			self.current_validation_pattern = 0
				
	def timeAdvance(self):
		return self.state['sigma']
		