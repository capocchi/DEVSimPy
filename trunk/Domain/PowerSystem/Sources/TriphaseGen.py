# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# TropahseGen.py --- Generateur de la fonction sinus
#                     --------------------------------
#                        	 Copyright (c) 2007
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 30/05/07
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

from math import pi, sqrt, sin, cos
from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

#    ======================================================================    #

class TriphaseGen(DomainBehavior):
	'''	Model atomique de la fonction triphase
	'''

	###
	def __init__(self, a=[1,1,1], f=50, phi=[0,0,0], k=20, m=["QSS2","QSS2","QSS2"]):
		'''	Constructeur
		'''
		DomainBehavior.__init__(self)

		assert(len(a)==len(phi)==len(m))

		# Declaration des variables d'�tat (actif tout de suite)
		self.state = { 'status': 'ACTIVE', 'sigma': 0}
		# Local copy
		self.a=a
		self.f=f
		self.phi=phi
		self.k=k							# nombre de points calcul�s
		self.m=m
		
		self.w= 2*3.14159*self.f								# pulsation
		self.dt=1/float(self.f)/float(self.k) 					# pas de calcul en temps
		
	###
  	def intTransition(self):

		# Changement d'�tat (inactif pendant dt)
		self.changeState(sigma=self.dt)
		return self.state

	###
  	def outputFnc(self):

		# Liste envoy�e dans le message de sortie
		for i in range(len(self.a)):
			L = [self.a[i]*sin(self.w*self.timeNext+self.phi[i]),0.0,0.0]
		
			if(self.m=="QSS2"):
				L[1]=self.a[i]*self.w*cos(self.w*self.timeNext+self.phi[i])
			elif(self.m=="QSS3"):
				L[1]=self.a[i]*self.w*cos(self.w*self.timeNext+self.phi[i])
				L[2]=-self.a[i]*pow(self.w,2)*sin(self.w*self.timeNext+self.phi[i])/2
			
			# envoie du message le port de sortie
			self.poke(self.OPorts[i], Message(L,self.timeNext))

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status']=status
		self.state['sigma']=sigma

	###
	def __str__(self):return "TriphaseGen"
