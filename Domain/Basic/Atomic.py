# -*- coding: utf-8 -*-

"""
Name : Atomic.py
Brief description : Basic DEVS atomic model
Authors : Laurent CAPOCCHI
Version : 1.0
Last modified : 12/02/10
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS
"""

from DomainInterface.DomainBehavior import DomainBehavior

class Atomic(DomainBehavior):
	"""	Basic atomic model.
	"""
	
	###
	def __init__(self):
		"""Constructor.
		"""
		DomainBehavior.__init__(self)
		
	def __str__(self):
		return "Atomic"