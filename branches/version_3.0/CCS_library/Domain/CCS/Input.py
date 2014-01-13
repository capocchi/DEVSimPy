# -*- coding: utf-8 -*-

"""
	This model represents the input layer of an artificiel neural network
	@author: Samuel TOMA
	@organization: University of Corsica
	@contact: toma@univ-corse.fr
	@since: 2010.12.10
	@version: 2.0
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.Basic.Object import Message

### Model class ----------------------------------------------------------------
class Input(DomainBehavior):
	""" Input Layer model
	
		2 input ports:
			- Learning input
			- Validation input
		Number of output depends of the input number
		
	"""
	
	def __init__(self):
		"""Constructor
		"""
		
		DomainBehavior.__init__(self)
		
		
		self.state = {'status':'Idle', 'sigma': INFINITY}
		#self.dt = INFINITY
		self.current_tpattern = 0
		self.current_vpattern = 0
		self.t_pattern = []
		self.v_pattern = []
		
	def extTransition(self):
		### receiving pattern before statring the simulation.
		for port, msg in self.peek_all():
			i = port.myID
			if i == 0:
				self.t_pattern.append(map(float,msg.value[0]))
				self.dt = 1.0/len(self.t_pattern)
				self.state = {'status':'PASSIVE', 'sigma':self.dt}
				self.msgListOut = [Message([None,None],0.0) for i in xrange(len(self.OPorts))]
			else:
				self.v_pattern.append(map(float,msg.value[0]))
				### changing state deleted.
	def outputFnc(self):
		""" sends one pattern at a time """
		if self.state['status'] == 'ACTIVE':
			for i in xrange(len(self.t_pattern[self.current_tpattern])):
				tval = self.t_pattern[self.current_tpattern][i]
				vval = self.v_pattern[self.current_vpattern][i] if self.v_pattern != [] else None
				msg = self.msgListOut[i]
				msg.value = [tval,vval,self.myID]
				self.poke(self.OPorts[i], msg)
	
	def intTransition(self):
		""" incrementation of the cursor on the patterns (current) """
		if self.state['status'] == 'PASSIVE':
			self.state = {'status':'ACTIVE', 'sigma':0.0}
		elif self.state['status'] == 'ACTIVE':
			self.current_tpattern += 1
			if self.current_tpattern >= len(self.t_pattern):
				self.current_tpattern = 0
			
			self.current_vpattern += 1
			if self.current_vpattern >= len(self.v_pattern):
				self.current_vpattern = 0
			self.state = {'status':'PASSIVE', 'sigma':self.dt}

	def concTransition(self):
		
		if self.state['status'] == 'ACTIVE':
			for sim in self.simData.simDico:
				if not self.myID in self.simData.simDico[sim]:
					s = self.createSim()
					self.simData.addSim(sim,self.myID,s)
					## new msg list with layer id variable.
				l = self.t_pattern[self.current_tpattern]
				l_v = self.v_pattern[self.current_vpattern] if self.v_pattern != [] else None
				self.simData.simDico[sim][self.myID].outputs = dict(zip(xrange(len(l)),l))
				self.simData.simDico[sim][self.myID].val_outputs = dict(zip(xrange(len(l_v)),l_v)) if self.v_pattern != [] else None

	def createSim(self,dataInit={}):
		dataInit['outputs'] = {}
		dataInit['val_outputs'] = {}
	
	def timeAdvance(self):
		return self.state['sigma']