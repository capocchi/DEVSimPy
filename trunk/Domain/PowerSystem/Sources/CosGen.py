# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# CosGen.py --- Cosinus atomic model
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

from SinGen import *

#    ======================================================================    #
class CosGen(SinGen):
	"""	Cosinus atomic model.
	"""

	###
	def __init__(self, a=1, f=50, phi=0, k=20, m='QSS2'):
		"""	Constructor.
		"""
		SinGen.__init__(self, a, f, phi, k, m)
		
	###
  	def outputFnc(self):
		
		# output message list
		L = [self.a*cos(self.w*(self.timeNext)+self.phi)]
		
		if (self.m=='QSS2'):
			L.append(-self.a*self.w*sin(self.w*(self.timeNext)+self.phi))
		elif (self.m=='QSS3'):
			L.append(-self.a*self.w*sin(self.w*(self.timeNext)+self.phi))
			L.append(-self.a*pow(self.w,2)*cos(self.w*(self.timeNext)+self.phi)/2 )

		# envoie du message le port de sortie
		for i in range(len(self.OPorts)):
			self.poke(self.OPorts[i], Message(L,self.timeNext))

	###
	def __str__(self):return "CosGen"
