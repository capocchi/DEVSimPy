# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# RampGen.py --- Ramp generator
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
from Object import Message

#    ======================================================================    #

class RampGen(DomainBehavior):
	""" Ramp atomic model.
	"""

	###
	def __init__(self, t0=.0, tr=.001, u=.5, m="QSS2", dq=.01):
		"""	Constructor.
		"""

		DomainBehavior.__init__(self)

		# State varaibles
		self.state = {	'status': 'ACTIVE', 'sigma': 0}

		# Local copy
		self.t0=t0		# initial time
		self.tr=tr		# rise time
		self.u=u		# final value
		self.m=m	# QSS methode choise
		self.dq=dq		# quantification level
		
		self.T = [0, self.t0, self.t0+self.tr, INFINITY]
		self.v = [0, 0, self.u, self.u]
		self.mv = [0]

		if (self.tr>0):
			self.mv.append(self.u/self.tr)
		self.mv.append(0)
		self.j = 0
		
	###
  	def intTransition(self):		
		if (self.m=="QSS") and (self.j==1):
			if (self.mv[1]>0) and ((self.v[self.j]+self.dq)<self.u):
				# Changement d'ï¿½tat
				self.state = self.changeState(sigma=self.tr*self.dq/self.u)
				self.v[1]+=self.dq
			elif(self.mv[1]<0) and ((self.v[self.j]-self.dq)>self.u):
				self.state = self.changeState(sigma=-self.tr*self.dq/self.u)
				self.v[1]-=self.dq
			else:
				self.j+=1
				self.changeState(sigma=-(self.u-self.v[self.j])/(self.u/self.tr))
				self.v[1]=self.u
		else:
			self.changeState(sigma=self.T[self.j+1]-self.T[self.j])
			self.j+=1
			if(self.j==3):
				self.changeState(sigma=INFINITY)

	###
  	def outputFnc(self):

		if (self.m == "QSS"):
			L=[int((self.v[self.j]+self.dq/2)/self.dq), int(self.v[self.j]+self.dq/2),0,0]
		else:
			L=[self.v[self.j], self.mv[self.j],0]

		# seld output message
		for i in range(len(self.OPorts)):
			self.poke(self.OPorts[i], Message(L,self.timeNext))

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		return { 'status':status, 'sigma':sigma}

	###
	def __str__(self):return "RampGen"
