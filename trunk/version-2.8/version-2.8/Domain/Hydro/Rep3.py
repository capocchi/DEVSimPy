# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        Rep3.py

 Model:       Rep3 Model
 Author:      L. Capocchi (capocchi@univ-corse.fr), J.F. Santucci (santucci@univ-corse.fr), C. Nicolai (cnicolai@univ-corse.fr)

 Created:     2011-04-20
 Description : 	Le modèle génére ces deux sortie uniquement lorsqu'il a recu ces deux entrées pour une semaine donnée.
				Si il n'y a pas de turbinage, la sortie 0 est 0.0 sinon, c'est la quantité d'eau à turbiner pour la semaine.
 
				A revoir car le modèle par du principe que l'on ne peux pas à la fois turbiner et remplir l'ospedale (donc il faut attendre les deux messages pour agir)
-------------------------------------------------------------------------------
"""

from DomainInterface.DomainBehavior import DomainBehavior

#    ======================================================================    #
class Rep3(DomainBehavior):
	'''	Model atomique de la modelisation du Rep3
	'''
	###
	def __init__(self):
		""" Constructor
		"""
		
		DomainBehavior.__init__(self)
	
		### Qt : quantité de turbinage
		### Qa : quantité arrivant de l'asinao
		self.msgQt = None
		self.msgQa = None
		
		self.state = {	'status':'IDLE', 'sigma': INFINITY }

	def extTransition(self):

		#Recuperation de Qt et Qa
		msgQt, msgQa = map(self.peek, self.IPorts)

		if(msgQt != None):
			self.msgQt = msgQt

		if(msgQa != None):
			self.msgQa = msgQa

		# changement d etat que lorsque Qa et Qt sont different de None
		if (self.msgQa != None and self.msgQt != None):
			self.changeState('ACTIF',0)

	###
  	def outputFnc(self):
		
		assert(self.msgQa != None and self.msgQt != None)
		
		self.msgQt.time = self.timeNext
		self.msgQa.time = self.timeNext
		
		### la valeur de remplissage de l'ospedale doit prendre en compte le turbinage éventuel en amont géré par turbineManager
		self.msgQa.value[0] = float(self.msgQa.value[0]) - float(self.msgQt.value[0])
		
		if self.msgQa.value[0] < 0:
			self.debugger("Error negative value (turbine > asinao)")
		
		### sending messages
		self.poke(self.OPorts[0], self.msgQt)
		self.poke(self.OPorts[1], self.msgQa)

		### reinitialisation pour la prochaine semaine
		self.msgQt = None
		self.msgQa = None

	###
  	def intTransition(self):
		# Changement d'etat
		self.changeState()

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState(self, status='IDLE', sigma=INFINITY):
		self.state['status'] = status
		self.state['sigma'] = sigma

	def __str__(self):return "Rep3"