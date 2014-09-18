# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DomainBehavior.py --- Domaine Behavior virtual class
#                     --------------------------------
#                        Copyright (c) 2009
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 14/07/09
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
#  GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

try:
	# heritage des proprietes de l'AtomicModel par domainBehavior 
	import Core.DEVSKernel.DEVS as DEVS
except:
	import sys, os

	for spath in [os.pardir + os.sep + 'Lib']:
		if not spath in sys.path: sys.path.append(spath)
	import Core.DEVSKernel.DEVS as DEVS

# composition DomainBehavior est compose d'un Master
from MasterModel import Master

#======================================================================#

class DomainBehavior(DEVS.AtomicDEVS):
	""" Abstract DomainBehavior class.
	"""

	###
	def __init__(self):
		"""	Constructor.
		"""
		DEVS.AtomicDEVS.__init__(self)


	###
	def faultTransition(self):
		"""
			Delta fault transition function
		"""
		pass