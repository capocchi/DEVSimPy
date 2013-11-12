# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# MasterModel.py --- DEVS Coupled Master  Model
#                     --------------------------------
#                        Copyright (c) 2010
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified:
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
#  GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from DEVSKernel.DEVS import CoupledDEVS

#    ======================================================================    #
class Master(CoupledDEVS):
	""" Master class represent the hight abstract level DEVS coupled model.
	"""
	FINAL_TIME = 10.0
	
	###
	def __init__(self):
		"""	Constructor method.
		"""
		CoupledDEVS.__init__(self)
		
		### param definition
		#self.VERBOSE = False
		#self.FAULT_SIM = False
		#self.PRIORITY_LIST = []

	####
	#def select(self, immList):
		#""" DEVS select function
		#"""
		##print self.PRIORITY_LIST
		##for model in self.PRIORITY_LIST:
		#for model in self.componentSet:
			#if model in immList:
				##print 'chose %s'%model.getBlockModel()
				#return model
		
		## si self.PRIORITY_LIST est vide on bascule sur une simulation sans priorité
		#return immList[0]
	###
	def __str__(self):
		return self.__class__.__name__