# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        <DeltaOutput_Weight.py>

 Model:       <New model added to a neural network to  calculate for a spacific layer its weight during learning phase>
 Author:      <Samuel TOMA>

 Created:     <2010-11-25>
-------------------------------------------------------------------------------
"""
	
### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.NN.Object import Message
import random
import os
import datetime
import numpy
import array

### Model class ----------------------------------------------------------------
class DeltaOutput_Weight(DomainBehavior):
	
	def __init__(self, M=0.1, N=0.9):
		""" constructor.
			@param M 		= factor from the previous weight while learning
			@param N 		= factor from the new weight while learning
			@param function 	= activation function "sigmoide or tanh"
		"""
		
		DomainBehavior.__init__(self)
		
		self.fileName = os.path.join(os.getcwd(), "weights.dat")
		self.state = {	'status': 'Idel', 'sigma':INFINITY}
		self.function = ""
		self.M = M
		self.N = N
		self.inputOutput = numpy.array([[]])
		self.w = array.array('d',[])
		self.deltas = array.array('d',[])
		self.outError = array.array('d',[])
		
	def extTransition(self):
		for np in range(len(self.IPorts)):
			self.msg = self.peek(self.IPorts[np])
			if self.msg != None:
				if np == 0:
					#### Initialization at Time zero.
					if self.msg.value[2] == True:
						self.w  = self.msg.value[0]
						self.function = self.msg.value[1]
						self.c = numpy.array([[0.0]*len(self.w[0])]*len(self.w))
						self.deltas = numpy.zeros(len(self.w[0]), float)
					else:
					#### receiving the input ouput values used to update the weights.
						self.inputOutput = self.msg.value[0]
						
				elif self.msg.value[0] == "trained":
					#self.print_weight()
					self.outError = self.msg.value
					self.state = {'status': 'ACTIVE', 'sigma':0}
				else:
					self.errors = self.msg.value
					self.deltas = map(self.dactivation, self.inputOutput[1]) * self.errors

					for j in xrange(len(self.inputOutput[0])):
						for k in xrange(len(self.inputOutput[1])):
							change = self.deltas[k]*self.inputOutput[0][j]
							self.w[j][k] += self.N*change + self.M*self.c[j][k]
							self.c[j][k] = change
					
					a = self.deltas*self.w
					self.outError = a.sum(axis=1)

					self.state = {'status': 'ACTIVE', 'sigma':0}
		
	def outputFnc(self):
		assert(self.msg != None)
		if self.msg.value[0] != "trained":
			self.poke(self.OPorts[0],Message([self.w],self.timeNext))
		if (len(self.outError)) != 0:
			self.poke(self.OPorts[1], Message(self.outError,self.timeNext))
	
	def intTransition(self):
		self.state = {'status': 'Idle', 'sigma':INFINITY}
	
	#def print_weight(self):
		#f = open(self.fileName,'a')
		#f.write(str(datetime.datetime.today()))
		#f.write("settings of neural network at :\n")
		#f.write("\tweights:\n\t")
		#for l in self.w:
			#for r in l:
				#f.write("%f "%r)
			#f.write("\n\t")
		#f.write("\n")
		#f.close()
	
	def timeAdvance(self):
		return self.state['sigma']
	
	def rand(self,a,b):
		return (b-a)*random() + a
	
	def dactivation(self,y):
		if self.function == "tanh":
			return 1.0 - y*y    		# tanh
		elif self.function == "sigmoide":
			return y-y*y			# sigmoide
		else:
			if y>1 or y<0:				#lineaire
				return 0.0
			else: 
				return 1.0