# -*- coding: utf-8 -*-

"""A class that contain all the necessary information about one simulation.

this class contain the weight list, learning factor and momentum, 
the bias, the activation function type and a list of the inputs and outputs 
of this network layer.

"""

class Signature(object):
	""" TODO
	"""
	def __init__(self, *args, **kwargs):
		""" TODO
		"""
		
		for key,value in kwargs.items():
			setattr(self, key, value)
		
		for val in args:
			if isinstance(val, dict):
				for k,v in val.items():
					setattr(self, k, v)
			elif isinstance(val, list):
				for c in filter(lambda a: isinstance(a, (tuple,list)), val):
					setattr(self, c[0], c[1])
	
	#def inputsUpdate(self,updatedInputs):
		#if updatedInputs.__class__.__name__ in ('list','tuple'):
			#self.inputs = updatedInputs
		#else:
			#print "Error updating inputs list, should be a list or a tuple" 
	
	#def outputsUpdate(self, updatedOutputs):
		#if updatedOutputs.__class__.__name__ in ('list','tuple'):
			#self.outputs = updatedOutputs
		#else:
			#print "Error updating outputs list, should be a list or a tuple" 
