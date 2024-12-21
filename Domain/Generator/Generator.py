# -*- coding: utf-8 -*-

"""
Name: Generator.py
Brief descritpion:
Author(s): L. Capocchi <capocchi@univ-corse.fr>
Version:  1.0
Last modified: 2011.11.16
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""


from DomainInterface.DomainBehavior import DomainBehavior
from Basic.Object import Message

import os.path

#    ======================================================================    #
class Generator(DomainBehavior):
	""" Base class for generators
	"""

	def __init__(self, sourceName="", listValues=[]):
		""" Constructor.

			@sourceName : name of source
			@listValues : list of values
		"""
		DomainBehavior.__init__(self)

		### local copy
		self.sourceName = sourceName
		self.__listValues = listValues

		self.T = []
		self.V = {}

		### flags
		self.type_error_flag = True in [not isinstance(a, int) for a in self.__listValues]
		self.file_error_flag = os.path.exists(self.sourceName)
		self.list_empty_flag = listValues == []

		### assert
		if self.type_error_flag: assert True, "Please use integer in listValue parameter !"

	@staticmethod
	def initDictionnaryValues(values):
		if values == []:
			return {0:[]}
		else:
			return dict([(value,[])for value in values])

	def intTransition(self):
		try:
			s = self.T[1]-self.T[0]
			del self.T[0]
		except IndexError:
			s = INFINITY

		self.state['sigma'] = s

	def outputFnc(self):
		### si la listValues est vide, cela veux dire qu'on veut toutes les valeurs des lignes sur une sortie
		if self.__listValues != []:
			assert(len(self.OPorts) == len(self.__listValues))
			for item in self.__listValues:
				data = [self.V[item].pop(0), 0.0, 0.0]
				msg = Message(data, self.timeNext)
				i = self.__listValues.index(item)

				self.poke(self.OPorts[i], msg)
		else:
			data = [self.V[0].pop(0), 0.0, 0.0]
			msg = Message(data, self.timeNext)
			self.poke(self.OPorts[0], msg)

	def timeAdvance(self): return self.state['sigma']

	def __str__(self): return "Generator"

##Gestion du temps (conversions)
#
#        def exploseTime(T,outPutTime):
#            maliste = []
#            for t in T:
#                maliste += creerListTemps(outPutTime,t)
#            print maliste
#
#        def exploseValue(V,outPutTime):
#            maliste = []
#            for v in V:
#                maliste += creerListValeur(outPutTime,v)
#                print maliste
#
#        def creerListTemps(num,temps):
#            return map(lambda t: (t*num)+temps, range(1,int(1/num)+1))
#
#        def creerListValeur(num,valeur):
#            return map(lambda v: num*valeur,range(1,int(1/num)+1))
