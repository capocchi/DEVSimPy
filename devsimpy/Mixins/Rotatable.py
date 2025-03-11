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

		self.dir = ('ouest', 'nord', 'est', 'sud')

		self.input_direction = 'ouest'
		self.output_direction = 'est'

	def __SetDirection(self, direction, val):
		""" Private method to set the direction attribute.
		"""
		if direction == self.input_direction:
			self.input_direction = val
		else:
			self.output_direction = val

	###
	def __Rotate(self, direction:str, way:str):
		""" Private method to rotate the block depending on the direction and the way.
		"""

		assert direction in (self.input_direction, self.output_direction)
		assert way in ('right','left')

		index = self.dir.index(direction)
		gap = 1 if way == 'right'else -1
		n = index + gap

		self.__SetDirection(direction, self.dir[n%len(self.dir)])

		### test if there is layering between input and output
		if self.input_direction == self.output_direction:
			n = n + gap
			self.__SetDirection(direction, self.dir[n%len(self.dir)])
			
	###
	def OnRotateInputR(self, event):
		""" Rotate on the right for input ports.
		"""

		self.__Rotate(self.input_direction,'right')
	###
	def OnRotateInputL(self, event):
		""" Rotate on the left for input ports.
		"""
		self.__Rotate(self.input_direction,'left')

	###
	def OnRotateOutputR(self, event):
		""" Rotate on the right for output ports.
		"""
		self.__Rotate(self.output_direction,'right')

	###
	def OnRotateOutputL(self, event):
		""" Rotate on the left for output ports.
		"""
		self.__Rotate(self.output_direction,'left')

	###
	def OnRotateR(self, event):
		""" Rotate on the left for all ports.
		"""
		self.OnRotateInputR(event)
		self.OnRotateOutputR(event)

	###
	def OnRotateL(self, event):
		""" Rotate on the right for all ports.
		"""
		self.OnRotateOutputL(event)
		self.OnRotateInputL(event)

def main():
    pass

if __name__ == '__main__':
    main()
