# -*- coding: utf-8 -*-

"""
Name : PWMGen.py 
Brief descritpion : PWM generator atomic model 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 21/03/09
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior
from Domain.PowerSystem.Object import Message

#    ======================================================================    #

class PWMGen(DomainBehavior):
	"""	PWM atomic model.
	"""

	###
	def __init__(self, a=0, tm=1):
		"""	Constructor.

			 @param a : Amplitude
			 @param tm : Modulating sinusoidal period
		"""

		DomainBehavior.__init__(self)

		# State variables
		self.state = {	'status': 'ACTIVE','sigma': 0}

		# Local copy
		self.a=a
		self.tm=tm
		
		self.dt= [ 0.52576249002189, 0.42770710237896, 0.62266988694768, 0.33235474394723, 0.71465110292802, 0.24345384677928, 0.79816713494423, 0.16448202528866, 0.87006137717856, 0.09849927665395, 0.92767110593532,0.04803154181473, 0.96890546649863,  0.01498703066906, 0.99229400455701, 0.00060227626444, 0.99701303051085, 0.00541209560964, 0.98289729495148, 0.02923790417889, 0.95044204882374, 0.07119152689703, 0.90079658391823, 0.12969549084197, 0.83574604807234,0.20252423831807, 0.75767499017353, 0.2868723108525,0.66950488056329, 0.37945431748385, 0.57459956378267, 0.47663726221426]
		self.dt +=[self.dt[31-i] for i in range(0,32)]
		self.dt = map(lambda x: 1.0*x*self.tm/32.0, self.dt)
		self.sig=1
		self.j=-1
		
	###
  	def intTransition(self):
		"""
		"""
		self.j+=1
		if(self.j>63):
			self.j=0
		self.sig=-self.sig
		
		self.state = self.changeState(sigma=self.dt[self.j])

	###
  	def outputFnc(self):
		"""
		"""
		# send output message
		for i in range(len(self.OPorts)):
			self.poke(self.OPorts[i], Message([1.0*self.a*self.sig, 0], self.timeNext))

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
	def __str__(self):return "PWMGen"
