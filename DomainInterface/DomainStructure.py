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

import builtins

### jsut for individual test
if __name__ == '__main__':
	import os
	import sys

	builtins.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"
	builtins.__dict__['DEVS_DIR_PATH_DICT'] = {\
	'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),\
	'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}

    ### permit correct import (based on fom instruction) in PyPDEVS directory (logger, util...) when this module executed (main)
	d = sys.path.append(os.pardir)
	if d not in sys.path:
		sys.path.append(d)

import re
import os

### import the DEVS module depending on the selected DEVS package in DEVSKernel directory
for pydevs_dir in builtins.__dict__['DEVS_DIR_PATH_DICT']:
    if pydevs_dir == builtins.__dict__['DEFAULT_DEVS_DIRNAME']:
        path = builtins.__dict__['DEVS_DIR_PATH_DICT'][pydevs_dir]
        ### split from DEVSKernel string and replace separator with point
        d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')
        
        ### for py 3.X
        import importlib
        BaseDEVS = importlib.import_module("DEVSKernel%s.DEVS"%d)

        #exec("import DEVSKernel%s.DEVS as BaseDEVS"%(d))

#    ======================================================================    #
class DomainStructure(BaseDEVS.CoupledDEVS):
	""" Abstract DomainStrucutre class.
	"""

	###
	def __init__(self, name=""):
		"""	Constructor.
		"""

		BaseDEVS.CoupledDEVS.__init__(self, name=name)

	def getFlatComponentSet (self):
	    """ get the list of composing submodels - recursive build
	    """
	    submodelList = {}
	    for submodel in self.getComponentSet():
	        submodelList.update(submodel.getFlatComponentSet())
	    return submodelList

	def getComponentSet(self)->list:
		""" return the component set attribute depending on the definition finded in the DEVS.py file
		"""
		if hasattr(self, 'componentSet'):
			return self.componentSet
		elif hasattr(self, 'component_set'):
			return self.component_set

	def setComponentSet(self,V:list)->None:
		""" set the component set attribute depending on the definition finded in the DEVS.py file
		"""
		if hasattr(self, 'componentSet'):
			self.componentSet = V
		elif hasattr(self, 'component_set'):
			self.component_set = V

	def addToComponentSet(self,V:list)->None:
		""" add values in components set attribute
		"""
		if hasattr(self, 'componentSet'):
			self.componentSet.extend(V)
		elif hasattr(self, 'component_set'):
			self.component_set.extend(V)

	def delToCompnentsSet(self,V:list)->None:
		""" del values in the components set attribute
		"""
		if hasattr(self, 'componentSet'):
			for v in V:
				self.componentSet.remove(v)
		elif hasattr(self, 'component_set'):
			for v in V:
				self.component_set.remove(v)

def main():
	DS = DomainStructure()

if __name__ == '__main__':
	main()
