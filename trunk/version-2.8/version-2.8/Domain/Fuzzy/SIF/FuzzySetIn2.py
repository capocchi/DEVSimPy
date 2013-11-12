# -*- coding: utf-8 -*-

from Domain.Fuzzy.FuzzyDomainBehavior import *

class FuzzySetIn2(DomainBehavior):
	'''	Basic atomic model
	'''
	###
	def __init__(self):
		"""Constructor.
		"""
		DomainBehavior.__init__(self)

		# Declaration des variables d'�tat (actif tout de suite)
		self.state = {	'status':	'PASSIVE', 'sigma':	Master.INFINITY}

		self.Se=FuzzySets([FuzzyInt(-5,-0.1,-6,0,'N'),FuzzyInt(0,0,-0.1,0.1,'Z'),FuzzyInt(0.1,5,0,6,'P')],'Se')
		self.out = None

	###
	def intTransition(self): self.state["sigma"] = Master.INFINITY

	###
	def extTransition(self):
		'''
		'''

		self.msg=self.peek(self.IPorts[0])
		self.out = self.Se.findValue(self.msg.value[0])
		self.state["sigma"] = 0

	###
  	def outputFnc(self):
		self.msg.value[0]=self.out[0]
		self.msg.time=self.timeNext
		self.poke(self.OPorts[0], self.msg)
		
	###
  	def timeAdvance(self):
		return self.state['sigma']

	def __str__(self):
		return "FuzzySetIn2"
