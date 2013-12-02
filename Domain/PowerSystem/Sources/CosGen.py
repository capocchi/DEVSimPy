# -*- coding: utf-8 -*-

"""
Name : CosGen.py 
Brief descritpion : Cosinus generator atomic model 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 21/03/09
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from SinGen import *

#    ======================================================================    #
class CosGen(SinGen):
	"""	Cosinus atomic model.
	"""

	###
	def __init__(self, a=1, f=50, phi=0, k=20, m='QSS2'):
		"""	Constructor.
	
			@param a : amplitude
			@param f : frequency
			@param phi : phase
			@param k : step sample
			@param m : QSS methode choise
		"""
		SinGen.__init__(self, a, f, phi, k, m)
		
	###
  	def outputFnc(self):
		"""
		"""

		# output message list
		L = [self.a*cos(self.w*(self.timeNext)+self.phi), 0.0, 0.0]
		
		if (self.m=='QSS2'):
			L[1]=-self.a*self.w*sin(self.w*(self.timeNext)+self.phi)
			
		elif (self.m=='QSS3'):
			L[1]=-self.a*self.w*sin(self.w*(self.timeNext)+self.phi)
			L[2]=-self.a*pow(self.w,2)*cos(self.w*(self.timeNext)+self.phi)/2

		# envoie du message le port de sortie
		for i in range(len(self.OPorts)):
			self.poke(self.OPorts[i], Message(L,self.timeNext))

	###
	def __str__(self):return "CosGen"
