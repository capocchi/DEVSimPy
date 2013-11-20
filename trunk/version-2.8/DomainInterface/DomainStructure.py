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

import os
import imp
import inspect
import sys

### jsut for individual test
if __name__ == '__main__':

	### permit correct import (based on fom instruction) in PyPDEVS directory (logger, util...) when this module executed (main)
	d = sys.path.append(os.pardir)
	if d not in sys.path:
		sys.path.append(d)

import DEVSKernel.PyDEVS.DEVS as PyDEVS
import DEVSKernel.PyPDEVS.DEVS as PyPDEVS

#    ======================================================================    #

class DomainStructure(PyDEVS.CoupledDEVS, PyPDEVS.CoupledDEVS):
	""" Abstract DomainStructure class.
	"""

	###
	def __init__(self, name=""):
		"""Constructor.
		"""

		eval("%s.CoupledDEVS.__init__(self, name)"%DEFAULT_DEVS_DIRNAME)

def main():

	DB= DomainStructure()
	print inspect.getmodule(DB)

if __name__ == '__main__':
	import inspect
	import __builtin__
	__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"

	main()