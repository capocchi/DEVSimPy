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

### just for individual test
if __name__ == '__main__':
	import os
	import sys

	__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"
	__builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}

    ### permit correct import (based on fom instruction) in PyPDEVS directory (logger, util...) when this module executed (main)
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

#import DomainStructure

###    ======================================================================    #
class Master(BaseDEVS.CoupledDEVS):
#class Master(DomainStructure.DomainStructure):
	""" Master class represent the high abstract level DEVS coupled model.
	"""
	FINAL_TIME = 10.0

	###
	def __init__(self, name=""):
		"""	Constructor method.
		"""
#		DomainStructure.DomainStructure.__init__(self, name=name)
		BaseDEVS.CoupledDEVS.__init__(self, name=name)

		self.FINAL_TIME = Master.FINAL_TIME

	def getFlatComponentSet(self):
	    """ get the list of composing submodels - recursive build
	    """
	    submodelList = {}
	    for submodel in self.componentSet:
	        submodelList.update(submodel.getFlatComponentSet())
	    return submodelList


	###
	def __str__(self):
		return self.__class__.__name__

def main():
	master = Master()

if __name__ == '__main__':
	main()
