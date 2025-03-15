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

### import the DEVS module depending on the selected DEVS package in DEVSKernel directory
#for pydevs_dir in builtins.__dict__['DEVS_DIR_PATH_DICT']:
#    if pydevs_dir == builtins.__dict__['DEFAULT_DEVS_DIRNAME']:
#        path = builtins.__dict__['DEVS_DIR_PATH_DICT'][pydevs_dir]
#        ### split from DEVSKernel string and replace separator with point
#        d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')

#        ### for py 3.X
#        import importlib
#        BaseDEVS = importlib.import_module("DEVSKernel%s.DEVS"%d)
#        
#        #exec("import DEVSKernel%s.DEVS as BaseDEVS"%(d))
        
from  DomainInterface import DomainStructure

###    ======================================================================    #
#class Master(BaseDEVS.CoupledDEVS):
class Master(DomainStructure):
	""" Master class represent the high abstract level DEVS coupled model.
	"""
	FINAL_TIME = 10.0

	###
	def __init__(self, name=""):
		"""	Constructor method.
		"""
		DomainStructure.__init__(self, name=name)
#		BaseDEVS.CoupledDEVS.__init__(self, name=name)

		self.FINAL_TIME = Master.FINAL_TIME

#	def getFlatComponentSet(self):
#	    """ get the list of composing submodels - recursive build
#	    """
#	    submodelList = {}
#	    for submodel in self.componentSet:
#	        submodelList.update(submodel.getFlatComponentSet())
#	    return submodelList

	###
	def __str__(self):
		return self.__class__.__name__
