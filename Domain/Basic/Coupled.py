# -*- coding: utf-8 -*-

"""
Name : Coupled.py
Brief description : Basic DEVS coupled model
Authors : Laurent CAPOCCHI
Version : 1.0
Last modified : 12/02/10
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS
"""

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