# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Object.py ---
#                     --------------------------------
#                        Copyright (c) 2011
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 05/12/11
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
#  GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class Message:
	'''	The class Message provide the activation of all DEVS components.


		@ivar value:
	
		@type value: None
		@type operation: string
	'''
	__slots__ = ("value", "time", "name")

	###
	def __init__(self, v=None, t=None):
		''''	Constructor method.

			@param v: Value of the transaction
			@param t : simulation time
		'''

		# make local copy
		self.value 	= v
		self.time	= t
		
		self.name = ""

	###
	def __str__(self):
		'''	Printer method.
			@return: Object representation.
			@rtype: str
		'''
		return "<< value = %s, time = %s>>"%(self.value, self.time)

