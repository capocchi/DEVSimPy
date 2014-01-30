# -*- coding: utf-8 -*-

"""
Name : DataBaseGen.py
Brief descritpion : External data generator atomic model (abstract)
Author(s) : Celine NICOLAI(cnicolai@univ-corse.fr), Bastien POGGI(bpoggi@univ-corse.fr), Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0
Last modified : 14/10/10
GENERAL NOTES AND REMARKS:0
***
GLOBAL VARIABLES AND FUNCTIONS:
"""

from Domain.Generator.ExternalGen import *

import os.path

#    ======================================================================    #
class FileGen(ExternalGen):
	"""
        Generic Event generator
	"""

	###
	def __init__(self, fileName=os.path.join(os.getcwd(),"fichier.csv")):
		""" Constructor
		
			@fileName = file path
		"""

		ExternalGen.__init__(self)

		self.V = {	}	# value list
		self.fileName = fileName

		if os.path.exists(self.fileName):
			with open(self.fileName,"rb") as f:
				for l in filter(lambda b: b != '' , map(lambda a: a.replace('\n', ''), f.readlines())):
						self.T.append(float(l.split(' ')[0]))
						self.V.append(float(l.split(' ')[1]))
						
			### sigma definition
			sig = self.T[0] if self.T != [] else INFINITY
		else:
			sig = INFINITY
		
		# State variables
		self.state = {	'status':	'ACTIVE', 'sigma':	sig}

	###
	def __str__(self):
            return "FileGen"
