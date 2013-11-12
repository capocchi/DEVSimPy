# -*- coding: utf-8 -*-

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.Basic.Object import Message
from Domain.Collector.QuickScope import QuickScope
#from simulation_object import SingeltonData
import random
import math
import numpy
#import array
import copy
		
### Model class ----------------------------------------------------------------
class ErrorGenerator(QuickScope):
	
	def __init__(self, stop_learning_factor = 0.0, stop_error_factor = 0.0,fusion = True, eventAxis = False):
		""" Constructor

				@param stop_learning_factor = descr1
				@param stop_error_factor = descr2
		"""
		QuickScope.__init__(self,fusion = True, eventAxis = False)
		#self.simData = SingeltonData()
		self.state = {	'status': 'Idle', 'sigma':INFINITY}
		#self.stop_learning_factor = stop_learning_factor
		#self.stop_error_factor = stop_error_factor
		self.current_pattern = 0
		self.current_validation_pattern = 0
		self.iteration  = 0
		self.validation_iteration = 0
		self.input_list = {}
		self.input_list_validation = {}
		self.errors = {}
		self.errors_validation = {}
		self.output_targets = []
		self.output_validation_targets = []
		#self.globalerror = {}
		#self.globalerror_validation = {}
		self.globalerror = 0.0
		self.globalerror_validation = 0.0
		self.layerId = None
		#self.AddSimFlag = False
		#self.DelSimFlag = False
		#self.neuron = True
	
	def extTransition(self):
		""" recieving """
		
		for port,msg in self.peek_all(): 
			i = port.myID
			if i>1:
				value = msg.value
				self.layerId = value[2]
				self.input_list[i-2] = value[0]
				self.input_list_validation[i-2] = value[1]
			
			elif i == 0:
				self.output_targets.append(map(float,msg.value[0]))
			else:
				self.output_validation_targets.append(map(float,msg.value[0]))
		if i > 1:
			results = self.errorCalc(self.input_list,self.input_list_validation)
			
			self.globalerror += results['gErrors']
			self.globalerror_validation += results['gErrors_v']
			self.errors = results['errors']
			
			self.state = {'status': 'ACTIVE' , 'sigma': 0.0}
	
	def concTransition(self):
		if self.state['status'] == 'ACTIVE':
			for Id in self.simData.simDico:
				''' 
				### extracting the signature of the output layer 
				### to get the output and calculate the errors
				'''
				try:
						
					sim = self.simData.simDico[Id][self.layerId]
					results = self.errorCalc(sim.outputs,sim.val_outputs)
					sim.errors = results['errors']
					sim.errorglobal += results['gErrors']
					sim.errorglobalvalidation += results['gErrors_v']

					if self.current_pattern == len(self.output_targets)-1:
						try:
							self.results['t'+str(Id)].append((self.iteration,sim.errorglobal))
						except:
							self.results['t'+str(Id)] = [(self.iteration,sim.errorglobal)]
						sim.errorglobal = 0.0
					if self.current_validation_pattern == len(self.output_validation_targets)-1:
						try:
							self.results['v'+str(Id)].append((self.iteration,sim.errorglobalvalidation))
						except:
							self.results['v'+str(Id)] = [(self.iteration,sim.errorglobalvalidation)]
						sim.errorglobalvalidation = 0.0
				except:
					pass
				
	def outputFnc(self):
		self.poke(self.OPorts[0], Message([self.errors,None,None], self.timeNext))
	
	def intTransition(self):
		if self.current_pattern == len(self.output_targets)-1:
			try:
				self.results['t'].append((self.iteration,self.globalerror))
			except:
				self.results['t'] = [(self.iteration,self.globalerror)]
			self.iteration += 1
			self.current_pattern = 0
			self.globalerror = 0.0
		else:
			self.current_pattern += 1
			
		if self.current_validation_pattern == len(self.output_validation_targets)-1:
			try:
				self.results['v'].append((self.iteration,self.globalerror_validation))
			except:
				self.results['v'] = [(self.iteration,self.globalerror_validation)]
			self.validation_iteration += 1
			self.current_validation_pattern = 0
			self.globalerror_validation = 0.0
		else:
			self.current_validation_pattern += 1
		
		self.state = {'status':'Idle', 'sigma':INFINITY}
	
	def timeAdvance(self):
		return self.state['sigma']
	
	def errorCalc(self,in_lst,in_lst_v):
		errors = {}
		errors_v = {}
		a = 0.0
		b = 0.0
		cp = self.current_pattern
		for i in in_lst:
			errors[i] = float(self.output_targets[cp][i] - in_lst[i])
			#print in_lst[i],i
			a = a + 0.5*(errors[i]*errors[i])
			if self.output_validation_targets != []:
				errors_v[i] = float(self.output_validation_targets[cp][i]-in_lst_v[i])
				b = b+ 0.5*(errors_v[i]*errors_v[i])
		#print a,self.iteration
		return {'errors':errors,'gErrors':a,'gErrors_v':b}
			