# -*- coding: iso-8859-1 -*-

try:
	from DomainInterface.DomainStructure import DomainStructure
except ImportError :
	import sys,os
	for spath in [os.pardir+os.sep+'Lib']:
		if not spath in sys.path: sys.path.append(spath)
	from DomainInterface.DomainStructure import DomainStructure

class MythDomainStructure(DomainStructure):
	'''	Abstract class of PowerSystems Behavioral Structure.
	'''
	###
	def __init__(self):
		''' Constructor.
		'''
		DomainStructure.__init__(self)