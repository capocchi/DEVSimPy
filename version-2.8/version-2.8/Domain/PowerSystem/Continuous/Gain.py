# -*- coding: utf-8 -*-

"""
Name : Gain.py
Brief description : Atomic model of gain
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version : 1.0
Last modified : 08/05/09
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior
from itertools import *

#    ======================================================================    #
class Gain(DomainBehavior):
	"""	Atomic model of gain
	"""

	###
	def __init__(self, k=1.0):
		""" Constructor.

			@param k : gain
		"""
		DomainBehavior.__init__(self)

		# state variable
		self.state = {	'status':	'IDLE', 'sigma': INFINITY}

		# Local copy
		self.k = k	# Gain y=k*x (QSS1/3)
		
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
		self.changeState('ACTIF',0)
		
	###
	def outputFnc(self):
		assert(self.msg!=None)
		self.msg.value = list(imap(lambda x: self.k*x,self.msg.value))
		self.msg.time = self.timeNext
		self.poke(self.OPorts[0], self.msg)

	###
	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status']=status
		self.state['sigma']=sigma

	def __str__(self):return "Gain"