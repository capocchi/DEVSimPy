# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DeFuzzyAtomiciDEVS.py --- Librairie de mod�les iDEVS
# DeFuzzyAtomiciDEVS.py --- iDEVS's models
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

#    ======================================================================    #
class DeFuzzyAtomiciDEVS(FuzzyDomainBehavior):
	'''	Mod�le atomique iDEVS de defuzzification. 
		Application power system stator model
	'''

	###
	def __init__(self, coef=0.5, omega=10, inc=0.01):
		'''	Constructeur
		'''
		FuzzyDomainBehavior.__init__(self)
		
		#local copy
		self.coef = coef
		self.omega = omega
		self.inc = inc
		self.state={'coefDef':self.coef,		# coefficient de d�fuzzification
				'compteur':4,		# nombre d'it�ration pour revenir � un statut normal apr�s une anomalie
				'status':0,		# statut du mod�le en fonction de la derni�re tension.
					# 0 statut normal
					# 1 sous tension
					# 2 sur tension
				'crispResult':0.0,	# r�sultat de la d�fuzzification
				'averageDegree':0.0,	# moyenne des degr�s d'apparenance defuzzifi�s
				'sigma':INFINITY}

		self.deFuzzResult = []

	###
	def extTransition(self):
		''' Application de la fuzzification
		'''
		self.inc=0.01
		self.msg=self.peek(self.IPorts[0])
		
		Dict={0:[], 1:[], 2:[]}
		self.deFuzzResult=[]
		#self.state['coefDef']=0.5

		##tester le status
		#if self.state['status'] == 0:			# statut normal
			#prCent = random.randint(0,1000)
			##print prCent
			## 98% de chance de cas normal
			#if prCent > 20:		 		
				#self.state['coefDef'] = 0.5
			## 2% de chance de sur tension
			#else:
				#self.state['coefDef'] = 0.8
				#self.state['status'] = 2
				#self.inc = 0.1
				#for i in Dict:
				  #self.msg.value[i].update(a=self.msg.value[i].a,b=self.msg.value[i].b,psi=self.msg.value[i].psi,omega=self.omega)
			## 1% de chance de sous tension
			##else:
			##	self.state['coefDef'] = 0.2
			##	self.state['status'] = 1
		##elif self.state['status'] == 1:		# statut sous tension
		##	self.state['compteur']-=1			# 1i�re mesure
		##
		##	if self.state['compteur'] != 0:
		##		self.state['coefDef'] += 0.1		# avance dans les mesures
		##	else:							# on revient � la normal
		##		self.state['coefDef'] = 0.5
		##		self.state['compteur']=4
		##		self.state['status'] = 0
		#elif self.state['status'] == 2:				# statut sur tension
			#self.state['compteur']-=1			# 1i�re mesure

			#if self.state['compteur'] != 0:
				#self.state['coefDef'] -= 0.1		# recule dans les mesures
				#self.inc = 0.1
				#for i in Dict:
				  #self.msg.value[i].update(a=self.msg.value[i].a,b=self.msg.value[i].b,psi=self.msg.value[i].psi,omega=self.omega)
			#else:						# on revient � la normal
				#self.state['coefDef'] = 0.5
				#self.state['compteur']=4
				#self.state['status'] = 0
				
		for i in range(3):
			v=self.msg.value[i]
			D = v.defuzzDEVS(Dict[i],self.state['coefDef'],self.inc,'eem')
			Dict[i]=D['mDegree']
			self.deFuzzResult.append(D['result'])

		self.state['sigma'] = 0
	
	###
	def intTransition(self): self.state["sigma"] = INFINITY    

	###
  	def outputFnc(self):	
		# envoie du message le port de sortie
		
		self.msg.value=self.deFuzzResult
		
		self.msg.time=self.timeNext
		self.poke(self.OPorts[0],self.msg)

	###
	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self):return "DeFuzzyAtomiciDEVS"

