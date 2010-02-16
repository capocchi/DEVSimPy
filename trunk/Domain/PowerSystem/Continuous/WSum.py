# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# WSum.py --- Atomic model that somme its input values
#                     --------------------------------
#                        	 Copyright (c) 2010
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/02/10
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from DomainInterface.DomainBehavior import DomainBehavior

class WSum(DomainBehavior):
	""" Atomic model for sommator
	"""

	###
	def __init__(self,K=[1,1]):
		"""	Constructor.
		"""

		DomainBehavior.__init__(self)
		
		# State variables
		self.state = {	'status': 'IDLE', 'sigma': INFINITY}
		
		# Local copy
		self.K=K			# matrix y=K[0]*x0+...+K[7]*x7 (QSS1 to3)
		
		# liste de 0
		self.Xs = [0.0]*len(self.K)
		self.Mxs = [0.0]*len(self.K)
		self.Pxs = [0.0]*len(self.K)
		self.Y=[0.0]*3
		
	###
  	def intTransition(self):
		self.state["status"] = 'IDLE'
		self.state["sigma"] = INFINITY

	###
        def extTransition(self):
		
		# probleme sous windows
		#activePort = self.myInput.keys()[0]
		#np=activePort.myID

		# marche quelque soit l'os mais plus lent !
		np=0
		self.msg= self.peek(self.IPorts[np])
		while(self.msg == None):
			np+=1
			self.msg= self.peek(self.IPorts[np])

		u=0.0
		v=0.0
		w=0.0
		
		for i in range(len(self.IPorts)):
			if i==np:
				self.Xs[i],self.Mxs[i],self.Pxs[i] = self.msg.value
			else:
				x=self.Pxs[i]*self.elapsed
				self.Xs[i]+=(self.Mxs[i]+x)*self.elapsed
				self.Mxs[i]+=x*2.0
			
			u += self.Xs[i]*self.K[i]
			v += self.Mxs[i]*self.K[i]
			w += self.Pxs[i]*self.K[i]
		
		self.Y=[u,v,w]
		
		self.state['status']="ACTIF"
		self.state['sigma']=0
			
	###
  	def outputFnc(self):
		assert(self.msg != None)
		
		self.msg.value=self.Y
		self.msg.time=self.timeNext
		
		self.poke(self.OPorts[0], self.msg)
		
	###
  	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self):return "WSum"
