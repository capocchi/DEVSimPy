# -*- coding: utf-8 -*-

"""
Name : Impfunction.py 
Brief descritpion : Implicit atomic model 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 21/03/09
GENERAL NOTES AND REMARKS:
#	- Implementation du modele avec comme hypothese qu'il ne peux recevoir que # des messages a des isntants diff�rents. Dans le cas ou il a deux messages au # meme temps (cas d'un dedoublement d'une branche d'un composant en entr�e), il # voie sur le second port un deepcopy du composant 1. Ceci est g�nre� lors des # couplage je pense ! 
Sinon il faut drait scanner tout les ports dans delta_ext # pour r�cup�rer l� liste des message non vide et les traiter (A faire car cela # rend plus rapide le traitrement)
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior

from math import *
from itertools import*

#    ======================================================================    #

class ImpFunction(DomainBehavior):
	'''	Model atomique de la fonction implicte
	'''

	###
	def __init__(self, tol=0.0001, y0=1.0, n=1):
		'''	Constructeur
		'''
		DomainBehavior.__init__(self)

		#  Declaration des variables d'état.
		self.state = {	'status': 'IDLE', 'sigma': INFINITY}
						
		self.Y = [0.0]*3
		
		#local copy
		self.n=n
		self.tol=tol
		self.y0=y0
		
		#self.mn	= 0
		self.u	= [0.0]*self.n 
		self.mu	= [0.0]*self.n 
		self.pu	= [00.]*self.n 
		
		#self.expr=str(pow(self.Y[0],3)+self.Y[0]+pow(self.u[0],2))
		
		self.nm=0.0

		#self.expr=compile(self.expr,"","eval")
		
		# message d'arriv� qui va �tre modifier pour etre renvoye
		self.msg = None
		self.p = 0

	###
	def extTransition(self):
		
		self.msg = None
		self.p=0
		while self.msg==None:
			self.msg=self.peek(self.IPorts[self.p])
			self.p+=1
		self.p-=1
		
		self.Y=self.getY(self.msg.value)
		
		self.state['sigma']=0

	###
  	def intTransition(self):
		self.state = self.changeState()
		
	###
  	def outputFnc(self):

		assert(self.msg != None)
		self.msg.value=self.Y
		self.msg.time=self.timeNext
		
		## envoie du message le port de sortie
		self.poke(self.OPorts[0], self.msg)

	###
  	def timeAdvance(self): return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		return { 'status':status, 'sigma':sigma}
		
	###
	def getY(self, Aux=[]): return [Aux[0]-2000,Aux[1],Aux[2]]
		
	###
	def __str__(self):return "ImpFunction"