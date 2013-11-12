# -*- coding: utf-8 -*-

"""
Name : WSum.py
Brief description : Atomic model that somme its input values
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version : 1.0
Last modified : 12/02/10
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS
"""

from DomainInterface.DomainBehavior import DomainBehavior

class WSum(DomainBehavior):
	""" Atomic model for sommator
	"""

	###
	def __init__(self, K = [1,1]):
		"""	Constructor.

			@param K : list of weight
		"""

		DomainBehavior.__init__(self)
		
		# State variables
		self.state = {	'status': 'IDLE', 'sigma': INFINITY}
		
		# Local copy
		self.K=map(float,map(eval,map(str,K)))			# matrix y=K[0]*x0+...+K[7]*x7 (QSS1 to3)
		
		n = len(self.K)
		try:
			from numpy import zeros
			
			self.Xs = zeros(n)
			self.Mxs = zeros(n)
			self.Pxs = zeros(n)
				
		except ImportError:
			
			self.Xs = [0.0]*n
			self.Mxs = [0.0]*n
			self.Pxs = [0.0]*n
		
		self.Y=[0.0]*3
		
	###
	def intTransition(self):
		self.state["status"] = 'IDLE'
		self.state["sigma"] = INFINITY

	###
	def extTransition(self):
		
		### il faut que le nombre de k soit égal au nombre d'entrée
		assert(len(self.Pxs)==len(self.K))
		
		### uncomment if numpy is not installed
		
		u=0.0
		v=0.0
		w=0.0
		
		# multi-port values version
		for i in xrange(len(self.IPorts)):
			msg = self.peek(self.IPorts[i])
			if msg is not None:
				self.msg = msg
				self.Xs[i],self.Mxs[i],self.Pxs[i] = self.msg.value
			else:
				x=self.Pxs[i]*self.elapsed
				self.Xs[i]+=(self.Mxs[i]+x)*self.elapsed
				self.Mxs[i]+=x*2.0
		
			#u += self.Xs[i]*self.K[i]
			#v += self.Mxs[i]*self.K[i]
			#w += self.Pxs[i]*self.K[i]
		
		u = self.Xs*self.K
		v = self.Mxs*self.K
		w = self.Pxs*self.K
		
		### work only with numpy
		self.Y[0]=u.sum()
		self.Y[1]=v.sum()
		self.Y[2]=w.sum()
		
		### sefl.Y=[u,v,w]
		self.state['status']="ACTIF"
		self.state['sigma']=0
			
	###
	def outputFnc(self):
		assert(self.msg != None)
		self.msg.value = self.Y
		self.msg.time = self.timeNext
		self.poke(self.OPorts[0], self.msg)
		
	###
	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self):return "WSum"