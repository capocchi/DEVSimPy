# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# MasterModel.py --- DEVS Coupled Master  Model
#                     --------------------------------
#                        Copyright (c) 2010
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 24/11/2013
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

### jsut for individual test
if __name__ == '__main__':
	import os
	import sys

	__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"
	__builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}

    ### permit correct import (based on fom instruction) in PyPDEVS directory (logger, util...) when this module executed (main)
	d = sys.path.append(os.pardir)
	if d not in sys.path:
		sys.path.append(d)

for pydevs_dir in __builtin__.__dict__['DEVS_DIR_PATH_DICT']:
	if pydevs_dir == __builtin__.__dict__['DEFAULT_DEVS_DIRNAME']:
		exec "import DEVSKernel.%s.DEVS as BaseDEVS"%(pydevs_dir)

###    ======================================================================    #
class Master(BaseDEVS.CoupledDEVS):
	""" Master class represent the hight abstract level DEVS coupled model.
	"""
	FINAL_TIME = 10.0

	###
	def __init__(self, name=""):
		"""	Constructor method.
		"""
		BaseDEVS.CoupledDEVS.__init__(self, name=name)

	###
	def __str__(self):
		return self.__class__.__name__

def main():
	master = Master()
	print master.__class__.__bases__

if __name__ == '__main__':
	main()