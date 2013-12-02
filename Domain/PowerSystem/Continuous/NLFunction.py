# -*- coding: utf-8 -*-

"""
Name : NLFunction.py 
Brief descritpion : Non linear atomic model 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 21/03/09
GENERAL NOTES AND REMARKS:
- Implementation du modele avec comme hypothese qu'il ne peux recevoir que # des messages a des isntants diff liste des message non vide et les traiter (A faire car cela # rend plus rapide le traitrement)
GLOBAL VARIABLES AND FUNCTIONS:
warning : the inputs of this model can't be connected to a signle model. 
If you want to connect one model to each inputs, you should duplicate the single model by the number of inputs.
"""

from DomainInterface.DomainBehavior import DomainBehavior

from math import *
from itertools import *
from re import findall, compile

#    ======================================================================    #
class NLFunction(DomainBehavior):
	"""	Non linear function atomic model.

		example of use: u0*2
	"""

	###
	def __init__(self, expr="u0*2"):
		"""	Constructor.
			@param expr: Expression which is evaluated
		"""
		DomainBehavior.__init__(self)

		# state variable
		self.state = {'status': 'IDLE', 'sigma': INFINITY}
		
		#local copy
		self.expr = expr
	
		self.n = int(max(filter(lambda a: a.replace('u',''), findall(compile('u[0-9]*'), self.expr))).replace('u',''))+1

		### try to import numpy for speed up the matrix multiplication
		try:
			from numpy import zeros
			
			self.u	= zeros(self.n)
			self.mu = zeros(self.n)
			self.pu = zeros(self.n)
			
			self.getY = self.getY1
			
		except ImportError:
			self.u	= [0.0]*self.n
			self.mu = [0.0]*self.n 
			self.pu = [0.0]*self.n
		
			self.getY = self.getY2
			
		for i in xrange(self.n):
			self.expr = self.expr.replace("u"+str(i),"self.u["+str(i)+']')

		self.Y = [0.0]*3
		
		# input msg
		self.msg = None

	###
	def extTransition(self):
		"""
		"""
		assert self.n == len(self.IPorts)

		# multi-port values version
		for p in xrange(self.n):
			msg = self.peek(self.IPorts[p])
			if msg != None:
				self.msg = msg
				self.Y = self.getY(self.msg.value, p)
			
		self.state['sigma'] = 0

	###
	def intTransition(self):
		self.state['status'] = "IDLE"
		self.state['sigma'] = INFINITY
		
	###
	def outputFnc(self):
		"""
		"""
		assert(self.msg != None)
		self.msg.value = self.Y
		self.msg.time = self.timeNext
		self.poke(self.OPorts[0], self.msg)

	###
	def timeAdvance(self):
		return self.state['sigma']
	
	###
	def getY1(self, Aux=[], port=0):
		
		A = self.pu*self.elapsed
		self.u += (self.mu+A)*self.elapsed
		self.mu += 2.0*A
		
		self.u[port], self.mu[port], self.pu[port] = Aux
		
		return [eval(self.expr), 0.0, 0.0]
	
	def getY2(self, Aux=[], port=0):
		
		I = range(self.n)
		self.u = map(lambda x,y: x+y, map(lambda i:self.mu[i]*self.elapsed+self.pu[i]*pow(self.elapsed,2), I),self.u)
		self.mu = map(lambda x,y: x+y, map(lambda i: 2.0*self.pu[i]*self.elapsed, I), self.mu)
	
		self.u[port], self.mu[port], self.pu[port] = Aux
		
		return [eval(self.expr), 0.0, 0.0]
	###
	def __str__(self):return "NLFunction"