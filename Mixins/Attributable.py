# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Attributable.py ---
#                     --------------------------------
#                        Copyright (c) 2013
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 19/11/13
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

#---------------------------------------------------------
class Attributable:
	"""  AttributeEditor mixin class to edit shape properties
	"""

	### Static variable for default graphical properties display
	GRAPHICAL_ATTR = [	'label',\
						'label_pos',\
						'pen',\
						'fill',\
						'font',\
						'image_path',\
					 	'input',\
					  	'output']

	###
	def __init__(self):
		""" Constructor.
		"""
		### list of attributes
		self.attributes = []

	###
	def AddAttribute(self, name, typ=""):
		""" Add attribute if not exist
		"""

		if not hasattr(self, name):
			setattr(self, name, typ)
			self.attributes.append(name)

	###
	def GetAttributes(self):
		""" Return attributes attribute
		"""
		return self.attributes

	###
	def SetAttributes(self, L):
		""" Set attributes list
		"""
		assert(isinstance(L,list))

		### set attribute
		for name in L:
			if not hasattr(self, name):
				setattr(self, name, '')

		### set attributes list
		self.attributes = L

	###
	def AddAttributes(self, attrs):
		""" Extend attributes list
		"""
		for attr in [a for a in attrs if a not in self.attributes]:
			self.attributes.append(attr)

	###
	def RemoveAttribute(self, name):
		""" Remove attribute name
		"""
		### delete the attribute
		if hasattr(self,name):
			delattr(self, name)

		### remove name from attributes list
		if name in self.attributes:
			self.attributes.remove(name)

def main():
    pass

if __name__ == '__main__':
    main()
