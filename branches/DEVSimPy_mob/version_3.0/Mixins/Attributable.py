# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Attributable.py ---
#                     --------------------------------
#                          Copyright (c) 2013
#                           Laurent CAPOCCHI
#                         University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 29/01/2013
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
# Mixin
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#---------------------------------------------------------
class Attributable:
	"""     Allows AttributeEditor to edit specified properties of the Shape
	"""

	### Static variable for default graphical properties display
	GRAPHICAL_ATTR = ['label', 'label_pos', 'pen','fill', 'font', 'image_path','input','output']

	def __init__(self):
		""" Constructor
		"""
		self.attributes = []

	def AddAttribute(self, name, typ=""):
		### add attribute if not exist
		if not hasattr(self, name):
			setattr(self, name, typ)

		self.attributes.append(name)

	def GetAttributes(self):
		return self.attributes

	def SetAttributes(self, L):
		""" Set attributes list
		"""
		assert (isinstance(L, list))
		#assert(False not in map(lambda txt: hasattr(self,txt),L))

		### set attribute
		for name in L:
			if not hasattr(self, name):
				setattr(self, name, '')

		### set attributres list
		self.attributes = L

	def AddAttributes(self, atts):
		""" Extend attributes list
		"""
		self.attributes.extend(atts)

	def RemoveAttribute(self, name):
		""" Remove attribute name
		"""
		### delete the attribute 
		if hasattr(self, name):
			delattr(self, name)

		### remove name from attributes list
		if name in self.attributes:
			self.attributes.remove(name)

		#def IsGraphicalAttribute(self, attr):
		#return attr in Attributable.GRAPHICAL_ATTR

		#def IsBehavioralAttribute(self, attr):
		#return not self.IsGraphicalAttribute(attr)

