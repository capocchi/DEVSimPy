# -*- coding: utf-8 -*-

"""
Name : PulseGen.py 
Brief descritpion : Pulse generator atomic model 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 21/03/09
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior
from Domain.PowerSystem.Object import Message

#    ======================================================================    #
class PulseGen(DomainBehavior):
	""" Pulse atomic model.
	"""

	###
	def __init__(self, v=0, a=.5, itim=0.01, etim=0.015):
		""" Constructor.

			@apram v : Base Value
			@param a : Amplitude
			@param itim	: Initial Step Time
			@param etim	: Final Pulse Time

		"""

		DomainBehavior.__init__(self)

		# state variable
		self.state = {	'status': 'ACTIVE', 'sigma': 0}

		# Local copy
		self.v=v 		
		self.a=a		
		self.itim=itim		
		self.etim=etim
		
		self.k=0
		self.tim = [0, self.itim, self.etim, INFINITY]
		self.value=[self.v, self.v+self.a, self.v]
		
	###
  	def intTransition(self):
		"""
		"""
		self.k+=1
		self.state = self.changeState(sigma=self.tim[self.k]-self.tim[self.k-1])

	###
  	def outputFnc(self):
		"""
		"""
		# send output message
		for i in range(len(self.OPorts)):
			self.poke(self.OPorts[i], Message([self.value[self.k],0,0],self.timeNext))

	###
  	def timeAdvance(self):
		"""
		"""
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		"""
		"""
		return { 'status':status, 'sigma':sigma}

	###
	def __str__(self):return "PulseGen"
