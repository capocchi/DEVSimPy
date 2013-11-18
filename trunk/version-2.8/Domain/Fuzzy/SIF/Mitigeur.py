# -*- coding: utf-8 -*-
 
# -*- coding: utf-8 -*-

from Domain.Fuzzy.FuzzyDomainBehavior import *
from Domain.Fuzzy.Object import *
import math

class Mitigeur(DomainBehavior):
	'''	Basic atomic model
	'''
	
	###
	def __init__(self, vc=0.5, vh=0.5):
		"""Constructor.
		"""
		DomainBehavior.__init__(self)
		
		# Declaration des variables d'�tat (actif tout de suite)
		self.state = {	'status':	'ACTIVE', 'sigma':	0}

		self.vc=vc
		self.vh=vh

		self.cpt=0
		self.start=True	

	###
	def intTransition(self): 
		self.state["sigma"] = Master.INFINITY

	###
	def extTransition(self):
		
		self.cpt+=1

		tmp1=self.peek(self.IPorts[0])
		tmp2=self.peek(self.IPorts[1])

		if tmp1 != None:
			self.msg1=tmp1
		if tmp2 != None:
			self.msg2=tmp2

		if self.cpt==2:
			self.state["sigma"] = 0
			self.cpt=0
	###
  	def outputFnc(self):
		if self.start:
			delta_vc=0
			delta_vh=0

			self.msg1=Message()
			self.msg2=Message()
			self.start=False
		else:
			delta_vc=self.msg1.value[0]
			delta_vh=self.msg2.value[0]
			

		self.vc+=delta_vc
		self.vh+=delta_vh
		deno=math.pow(self.vc,2)+math.sqrt(self.vh)
		self.msg1.value=[(10*math.pow(self.vc,2)+80*math.sqrt(self.vh))/deno,0,0]
		self.msg2.value=[deno,0,0]
		
		self.msg1.time=self.timeNext
		self.msg2.time=self.timeNext

		self.poke(self.OPorts[0], self.msg1)
		self.poke(self.OPorts[1], self.msg2)

	###
  	def timeAdvance(self):
		return self.state['sigma']

	def __str__(self):
		return "Mitigeur"