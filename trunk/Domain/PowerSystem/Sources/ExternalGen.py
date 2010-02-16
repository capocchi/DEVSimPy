# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ExternalGen.py --- External event generator from text file.
#                     --------------------------------
#                        	 Copyright (c) 2010
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/02/10
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

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message
	
import csv

#    ======================================================================    #
class ExternalGen(DomainBehavior):
	""" External event generator from text file.
	"""

	###
	def __init__(self, T=[0.0], V=[0.0], fileName="data.csv"):
		""" Constructor.
		"""

		DomainBehavior.__init__(self)
		
		# State variables
		self.state = {	'status':	'ACTIVE', 'sigma':	self.T[0]}

		# local copy
		self.T = T		# time list
		self.V = V		# value list
		self.fileName = fileName

		try:
			cr = open(self.fileName,"rb")
			
			for l in cr.readlines():
				self.T.append(float(l.split(' ')[0]))
				self.V.append(float(l.split(' ')[1]))
		except:
			pass
		
	###
  	def intTransition(self):

		try:
			s=self.T[1]-self.T[0]
		except IndexError:
			s=INFINITY

		self.state['sigma']=s

	###
  	def outputFnc(self):
		# Output message list
		L = [self.V.pop(0),0.0,0.0]
		del self.T[0]

		# envoie du message le port de sortie
		self.poke(self.OPorts[0], Message(L,self.timeNext))

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def __str__(self):return "ExternalGen"