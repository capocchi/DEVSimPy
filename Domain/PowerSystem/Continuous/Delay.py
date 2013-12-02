# -*- coding: utf-8 -*-

"""
Name : Delay.py
Brief description : Atomic model that send message with delay
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr), jfs (santucci@univ-corse.fr)
Version : 1.0
Last modified : 05/01/12
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior
from itertools import *

#    ======================================================================    #
class Delay(DomainBehavior):
	"""	Atomic model that send message with delay
	"""

	###
	def __init__(self, delay=1.0):
		""" Constructor.

			@param delay : Sending delay
		"""
		DomainBehavior.__init__(self)

		# state variable
		self.state = {	'status':	'IDLE', 'sigma': INFINITY}

		# Local copy
		self.s = delay	# step
		
		### output message
		self.msg = None
		
	###
  	def intTransition(self):
		# state change
		self.changeState()

	###
	def extTransition(self):
		# checkin
		self.msg = self.peek(self.IPorts[0])

		# state change
		self.changeState('ACTIF', self.s-self.elapsed)
		
	###
  	def outputFnc(self):
		assert(self.msg!=None)
		self.msg.time = self.timeNext
		self.poke(self.OPorts[0], self.msg)

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status']=status
		self.state['sigma']=sigma

	def __str__(self):return "Delay"
