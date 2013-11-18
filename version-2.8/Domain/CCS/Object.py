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

#import collections

#Message = collections.namedtuple('Message', 'value time')

class Message:
	'''	The class Message provide the activation of all DEVS components.


		@ivar value:

		@type value: None
		@type operation: string
	'''

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
		
class NeuralMessage(object):
	
	def __init__(self,layerId, simList=None, simId=None, timeNext=None):
		self.layerId = layerId
		self.timeNext = timeNext
		if simList is None and simId is None:
			self.simList = {}
		elif simList is not None and simId is None:
			self.simList = {0:simList}
		else:
			print simList
			self.simList = {simdId:simList}
			
	def addSim(self,simId,Test,Valid =None):
		""" # T,V could be the training and validation outputs --> floats,
			# validation could simply be None if there is no validation phase,
			# When V is None this might mean that T is the error list for the error models
		"""
		if Valid is not None:
			self.simList[simId] = [Test,Valid]
		else:
			self.simList[simId] = [Test,None]