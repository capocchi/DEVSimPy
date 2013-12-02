# -*- coding: utf-8 -*-

"""
Name : Gen.py 
Brief descritpion : 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr),  SANTUCCI (santucci@univ-corse.fr)
Version :  1.0                                        
Last modified : 08/01/13
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""
import sys

from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

#    ======================================================================    #
class Gen(DomainBehavior):
	""" 
	"""

	###
	def __init__(self, a = ['(0,0.0)']):
		"""	Constructor

			@param a : amplitude
		"""

		DomainBehavior.__init__(self)
		
		# Local copy
		self.a = map(lambda c: tuple(eval(c)),a)
		
		self.T = map(lambda a: float(a[0]), self.a)
		self.V = map(lambda a: float(a[1]), self.a)
		
		# state variable declaration
		self.state = {	'status':'ACTIVE','sigma':float(self.T[0])}
		
	def intTransition(self):
		try:
			s = self.T[1]-self.T[0]
			del self.T[0]
		except IndexError:
			s = INFINITY

		self.state['sigma'] = s
		
	###
	def outputFnc(self):
		"""
		"""
		self.poke(self.OPorts[0], Message([self.V.pop(0),0.0, 0.0], self.timeNext))

	###
	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self): return "Gen"
