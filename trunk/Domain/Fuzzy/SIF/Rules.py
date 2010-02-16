# -*- coding: utf-8 -*-

from Domain.Fuzzy.FuzzyDomainBehavior import *

class Rules(DomainBehavior):
	'''	Basic atomic model
	'''
	
	###
	def __init__(self):
		"""Constructor.
		"""
		DomainBehavior.__init__(self)

		# Declaration des variables d'�tat (actif tout de suite)
		self.state = {	'status':	'PASSIVE', 'sigma':	Master.INFINITY}

		self.vh = None
		self.vc = None
		self.cpt=0

	###
	def intTransition(self): 
		self.state["sigma"] = Master.INFINITY

	###
	def extTransition(self):
		self.cpt+=1
	
		
		tmp1 = self.peek(self.IPorts[0])
		tmp2 = self.peek(self.IPorts[1])

		if tmp1 != None:
			self.msg1=tmp1
		if tmp2 != None:
			self.msg2=tmp2

		if self.cpt==2:
			if self.msg1.value[0]=='N' and self.msg2.value[0]=='N':
				self.vh, self.vc=('PG','ZR')
			elif self.msg1.value[0]=='N' and self.msg2.value[0]=='Z':
				self.vh, self.vc=('PP','NP')
			elif self.msg1.value[0]=='N' and self.msg2.value[0]=='P':
				self.vh, self.vc=('ZR','NG')
			elif self.msg1.value[0]=='Z' and self.msg2.value[0]=='N':
				self.vh, self.vc=('PP','PP')
			elif self.msg1.value[0]=='Z' and self.msg2.value[0]=='Z':
				self.vh, self.vc=('ZR','ZR')
			elif self.msg1.value[0]=='Z' and self.msg2.value[0]=='P':
				self.vh, self.vc=('NP','NP')
			elif self.msg1.value[0]=='P' and self.msg2.value[0]=='N':
				self.vh, self.vc=('ZR','PG')
			elif self.msg1.value[0]=='P' and self.msg2.value[0]=='Z':
				self.vh, self.vc=('NP','PP')
			elif self.msg1.value[0]=='P' and self.msg2.value[0]=='P':
				self.vh, self.vc=('NG','ZR')
		
			self.cpt=0
			self.state["sigma"] = 0
	###
  	def outputFnc(self):
		self.msg1.value=[self.vc,0,0]
		self.msg2.value=[self.vh,0,0]
		self.msg1.time=self.timeNext
		self.msg2.time=self.timeNext

		self.poke(self.OPorts[0], self.msg1)
		self.poke(self.OPorts[1], self.msg2)

	###
  	def timeAdvance(self):
		return self.state['sigma']

	def __str__(self):
		return "Rules"