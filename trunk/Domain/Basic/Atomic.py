# -*- coding: utf-8 -*-

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