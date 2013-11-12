# -*- coding: utf-8 -*-


from DomainInterface.DomainStructure import DomainStructure

class FuzzyDomainStructure(DomainStructure):
	'''	Abstract class of PowerSystems Behavioral Structure.
	'''
	###
	def __init__(self):
		''' Constructor.
		'''
		DomainStructure.__init__(self)
