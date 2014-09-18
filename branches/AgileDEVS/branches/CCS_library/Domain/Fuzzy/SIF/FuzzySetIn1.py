# -*- coding: utf-8 -*-

from Domain.Fuzzy.FuzzyDomainBehavior import *

class FuzzySetIn1(DomainBehavior):
	'''	Basic atomic model
	'''
	
	###
	def __init__(self):
		"""Constructor.
		"""
		DomainBehavior.__init__(self)

		# Declaration des variables d'�tat (actif tout de suite)
		self.state = {	'status':	'PASSIVE', 'sigma':	Master.INFINITY}

		self.Te=FuzzySets([FuzzyInt(-50,-10,-60,0,'N'),FuzzyInt(0,0,-10,10,'Z'),FuzzyInt(10,50,0,60,'P')],'Te')
		self.out = None

	###
	def intTransition(self): self.state["sigma"] = Master.INFINITY

	###
	def extTransition(self):
		'''
		'''

		self.msg=self.peek(self.IPorts[0])
		self.out = self.Te.findValue(self.msg.value[0])
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
		return "FuzzySetIn1" 
