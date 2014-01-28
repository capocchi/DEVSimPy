# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DomainStructure.py --- Domaine Structure virtual class
#                     --------------------------------
#                        Copyright (c) 2003
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 7/12/04
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
	# heritage des propri�t�s du CoupledModel par domainStructure
	import Core.DEVSKernel.DEVS as DEVS
except:
	import sys, os

	for spath in [os.pardir + os.sep + 'Lib']:
		if not spath in sys.path: sys.path.append(spath)
	import Core.DEVSKernel.DEVS as DEVS

#======================================================================#

class DomainStructure(DEVS.CoupledDEVS):
	""" Abstract DomainStructure class.
	"""

	###
	def __init__(self):
		"""Constructor.
		"""
		DEVS.CoupledDEVS.__init__(self)

		self.dynamicComponentSet = []
		self.dynamicIC = []
		self.dynamicEIC = []
		self.dynamicEOC = []