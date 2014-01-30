# -*- coding: utf-8 -*-

"""
Name : ExternalGen.py
Brief descritpion : External data generator atomic model (abstract)
Author(s) : Celine NICOLAI(cnicolai@univ-corse.fr), Bastien POGGI(bpoggi@univ-corse.fr), Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0
Last modified : 14/10/10
GENERAL NOTES AND REMARKS:0
***
GLOBAL VARIABLES AND FUNCTIONS:
"""

from Domain.Generator.ExternalGen import *
from Domain.Generator.fusionTable.fusionTable import Request

import os.path

#    ======================================================================    #
class DataBaseGen(ExternalGen):
	"""
        Generic Event generator
	"""

	###
	def __init__(self, sourceName="265331", annee="1995"):
		""" Constructor.
		"""

		ExternalGen.__init__(self)

		# local copy
		self.sourceName = sourceName
		self.annee= annee

		if(self.sourceName!="" and self.annee!=""):
			myRequester = Request(self.sourceName,"Semaine",self.annee) #ID TABLE | ANNEE
			self.V = myRequester.getListData() # time list
			self.T = myRequester.getListTime() # value list
			print self.V
			print self.T
			sig = self.T[0] if self.T != [] else INFINITY
		else:
			sig = INFINITY
			
		self.state = {	'status':	'ACTIVE', 'sigma':	sig}

	###
	def __str__(self):
            return "DataBaseGen"
