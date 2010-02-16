# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# SinGen.py --- Sinus generator
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

	
from math import pi, sqrt, sin, cos
from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message
        
#    ======================================================================    #
class SinGen(DomainBehavior):
	""" Sinus atomic model.
	"""

	###
	def __init__(self, a=1.0, f=50.0, phi=0.0, k=20, m="QSS2"):
		"""	Constructor
		"""

		DomainBehavior.__init__(self)
		
		# state variable declaration
		self.state = {	'status':'ACTIVE','sigma':0}
		
		# Local copy    
		self.a=a
		self.f=f
		self.phi=phi
		self.m=m
		self.k=k								# nombre de points calcule	
		self.w=2*3.14159*self.f # pulsation
		self.dt=1/float(self.f)/float(self.k)
	
	###
  	def intTransition(self):
		# (inactive during dt)
		self.state["sigma"] = self.dt
		
	###
  	def outputFnc(self):
		
		# output value list
		L = [self.a*sin(self.w*self.timeNext+self.phi),0.0,0.0]
	
		if(self.m=="QSS2"):
			L[1]=self.a*self.w*cos(self.w*self.timeNext+self.phi)
		elif(self.m=="QSS3"):
			L[1]=self.a*self.w*cos(self.w*self.timeNext+self.phi)
			L[2]=-self.a*pow(self.w,2)*sin(self.w*self.timeNext+self.phi)/2
		
		# send output message
		for i in range(len(self.OPorts)):
			self.poke(self.OPorts[i], Message(L,self.timeNext))

	###
  	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self):return "SinGen"
