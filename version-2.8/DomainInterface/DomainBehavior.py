# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DomainBehavior.py --- Domaine Behavior virtual class
#                     --------------------------------
#                        Copyright (c) 2009
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 14/07/09
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

class DomainBehavior(PyDEVS.AtomicDEVS, PyPDEVS.AtomicDEVS):
	""" Abstract DomainBehavior class.
	"""

	###
	def __init__(self, name=""):
		"""	Constructor.
		"""

		eval("%s.AtomicDEVS.__init__(self, name)"%DEFAULT_DEVS_DIRNAME)

	###
	def faultTransition(self):
		"""
			Delta fault transition function
		"""
		pass

def main():

	DB= DomainBehavior()
	print inspect.getmodule(DB)

if __name__ == '__main__':
	import inspect
	import __builtin__
	__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"

	main()