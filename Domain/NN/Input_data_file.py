# -*- coding: utf-8 -*-

"""
Name : Input_data_file.py
Brief descritpion : 
Author(s) : Samuel TOMA <toma@univ-corse.fr>
Version :  1.0
Last modified :
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message
import os.path

### Model class ----------------------------------------------------------------
class Input_data_file(DomainBehavior):
	"""
	"""
	def __init__(self,fileName = os.path.join(os.getcwd(),"training.dat"), fileName1=os.path.join(os.getcwd(),"validation.dat")):
		"""
		@param fileName : training file path
		@param fileName1 : validation file path
		
		"""
		
		DomainBehavior.__init__(self)
		
		self.current_pattern = 0
		self.training_data = []
		self.validation_data = []
		self.file_training = fileName			
		self.file_validation = fileName1	
		self.mode = "training"
		if os.path.exists(self.file_training):
			with open(self.file_training,"rb") as f:
				for l in filter(lambda b: b != '' , map(lambda a: a.replace('\n', ''), f.readlines())):
					temp = filter(lambda a: a != '',l.split(' '))
					i = 0
					for t in temp:
						temp[i] = float(temp[i])
						i += 1
					self.training_data.append(temp)
		if os.path.exists(self.file_validation):
			with open(self.file_validation,"rb") as f:
				for l in filter(lambda b: b != '' , map(lambda a: a.replace('\n', ''), f.readlines())):
					temp = filter(lambda a: a != '',l.split(' '))
					i = 0
					for t in temp:
						temp[i] = float(temp[i])
						i += 1
					self.validation_data.append(temp)		
		if len(self.training_data) != 0 :
			self.state = {'status':'ACTIVE','sigma':0}
		else:
			self.state = {'state':'Idle','sigma':INFINITY}
	def extTransition(self):
		pass
	
	def outputFnc(self):
		if len(self.OPorts) != len(self.training_data[0]):
			print "Wrong number of inputs or outputs, no training phase will be excecuted"
			self.state = {'state':'Idle','sigma':INFINITY}
		elif self.mode == "training":
			for j in range(len(self.training_data[self.current_pattern])):
				self.poke(self.OPorts[j],Message([self.training_data[self.current_pattern][j]],self.current_pattern+1))
			self.current_pattern += 1
		elif self.mode == "transit":
			print "hi "
			self.poke(self.OPorts[0],Message(["validation"],self.current_pattern+1))
		elif self.mode == "validation":
			for j in range(len(self.validation_data[self.current_pattern])):
				self.poke(self.OPorts[j],Message([self.validation_data[self.current_pattern][j]],self.current_pattern+1))
			self.current_pattern += 1
	      
	def intTransition(self):
		if self.mode == "training":
			if self.current_pattern  == len(self.training_data):
				if len(self.validation_data) != 0 :
					self.mode = "transit"
					self.current_pattern = 0
				else:
					self.mode = "Done"
					print self.mode
					self.state= {'state':'Idle','sigma':INFINITY}
		elif self.mode == "transit":
			self.mode = "validation"
		elif self.mode == "validation":
			if len(self.OPorts) != len(self.training_data[0]):
				print "no validation data or Wrong number of inputs or outputs"
			elif self.current_pattern  == len(self.validation_data):
				self.state= {'state':'Idle','sigma':INFINITY}
		  
	def timeAdvance(self):
		return self.state['sigma']
