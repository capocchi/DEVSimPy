# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# LB.py --- Loop Breaking model
#                     --------------------------------
#                        	 Copyright (c) 2007
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 25/11/07
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

try:
	from PSDomain.PSDomainBehavior import PSDomainBehavior, Master
	from PSDomain.Object import Message
except ImportError:
	import sys,os
	for spath in [os.pardir+os.sep]:
		if not spath in sys.path: sys.path.append(spath)
	from PSDomain.PSDomainBehavior import PSDomainBehavior, Master
	from PSDomain.Object import Message
	
from math import *
from itertools import*

#from delegate import parallelize

#    ======================================================================    #
INFINITY = 4e10

class LB(PSDomainBehavior):
	'''	Model atomique de la fonction NL
	'''

	###
	def __init__(self,tolerance=0.001):
		'''	Constructeur
		'''
		PSDomainBehavior.__init__(self)

		#  Declaration des variables d'�tat.
		self.state = {	'status':	'IDLE',
						'sigma':	INFINITY}
		#local copy
		self._tol=tolerance
		
		self.y=0.0
		self.z1=0.0
		self.z2=0.0
		self.h1=0.0
		self.msg = None

		# Declaration des ports de sortie
		self.IN = self.addInPort()
		self.OUT = self.addOutPort()

	###
	def extTransition(self):
		
		self.msg=self.peek(self.IN)
		xv=self.msg.value[0]
		
		if fabs(xv-self.z2)<self._tol:
			self.state['sigma']= INFINITY
		else:
			tmp=self.z2
			if (self.z1==0.0) and (self.z2==0.0):
				self.z2=xv
			else:
				self.z2=(self.z1*xv-self.z2*self.h1)/(xv-self.h1+self.z1-self.z2)
			self.z1=tmp
			self.h1=xv
			self.state['sigma']= 0
	
		return self.state

	###
  	def intTransition(self):
		
		self.state = self.changeState()		
		return self.state
	
		
	###
  	def outputFnc(self):
		
		self.y=self.z2
		
		assert(self.msg != None)
		self.msg.value[0]=self.y
		self.msg.time=self.timeNext
		
		## envoie du message le port de sortie
		self.poke(self.OUT, self.msg)

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		return { 'status':status, 'sigma':sigma}
	
	###
	def __str__(self):return "PB"