# -*- coding: utf-8 -*-

"""
	This model represents the Hidden layer of an artificiel neural network
	@author: Samuel TOMA
	@organization: University of Corsica
	@contact: toma@univ-corse.fr
	@since: 2010.12.10
	@version: 3.0 beta
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
#from Object import Message, NeuralMessage
from Domain.Basic.Object import Message
from random import randint,seed,random
#import random
import math
#import shelve
import os
#import sys
#import copy
from Signature import Signature

### Model class ----------------------------------------------------------------
class Hidden(DomainBehavior):
	""" Hidden Layer
	"""
	def __init__(self, 	bias = 1.0,
						N = 0.9,
						M = 0.1,
						activation_f = ("tanh","sigmoid"),
						k = 1.0,
						a = -0.2,
						b = 0.2,
						fileName = os.path.join(os.getcwd(),"weights_%d"%randint(1,100)),
						learning_flag = True):
		""" constructor.
			@param bias 				= the bias value of hidden layer.
			@param activation_function 	= the type of the activation function.
			@param k					= param. for sigmoide activation function only.
			@param a					= weight initialization range [a,b]
			@param b					= weight initialization range [a,b]
			@param fileName 			= weights file
			@param learning_flag		= model status \n if true model write its weights at the end of simulation into a file then it read weights file
		"""
		DomainBehavior.__init__(self)
		self.state = {'status':'Idle','sigma':INFINITY}
		#self.simData = SingeltonData()
		#self.simData.Set({})
		
		self.dataInit = {'N':N,'M':M,'bias':bias,'activation':activation_f[0]}
		self.k = k
		self.a = a
		self.b = b
		self.msgListOut = []
		self.msgListIn = {}
		self.sim = None
		self.fileName = fileName
		self.learning_flag = learning_flag
		self.layerId = self.myID
		
		seed(0)

	def extTransition(self):
		""" receiving only new input to claculate or just a signal of weight changes. """
		i=0
		for port,msg in self.peek_all():
			i = port.myID
			self.msgListIn[i] = msg
			value = msg.value
			
			if i == (len(self.IPorts)-1):
				""" receiving weight changing signal """
				self.sim = value
				self.msgListIn = {}
				break
			else:
				""" receiving new input to calculate """
				if self.sim == None: 
					self.sim = Signature(self.createSim(self.dataInit))
				self.sim.inputs[i] = value[0]
				self.sim.val_inputs[i] = value[1]
					
		### after receiving all inputs then go to calculate and propagate the output throught the netwok.
		if not i == (len(self.IPorts)-1):
			self.transfer(self.sim)
			self.state = {'status':'ACTIVE','sigma':0.0}
		print "."
	def concTransition(self):
		if self.state['status'] == 'ACTIVE':
			plid = self.msgListIn[0].value[2]
			for Id in self.simData.simDico:
				try:
					sim = self.simData.simDico[Id]
					if not self.layerId in sim:
						self.simData.addSim(Id,self.layerId,self.createSim(self.dataInit))
					sim[self.layerId].previousId = plid
					sim[self.layerId].inputs.update(sim[plid].outputs)
					#sim[self.layerId].inputs[len(sim[self.layerId].inputs)]=sim[self.layerId].bias
					try:
						sim[self.layerId].val_inputs.update(sim[plid].val_outputs)
					except:
						pass
					self.transfer(sim[self.layerId])
				except:
					pass

	def outputFnc(self):
		Nbports = len(self.OPorts)-1
		for i in range(Nbports):
			msg = self.msgListOut[i]
			try:
				T = self.sim.outputs[i]
				V = self.sim.val_outputs[i]
			except:
				V = None
			msg.value= [T,V,self.layerId]
			self.poke(self.OPorts[i],msg)
		
		msg = self.msgListOut[Nbports]
		msg.value = [self.sim,None,self.layerId]
		self.poke(self.OPorts[Nbports],msg)
		self.msgListIn = {}

	def intTransition(self):
		self.state = {'status': 'Idle', 'sigma':INFINITY}

	def rand(self,a,b):
		return (b-a)*random() + a

	def timeAdvance(self):
		return self.state['sigma']

	def transfer(self,sim):
		for i in sim.wh:
			s = sum([sim.inputs[j]*sim.wh[i][j] for j in sim.wh[i]])
			sim.outputs[i] = self.activation(sim.activation,s)
			#if sim.val_inputs[i] != None:
			try:
				s_val = sum([sim.val_inputs[j]*sim.wh[i][j] for j in sim.wh[i]])
				sim.val_outputs[i] = self.activation(sim.activation,s_val)
			#else:
			except:
				sim.val_outputs[i]= None
				#raise

	def activation(self,activation,x,k=1.0):
		""" activation Functions."""
		if activation == "tanh":
			return math.tanh(x)
		elif activation == "sigmoid":
			return 1.0/(1.0+math.exp(float(k)*(-float(x))))
		else:
			return x
				
	def finish(self, msg):
		""" optional method to control the the behavior when simulation finished
		"""
		#if self.learning_flag:
			#### write weights to file
			#try:
				#s = shelve.open(self.fileName+".db")
				#s['w'] = self.simData
			#finally:
				#s.close()
		
		pass
		
	def createSim(self,dataInit):

		dataInit['inputs'] = {len(self.IPorts)-1:self.dataInit['bias']}
		dataInit['val_inputs'] = {len(self.IPorts)-1:self.dataInit['bias']}
		
		dataInit['outputs'] = {}
		dataInit['val_outputs'] = {}
		dataInit['wh'] = {}
		dataInit['c'] = {}
		dataInit['errors'] = {}
		dataInit['errorglobal'] = 0.0
		dataInit['errorglobalvalidation'] = 0.0
		dataInit['previousId'] = None
		
		for i in range(len(self.OPorts)-1):
			dataInit['wh'][i] = {}
			dataInit['c'][i] = {}
			for j in range(len(self.IPorts)):
				dataInit['wh'][i][j] = self.rand(self.a, self.b)
				dataInit['c'][i][j] = 0.0
		self.msgListOut = [Message([None,None],0.0) for i in xrange(len(self.OPorts))]
		
		return dataInit
	
	def __str__(self): 
		return 'Hidden'