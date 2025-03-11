# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        	FusionTableGenerator.py

 Model:
 Authors:      	Bastien Poggi University Of Corsica Laboratory SPE
				bpoggi@univ-corse.fr

 Date:      	2010-09-30
-------------------------------------------------------------------------------
"""

from .Generator.Generator import *
from .Generator.fusionTable.fusionTable import Request
import os.path

#    ======================================================================    #
class FusionTableGenerator(Generator):
	"""
	This module extract data from a googleFusionTable and use it with DEVS formalism
	"""

	def __init__(self, TableId="315898",listValues=["Temperature"],time="Semaine",outPutFrequency=1.0, login="", password=""):
		"""
		TODO Gérer time = None

			@TableId :file path of model
			@listValues : numbers or strings of considered columns
			@time : name of time column
			@outPutFrequency : sigma step
			@login : required google login
			@password : required google password
		"""


		Generator.__init__(self, TableId, listValues)

		self.time = time
		self.outPutFrequency = outPutFrequency
		self.V = self.initDictionnaryValues(listValues)

		if(self.sourceName!="" and len(list(self.V.keys()))>0):
			for columns in list(self.V.keys()):

				myRequester = Request(self.sourceName,self.time,columns,login, password) #ID TABLE | ANNEE

				self.V[columns] = myRequester.getListData() # time list

			self.T = myRequester.getListTime() # value list
			self.state = {'status':'ACTIVE','sigma':self.T[0]}
		else:
			self.state = {'status':'ACTIVE','sigma':INFINITY}

	def __str__(self):
		return "FusionTableGenerator"
