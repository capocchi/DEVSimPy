# -*- coding: utf-8 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# FuzzyAtomiciDEVS.py --- Librairie de mod�les iDEVS
# FuzzyAtomiciDEVS.py --- iDEVS's models
#
#                     --------------------------------
#                        Copyright (c) 2009
#                       Paul-Antoine Bisgambiglia
#			bisgambiglia@univ-corse.fr
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 01/06/09
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##
## GENERAL NOTES AND REMARKS:
##	Python 2.5.2 (r252:60911, Jul 31 2008, 17:28:52)
##	[GCC 4.2.3 (Ubuntu 4.2.3-2ubuntu7)] on linux2
##
## fonctionne pour 1 port in et un port out
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from Domain.Fuzzy.FuzzyDomainBehavior import *
import math

#    ======================================================================    #
class FuzzyAtomiciDEVS(FuzzyDomainBehavior):
	'''	Mod�le atomique iDEVS de fuzzification. 
		Application power system stator model
	'''

	###
	def __init__(self,left=10,right=10):
		'''	Constructeur
		'''
		FuzzyDomainBehavior.__init__(self)
		#local copy
		self.left = left # left
		self.right = right # right
		self.state["sigma"] = INFINITY

	###
	def extTransition(self):
		'''
			Application de la fuzzification
		'''

		self.msg=self.peek(self.IPorts[0])
		self.state["sigma"] = 0
	
	###
	def intTransition(self): self.state["sigma"] = INFINITY

	###
  	def outputFnc(self):
		fuzzResult=[]
		# pour chaque valeur du sinus (derivée 1 et 2)
		for v in self.msg.value:
			if 0.1< self.timeNext <0.2:
				self.right=100
				fuzzResult.append(FuzzyInt(a=v,b=v,psi=v-(self.left*abs(v))/100,omega=v+(self.right*abs(v))/100))
			else:
				self.right=10
				fuzzResult.append(FuzzyInt(a=v,b=v,psi=v-(self.left*abs(v))/100,omega=v+(self.right*abs(v))/100))

		self.msg.value=fuzzResult
		self.msg.time=self.timeNext
		self.poke(self.OPorts[0], self.msg)

	###
	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self):return "FuzzyAtomiciDEVS"

