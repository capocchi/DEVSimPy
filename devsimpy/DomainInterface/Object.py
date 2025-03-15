# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Object.py ---
#                     --------------------------------
#                        Copyright (c) 2009
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified:
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

	###
	def __init__(self, v = None, t = None):
		''''	Constructor method.

			@param v: Value of the transaction
			@param t : simulation time
		'''

		# make local copy
		self.value 	= v
		self.time	= t
		self.name = ""

	def copy(self):
		''' Create a copy of the current instance.
			@return: A new instance of Message with the same attributes.
			@rtype: Message
		'''
		return Message(self.value, self.time)
	
	###
	def __str__(self):
		'''	Printer method.
			@return: Object representation.
			@rtype: str
		'''
		return "<< value = %s; time = %s>>"%(self.value, self.time)

