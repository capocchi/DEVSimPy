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

import __builtin__

### just for individual test
if __name__ == '__main__':
	import os
	import sys

	__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"
	__builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {\
	'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),\
	'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}

    ### permit correct import (based on from instruction) in PyPDEVS directory (logger, util...) when this module executed (main)
	d = sys.path.append(os.pardir)
	if d not in sys.path:
		sys.path.append(d)

import re
import os

### import the DEVS module depending on the selected DEVS package in DEVSKernel directory
for pydevs_dir in __builtin__.__dict__['DEVS_DIR_PATH_DICT']:
    if pydevs_dir == __builtin__.__dict__['DEFAULT_DEVS_DIRNAME']:
        path = __builtin__.__dict__['DEVS_DIR_PATH_DICT'][pydevs_dir]
        ### split from DEVSKernel string and replace separator with point
        d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')
        exec "import DEVSKernel%s.DEVS as BaseDEVS"%(d)

#    ======================================================================    #
class DomainBehavior(BaseDEVS.AtomicDEVS):
	""" Abstract DomainBehavior class.
	"""

	###
	def __init__(self, name=""):
		"""	Constructor.
		"""

		BaseDEVS.AtomicDEVS.__init__(self, name=name)

	###
	def poke(self, p, v):
		""" Overwrite here the poke method in order to adapt the model with all simulator (PyDEVS, PyPDEVS, etc...)
		"""
		if 'PyDEVS' in __builtin__.__dict__['DEFAULT_DEVS_DIRNAME']:
			BaseDEVS.AtomicDEVS.poke(self, p, v)
		### PyPDEVS
		else:
			from Object import Message
			if isinstance(v, Message):
				v = v.value
			return {p:v}

#	def peek(self, p):
#		""" Overwrite here the peek method in order to adapt the model with all simulator (PyDEVS, PyPDEVS, etc...)
#		"""
#		if 'PyDEVS' in __builtin__.__dict__['DEFAULT_DEVS_DIRNAME']:
#			return BaseDEVS.AtomicDEVS.peek(self, p)
#		else:
#			return self.myInput[p]

	def __str__(self):
		"""
		"""
		if hasattr(self, 'bloclModel'):
			return self.blockModel.label
		else:
			return self.__class__.__name__

def main():
	DB = DomainBehavior()
	print DB.__class__.__bases__

if __name__ == '__main__':
	main()
