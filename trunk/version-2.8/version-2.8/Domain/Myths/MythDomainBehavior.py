# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior

class MythDomainBehavior(DomainBehavior):
	'''	Abstract class of Power Systemes Behavioral Domain.
	'''
	
	###
	def __init__(self):
		''' Constructor method.
		'''
		DomainBehavior.__init__(self)