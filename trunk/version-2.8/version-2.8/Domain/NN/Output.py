# -*- coding: utf-8 -*-

"""
	This model represents the Hidden layer of an artificiel neural network
	@author: Samuel TOMA
	@organization: University of Corsica
	@contact: toma@univ-corse.fr
	@since: 2010.12.10
	@version: 1.5
"""

### Specific import ------------------------------------------------------------
from Hidden import Hidden
import os
from random import randint

### Model class ----------------------------------------------------------------
class Output(Hidden):
	
	def __init__(self, 	bias = 0.0,
						activation_function = ("sigmoide","tanh","lineaire"),
						k = 1.0,
						a = -0.5,
						b = 0.5,
						fileName = os.path.join(os.getcwd(),"weights_%d"%randint(1,100)),
						learning_flag = True):
		""" constructor.
			@param bias 				= the bias value of hidden layer.
			@param activation_function 	= The type of the activation function.
			@param k					= param. of sigmoide activation function. exp(-kx)
			@param a					= weight initialization range [a,b]
			@param b					= weight initialization range [a,b]
			@param fileName				= weights file
			@param learning_flag		= model status - if true model write its weights at the end of simulation into a file then it read weights file
		"""
		Hidden.__init__(self, bias, activation_function, k, a, b, fileName, learning_flag)
		
	def __str__(self):
		return 'Output'