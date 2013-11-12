# -*- coding: utf-8 -*-

"""
Name : Integrator2.py
Brief description : Atomic Model for integration function with init message sending
Authors : Laurent CAPOCCHI
Version : 1.0
Last modified : 31/10/11
GENERAL NOTES AND REMARKS: en debut de simulation, génération d'une sortie correspondant à l'initialisation. Si l'utilisateur veut uniquement effectuer
une initilaisation sans génération de sortie, il faut utiliser integrator.py.
GLOBAL VARIABLES AND FUNCTIONS
"""

from Domain.PowerSystem.Continuous.Integrator import *
from Domain.PowerSystem.Object import Message

class Integrator2(Integrator):
	""" Atomic model for QSS integration function.
		Send init message at the begining of the simulation
	"""

	###
	def __init__(self, m=('QSS3','QSS2','QSS1'), dQ=0.01, x=0.0):
		"""	Constructor.
		
			@param m : QSS methode choise
			@param dQ : quantification level
			@param x : initial value
		"""

		Integrator.__init__(self,m,dQ,x)

	###
  	def outputFnc(self):

		if self.timeNext == 0:
			self.msg = Message([self.x,0.0,0.0], self.timeNext)
		else:
			assert( self.msg != None)
			
			if(self.m == "QSS"):
				if(self.u==0):
					val = [self.q,0,0]
				else:
					if CYTHON:
						val = calc4(self.q,self.dQ,self.u)
					else:
						val = [self.q+self.dQ*self.u/fabs(self.u), 0.0, 0.0]
			elif(self.m == "QSS2"):
				if CYTHON:
					val = calc5( self.x, self.u, self.state['sigma'], self.mu)
				else:
					val = [self.x+self.u*self.state['sigma']+self.mu*self.state['sigma']*self.state['sigma']/2, self.u+self.mu*self.state['sigma'], 0.0]
			else:
				if CYTHON:
					val = calc6(self.x, self.u, self.state['sigma'], self.mu, self.pu)
				else:
					val = [self.x+self.u*self.state['sigma']+(self.mu*pow(self.state['sigma'],2))/2.0 + (self.pu*pow(self.state['sigma'],3))/3.0, self.u+self.mu*self.state['sigma']+self.pu*pow(self.state['sigma'],2), self.mu/2.0 + self.pu*self.state['sigma']]

			self.msg.value = val
			self.msg.time = self.timeNext
			
		self.poke(self.OPorts[0], self.msg)

	###
	def __str__(self):return "Integrator2"