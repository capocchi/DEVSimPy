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

		self.dir = ['ouest', 'nord', 'est', 'sud']

		self.input_direction = "ouest"
		self.output_direction = "est"

	###
	def OnRotateInputR(self, event):
		""" Rotate on the right for input ports.
		"""

		index = self.dir.index(self.input_direction)
		n = index + 1
		self.input_direction = self.dir[n%len(self.dir)]

		### test if there is layering between input and output
		if self.input_direction == self.output_direction:
			n+=1
			self.input_direction = self.dir[n%len(self.dir)]
	###
	def OnRotateInputL(self, event):
		""" Rotate on the left for input ports.
		"""
		index = self.dir.index(self.input_direction)
		n = index - 1
		self.input_direction = self.dir[n%len(self.dir)]

		### test if there is layering between input and output
		if self.input_direction == self.output_direction:
			n-=1
			self.input_direction = self.dir[n%len(self.dir)]
	###
	def OnRotateOutputR(self, event):
		""" Rotate on the right for output ports.
		"""
		index = self.dir.index(self.output_direction)
		n = index + 1
		self.output_direction = self.dir[n%len(self.dir)]

		### test if there is layering between input and output
		if self.input_direction == self.output_direction:
			n+=1
			self.output_direction = self.dir[n%len(self.dir)]
	###
	def OnRotateOutputL(self, event):
		""" Rotate on the left for output ports.
		"""

		index = self.dir.index(self.output_direction)
		n = index - 1
		self.output_direction = self.dir[n%len(self.dir)]

		### test if there is layering between input and output
		if self.input_direction == self.output_direction:
			n-=1
			self.output_direction = self.dir[n%len(self.dir)]

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
