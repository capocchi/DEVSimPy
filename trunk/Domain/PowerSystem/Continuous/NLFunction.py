# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# NLFunction.py --- Non linear function.
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
#	- Implementation du modele avec comme hypothese qu'il ne peux recevoir que # des messages a des isntants diff liste des message non vide et les traiter (A faire car cela # rend plus rapide le traitrement)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
# warning : the inputs of this model can't be connected to a signle model. 
# If you want to connect one model to each inputs, you should duplicate the single model by the number of inputs.
# 
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from DomainInterface.DomainBehavior import DomainBehavior

from math import *
from itertools import*
from re import findall, compile

#    ======================================================================    #
class NLFunction(DomainBehavior):
	"""	Non linear function atomic model.
	"""

	###
	def __init__(self, expr=""):
		"""	Constructor.
		"""
		DomainBehavior.__init__(self)

		# state variable
		self.state = {'status': 'IDLE', 'sigma': INFINITY}
		
		#local copy
		self.expr = expr
		
		self.n = len(findall(compile('u[0-9]*'), self.expr))
		self.u	= [0.0]*self.n
		self.mu = [0.0]*self.n 
		self.pu = [0.0]*self.n 
		
		for i in range(self.n):
			self.expr = self.expr.replace("u"+str(i),"self.u["+str(i)+']')
	
		self.Y = [0.0]*3
		
		# input msg
		self.msg = None

	###
	def extTransition(self):
		
		assert self.n == len(self.IPorts)

		# version agree with the annoted header warning
		#self.msg = None
		#p = 0
		#while self.msg == None:
			#self.msg = self.peek(self.IPorts[p])
			#p +=1
		#p -= 1
		#self.Y = self.getY(self.msg.value, p)

		# multi-port values version
		for p in range(self.n):
			self.msg = self.peek(self.IPorts[p])
			if self.msg != None:
				self.Y = self.getY(self.msg.value, p)
			
		self.state['sigma'] = 0

	###
  	def intTransition(self):
		self.state['status'] = "IDLE"
		self.state['sigma'] = INFINITY
		
	###
  	def outputFnc(self):
			
		self.Y[1] = self.Y[2] = 0.0
		
		assert(self.msg != None)
		self.msg.value = self.Y
		self.msg.time = self.timeNext
		
		## envoie du message le port de sortie
		self.poke(self.OPorts[0], self.msg)

	###
  	def timeAdvance(self):
		return self.state['sigma']
	
	###
	def getY(self, Aux=[], port=0):
		
		I = range(self.n)
		self.u = list(imap(lambda x,y: x+y,list(imap(lambda i:self.mu[i]*self.elapsed+self.pu[i]*pow(self.elapsed,2),I)),self.u))
		self.mu = list(imap(lambda x,y: x+y,list(imap(lambda i: 2.0*self.pu[i]*self.elapsed,I)),self.mu))
		self.u[port], self.mu[port], self.pu[port] = Aux
		
		return [eval(self.expr), 0.0, 0.0]
	###
	def __str__(self):return "NLFunction"
