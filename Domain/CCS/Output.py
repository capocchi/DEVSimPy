# -*- coding: utf-8 -*-

"""
	This model represents the Hidden layer of an artificiel neural network
	@author: Samuel TOMA
	@organization: University of Corsica
	@contact: toma@univ-corse.fr
	@since: 2010.12.10
	@version: 1.1 beta
"""

### Specific import ------------------------------------------------------------
from Hidden import Hidden

### Model class ----------------------------------------------------------------
class Output(Hidden):
	""" Output Layer
	"""
	
	def __str__(self):
		return 'Output'