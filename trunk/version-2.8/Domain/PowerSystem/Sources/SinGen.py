# -*- coding: utf-8 -*-

"""
Name : SinGen.py 
Brief descritpion : Sinus generator atomic model 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 21/03/09
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""
import sys

from math import sqrt, sin, cos, pow
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.PowerSystem.Object import Message

#    ======================================================================    #
class SinGen(DomainBehavior):
	""" Sinus atomic model
	"""

	###
	def __init__(self, a = 1.0, f = 50.0, phi = 0.0, k = 20, m = "QSS2"):
		"""	Constructor

			@param a : amplitude
			@param f : frequency
			@param phi : phase
			@param k : step sample
			@param m : QSS order
		"""

		DomainBehavior.__init__(self)
		
		# state variable declaration
		self.state = {	'status':'ACTIVE','sigma':0}
		
		# Local copy    
		self.a = a
		self.f = f
		self.phi = phi
		self.m = m
		self.k = k								# nombre de points
		self.w = 2*3.14159*self.f # pulsation
		self.dt = 1/float(self.f)/float(self.k)
		
	###
	def intTransition(self):
		"""
		"""
		# (idle during dt)
		self.state["sigma"] = self.dt
		
	###
	def outputFnc(self):
		"""
		"""
		
		# output value list
		L = [self.a*2*sin(self.w*self.timeNext+self.phi),0.0,0.0]
		
		if(self.m == "QSS2"):
			L[1] = self.a*self.w*cos(self.w*self.timeNext+self.phi)
		elif(self.m == "QSS3"):
			L[1] = self.a*self.w*cos(self.w*self.timeNext+self.phi)
			L[2] = -self.a*pow(self.w,2)*sin(self.w*self.timeNext+self.phi)/2
			
		# send output message
		for i in xrange(len(self.OPorts)):
			self.poke(self.OPorts[i], Message(L,self.timeNext))

	###
	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self): return "SinGen"
