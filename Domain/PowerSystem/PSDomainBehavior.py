# -*- coding: utf-8 -*-

try:
	from DomainInterface.DomainBehavior import DomainBehavior, Master
except ImportError:
	import sys,os
	for spath in [os.pardir+os.sep+os.pardir+os.sep]:
		if not spath in sys.path: sys.path.append(spath)
	from DomainInterface.DomainBehavior import DomainBehavior, Master

class PSDomainBehavior(DomainBehavior):
	'''	Abstract class of Power Syst�mes Behavioral Domain.
	'''
	
	###
	def __init__(self):
		''' Constructor method.
		'''
		DomainBehavior.__init__(self)
