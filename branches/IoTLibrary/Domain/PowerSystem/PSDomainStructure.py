# -*- coding: utf-8 -*-

try:
	from DomainInterface.DomainStructure import DomainStructure
except ImportError :
	import sys,os
	for spath in [os.pardir+os.sep+os.pardir+os.sep]:
		if not spath in sys.path: sys.path.append(spath)
	from DomainInterface.DomainStructure import DomainStructure

class PSDomainStructure(DomainStructure):
	'''	Abstract class of PowerSystems Behavioral Structure.
	'''
	###
	def __init__(self):
		''' Constructor.
		'''
		DomainStructure.__init__(self)
