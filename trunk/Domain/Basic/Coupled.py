# -*- coding: utf-8 -*-

from DomainInterface.DomainStructure import DomainStructure

class Coupled(DomainStructure):
	""" Basic coupled model. 
	"""

	###
	def __init__(self):
		"""Constructor.
		"""
		DomainStructure.__init__(self)
		
	def __str__(self): return "Coupled"