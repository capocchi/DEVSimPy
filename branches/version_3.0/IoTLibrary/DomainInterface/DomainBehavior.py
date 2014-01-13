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

### jsut for individual test
if __name__ == '__main__':
	import os
	import sys

	__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"
	__builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {\
	'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),\
	'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}

    ### permit correct import (based on fom instruction) in PyPDEVS directory (logger, util...) when this module executed (main)
	d = sys.path.append(os.pardir)
	if d not in sys.path:
		sys.path.append(d)

##### Get .devsimpy file
##import wx
##sp = wx.StandardPaths.Get()
##config_file_path = os.path.join(sp.GetUserConfigDir(), '.devsimpy')
##
##### if config file exist
##if os.exists(config_file_path):
##
##	f = open(config_file_path, 'r')
##	for line in  f.readlines():
##		if 'builtin_dict' in line:
##			exec line
##			break
##	f.close()
##
##	### try to find builtin_dict variable in config file
##	try:
##		DEFAULT_DEVS_DIRNAME = builtin_dict['DEFAULT_DEVS_DIRNAME']
##	### if config file not contain builtin_dict, we load it from builtin definde by devsimpy.py before all import...
##	except NameError:
##		import __builtin__
##        DEFAULT_DEVS_DIRNAME =__builtin__.__dict__['DEFAULT_DEVS_DIRNAME']


for pydevs_dir in __builtin__.__dict__['DEVS_DIR_PATH_DICT']:
	if pydevs_dir == __builtin__.__dict__['DEFAULT_DEVS_DIRNAME']:
		exec "import DEVSKernel.%s.DEVS as BaseDEVS"%(pydevs_dir)

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
	def faultTransition(self):
		"""
			Delta fault transition function
		"""
		pass

def main():
	DB = DomainBehavior()
	print DB.__class__.__bases__

if __name__ == '__main__':
	main()