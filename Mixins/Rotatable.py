# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Rotatable.py ---
#                     --------------------------------
#                        Copyright (c) 2014
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 21/03/14
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
class Rotatable:
	""" Mixin to create rotatable component which can rotate under 4 directions \
	(est, ouest, nord, sud)
	"""

	###
	def __init__(self):
		""" Constructor.
		"""
		self.direction = "ouest"

	###
	def OnRotateR(self, event):
		""" Rotate on the left
		"""
		if self.direction == "ouest":
			self.direction = "nord"
		elif self.direction == "nord":
			self.direction = "est"
		elif self.direction == "est":
			self.direction = "sud"
		else:
			self.direction = "ouest"

	###
	def OnRotateL(self, event):
		""" Rotate on the right
		"""
		if self.direction == "ouest":
			self.direction = "sud"
		elif self.direction == "nord":
			self.direction = "ouest"
		elif self.direction == "est":
			self.direction = "nord"
		else:
			self.direction = "est"

def main():
    pass

if __name__ == '__main__':
    main()
