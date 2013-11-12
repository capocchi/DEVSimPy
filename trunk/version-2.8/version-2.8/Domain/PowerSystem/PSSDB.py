# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DataBase.py ---
#                     --------------------------------
#                        Copyright (c) 2009
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 28/04/09
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
#  GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
#  GLOBAL VARIABLES AND FUNCTIONS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

try:
	from DomainInterface.SDB import SDB
except ImportError :
	import sys,os
	for spath in [os.curdir+os.sep+'Lib']:
  		if not spath in sys.path: sys.path.append(spath)
	from DomainInterface.SDB import SDB

class PSSDB(SDB):
 	'''	 
	'''

	###
	def __init__(self, paramDico = {}):
		'''	Constructor

			@param paramDico: Dictionary used for storage of the user parameters

		'''
		SDB.__init__(self)

		# a essayer !
		#for key in paramDico:
		  #exec "self." + key +'=paramDico[\''+key+'\']'
		  
		# user macro
		self.VERBOSE 				= paramDico['VERBOSE']
		self.FINAL_TIME				= paramDico['FINAL_TIME']
		self.FAULT_SIM				= paramDico['FAULT_SIM']
		self.WITH_COUPLED_SOLVER 	= paramDico['WITH_COUPLED_SOLVER']
		
	def SetAttribut(self,name, value):
		exec "self."+name+"="+str(value)