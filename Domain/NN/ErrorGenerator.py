# -*- coding: utf-8 -*-

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.NN.Object import Message
import random
import math
import numpy
import array

### Model class ----------------------------------------------------------------
class ErrorGenerator(DomainBehavior):
	
	def __init__(self, stop_learning_factor = 0.0, stop_error_factor = 0.0):
		""" Constructor

				@param stop_learning_factor = descr1
				@param stop_error_factor = descr2
		"""
		DomainBehavior.__init__(self)
		self.state = {	'status': 'Idle', 'sigma':INFINITY}
		self.stop_learning_factor = stop_learning_factor
		self.stop_error_factor = stop_error_factor
		self.current_pattern = 0
		self.current_validation_pattern = 0
		self.iteration  = 0
		self.validation_iteration = 0
		self.input_list = array.array('d',[])
		self.input_list_validation = array.array('d',[])
		self.errors = numpy.array([])
		self.errors_validation = array.array('d',[])
		self.output_targets = []
		self.output_validation_targets = []
		self.globalerror = 0.0
		self.globalerror_validation = 0.0
		self.lastglobalerror = 10.0
		self.globalerrordiff = array.array('d',[])
		self.first_time = True
		self.msg = None

	def extTransition(self):
		### initialisation.
		if self.first_time:
			self.first_time = False
			self.errors = numpy.zeros(len(self.IPorts)-2,float)
			self.errors_validation = numpy.zeros(len(self.IPorts)-2,float)
			self.input_list = numpy.zeros(len(self.IPorts)-2,float)
			self.input_list_validation = numpy.zeros(len(self.IPorts)-2,float)
			self.output_targets = []
			self.output_validation_targets = []

		for port, msg in self.peek_all():
			i = port.myID
			self.msg = msg
			
			if i > 1:
				self.input_list[i-2] = msg.value[0]
				self.input_list_validation[i-2] = msg.value[1]
			else:
				v = map(float,msg.value[0])
				if i == 0:
					self.output_targets.append(v)
					break
				else:
					self.output_validation_targets.append(v)
					break
			
		if i > 1:
			self.run()
			self.state = {'status': 'ACTIVE' , 'sigma': 0}
	
	def outputFnc(self):
		#assert(self.msg != None)

		#self.msg.value = self.errors
		#self.msg.time = self.timeNext
		### list of errors for each output sent to the training phase.
		self.poke(self.OPorts[3], Message(self.errors, self.timeNext))
		
		if self.current_validation_pattern == len(self.output_validation_targets)-1:
			self.poke(self.OPorts[2], Message([self.globalerror_validation], self.timeNext))
		
		### global error output for all patterns to see how the training phase goes.
		if self.current_pattern == len(self.output_targets)-1:
			self.poke(self.OPorts[1], Message([self.globalerror], self.timeNext))
			
			### learning stop conditions.
			l = len(self.globalerrordiff)
			s = sum(self.globalerrordiff[(l-20):])/20.0
			if s < self.stop_learning_factor and self.globalerror < self.stop_error_factor:
				self.poke(self.OPorts[0], Message(self.globalerrordiff, self.iteration))
				
				self.poke(self.OPorts[3], Message(["trained"], self.iteration))

	def intTransition(self):
		
		### patterns counter.
		if self.current_validation_pattern == len(self.output_validation_targets)-1:
			self.current_validation_pattern = 0
			self.globalerror_validation = 0
		else:
			self.current_validation_pattern += 1
			
		if self.current_pattern == len(self.output_targets)-1:
			self.current_pattern = 0
			#self.globalerror_validation = 0
			self.globalerror = 0
		else:
			self.current_pattern += 1
			
		self.state = {'status':'Idle', 'sigma':INFINITY}
	
	def timeAdvance(self):
		return self.state['sigma']
	
	def run(self):
		
		### The error for each output.
		self.errors = self.output_targets[self.current_pattern] - self.input_list
		
		### Global error fucntion. 
		a = 0.5*(self.errors*self.errors)
		self.globalerror += a.sum(axis=0)
		### If the test patterns exist we will calculat their output too.
		if self.output_validation_targets != []:
			self.errors_validation = self.output_validation_targets[self.current_validation_pattern] - self.input_list_validation
		
			b = 0.5*(self.errors_validation*self.errors_validation)
			self.globalerror_validation += b.sum(axis=0)
			
			### validation's iteration counter
			if self.current_validation_pattern == len(self.output_validation_targets)-1:
				self.validation_iteration += 1

		### iteration counter and calculator of the stop conditon 
		if self.current_pattern == len(self.output_targets)-1:
			self.iteration += 1
			self.globalerrordiff.append(abs(self.lastglobalerror - self.globalerror))
			#self.globalerrordiff.pop()
			self.lastglobalerror = self.globalerror