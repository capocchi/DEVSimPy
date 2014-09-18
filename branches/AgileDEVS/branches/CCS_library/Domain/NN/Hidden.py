# -*- coding: utf-8 -*-

"""
	This model represents the Hidden layer of an artificiel neural network
	@author: Samuel TOMA
	@organization: University of Corsica
	@contact: toma@univ-corse.fr
	@since: 2010.12.10
	@version: 1.5
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.NN.Object import Message
from random import random, randint
#from numpy import array, zeros
import array
import math
import shelve
import os
import sys

### Model class ----------------------------------------------------------------
class Hidden(DomainBehavior):
	""" Hidden Layer

	"""
	def __init__(self, 	bias = 0.5,
						activation_function = ("sigmoide","tanh","lineaire"),
						k = 1.0,
						a = -0.5,
						b = 0.5,
						fileName = os.path.join(os.getcwd(),"weights_%d"%randint(1,100)),
						learning_flag = True):
		""" constructor.
			@param bias 				= the bias value of hidden layer.
			@param activation_function 	= the type of the activation function.
			@param k					= param. of sigmoide activation function.
			@param a					= weight initialization range [a,b]
			@param b					= weight initialization range [a,b]
			@param fileName 			= weights file
			@param learning_flag		= model status \n if true model write its weights at the end of simulation into a file then it read weights file
		"""
		DomainBehavior.__init__(self)
		
		self.state = {'status': 'ACTIVE', 'sigma':0.0}
		self.bias = bias
		### if activation_function is tuple, then we should choose the first item
		self.activation_function = activation_function[0]
		self.k = k
		self.a = a
		self.b = b
		self.inputs = None
		self.outputs = None
		self.validation_in = None
		self.validation_out = None
		self.wh = None
		self.msgList = []
		self.fileName = fileName
		self.learning_flag = learning_flag

	def extTransition(self):
		#### apres avec pruning il faut que ca soit dynamique ca veut dire en fonction de inputs.

		i=0
		for port,msg in self.peek_all():
			i = port.myID
			if i == (len(self.IPorts)-1):
				### Update the weight list from DeltaOuput_Weight.
				#### ajouter la verification de la modification de pruning
				self.wh = msg.value[0]
				i = -1
				break
			else:
				### receiving inputs.
				self.inputs[i] = msg.value[0]
				self.validation_in[i] = msg.value[1]
				
		### after receiving all inputs then go to calculate and propagate the output throught the netwok.
		if i>=0:
			self.update()
			self.state = { 'status':'ACTIVE','sigma': 0.0 }
			
	def outputFnc(self):
		### first time sending the parameter to the learning phase.
		if self.inputs == None and self.wh != None:
			msg = self.msgList[0]
			#msg = Message([self.wh, self.activation_function, 0.0],self.timeNext)
			msg.value = [self.wh, self.activation_function, 0.0]
			msg.time = self.timeNext
			#msg = msg._replace(value=[self.wh, self.activation_function, 0.0], time=self.timeNext)
			self.poke(self.OPorts[len(self.OPorts)-1], msg)

		### propagation of the layer's output throught the network.
		elif self.inputs != None:
			if self.outputs[0] == 10.0:
				### sending initialised weights 
				msg = self.msgList[-1]
				msg.value = [self.wh, self.activation_function, True]
				msg.time = self.timeNext
				#msg = Message([self.wh, self.activation_function, True], self.timeNext)
				#msg = msg._replace(value=[self.wh, self.activation_function, True], time=self.timeNext)
				self.poke(self.OPorts[len(self.OPorts)-1], msg)
			else:
				for i in xrange(len(self.outputs)):
					msg = self.msgList[i]
					assert(msg is not None)
					msg.value = [self.outputs[i],self.validation_out[i],0.0]
					msg.time = self.timeNext
					#msg = msg._replace(value=[self.outputs[i],self.validation_out[i],0.0], time=self.timeNext)
					self.poke(self.OPorts[i], msg)
					
				msg = self.msgList[-1]
				assert(msg is not None)
				msg.value = [[self.inputs,self.outputs],self.activation_function,0.0]
				msg.time = self.timeNext
				#msg = msg._replace(value=[[self.inputs,self.outputs],self.activation_function,0.0], time=self.timeNext)
				self.poke(self.OPorts[len(self.OPorts)-1], msg)
	
	def intTransition(self):
		if self.wh == None:
			### weights manager
			if self.learning_flag:
				self.wh = [[ self.rand(self.a, self.b) for i in range(len(self.OPorts)-1)] for j in range(len(self.IPorts)-1)]
			elif os.path.isfile(self.fileName+'.db'):
				s = shelve.open(self.fileName+".db", flag='r')
				self.wh = s['w']
				s.close()
			else:
				sys.stderr.write("Go back to the learning phase to build weights file")
				self.state = {'status': 'Idle', 'sigma':INFINITY}
				
			
			### initialisation.
			self.inputs = array.array('f',[10.0]*(len(self.IPorts)-1))
			self.validation_in = array.array('f',[10.0]*(len(self.IPorts)-1))
			self.outputs = array.array('f',[10.0]*(len(self.OPorts)-1))
			self.validation_out = array.array('f',[10.0]*(len(self.OPorts)-1))
			self.msgList = [Message(None,None) for i in xrange(len(self.outputs)+1)]
			
			### activation only for the first time to send the initialized weight list to DeltaOutput_Weight
			self.state = {'status': 'ACTIVE', 'sigma':0.0}
		else:
			
			self.state = {'status': 'Idle', 'sigma':INFINITY}
	
	def rand(self,a,b):
		return (b-a)*random() + a
	
	def timeAdvance(self):
		return self.state['sigma']
	
	def update(self):
		
		### calculate the sum and then go throw the activation function. (layer forward calculation)
		for i in xrange(len(self.outputs)):
			s = sum([self.inputs[j]*self.wh[j][i] for j in range(len(self.IPorts) - 1)])
			s_validation = sum([self.validation_in[j]*self.wh[j][i] for j in range(len(self.IPorts) - 1)])
			self.outputs[i] = self.activation(s+self.bias)
			self.validation_out[i] = self.activation(s_validation+self.bias)
	
	def activation(self,x,k=1.0):
		### activation Functions.
		if self.activation_function == "tanh":
			return math.tanh(x)
		elif self.activation_function == "sigmoide":
			return 1.0/(1.0+math.exp(float(k)*(-float(x))))
		else:
			if x>1:				#lineaire
				return 1.0
			elif x<0:
				return 0.0
			else: 
				return x

	def finish(self, msg):
		""" optional method to control the the behavior when simulation finished
		"""
		if self.learning_flag:
			### write weights to file
			try:
				s = shelve.open(self.fileName+".db")
				s['w'] = self.wh
			finally:
				s.close()
			
	def __str__(self): return 'Hidden'