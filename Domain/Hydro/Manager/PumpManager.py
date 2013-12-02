# -*- coding: utf-8 -*-

"""
Name: PumpManager.py

Author(s): L. Capocchi (capocchi@univ-corse.fr), J.F. Santucci (santucci@univ-corse.fr)
Version: 0.1
Last modified: 05/31/2011
GENERAL NOTES AND REMARKS: Ho+=asinao and Hf+=orgone because we applied a strategy that predict the asiano and orgone water quantities
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior 

WEEKS = 53

class PumpManager(DomainBehavior):
	"""
	"""

	def __init__(self):
		"""
		"""
		DomainBehavior.__init__(self)
		
		### liste des messages permettant de genere une sortie uniquement lorsque tout les msg sont arrives.
		self.msgList = [None]*20
		
		self.state = {'status':'IDLE','sigma':INFINITY}

	###
  	def intTransition(self):
		# Changement d'etat
		self.changeState()

	###
	def extTransition(self):
		
		self.msgList = self.msgList[0:len(self.IPorts)]
		
		### scan port
		for i,port in enumerate(self.IPorts):
			msg = self.peek(port)
			if self.msgList[i] == None and msg != None:
				self.msgList[i] = msg
		
		### generation de la sortie si tout les msg sont arrives (en regime permanent c1, c2, Ho, Hf, oso)
		if None not in self.msgList:
			# changement d'etat
			self.changeState('ACTIF',0)
		
	###
  	def outputFnc(self):
		assert(None not in self.msgList)

		### 8 parce que le message vient d'un enumerate
		msg = self.msgList[8]
		
		### data
		### c1: conso PV
		### c2: conso B
		### Ho: hauteur ospedale
		### Hf: hauteur figari
		### d1: date Ete/Hiver
		### d2: date Hivet/Ete
		### s0: seuil bas figari
		### s2: seuil bas ospedale
		### oso: prise oso
		### s : semaine consideree
		
		c1, c2, Ho, Hf, d1, d2, s0, s2, oso = map(lambda m: float(m.value[0]), self.msgList)
		s = int(msg.time)
		
		val = 0.0
		
		### en ete
		### on pompe que si on est en été que l'ospedale en dessous de son seuil min (on a tout consome) que figarie au dessus de son seuil min
		self.debugger("%f %f %f"%(d1,s,d2))
		
		if s < d1 and s > d2:
			if (Ho < s2) and (Hf > s0):
				val = c1+c2
				self.debugger("ete pompage")
			else:
				self.debugger("ete pas de pompage")
		### hiver
		### pas de pompage
		else:
			self.debugger("hiver pas de pompage")	
		
		msg.time = self.timeNext
		msg.value = [val, s, 0.0]
		
		# envoie du message sur le port de sortie
		self.poke(self.OPorts[0], msg)

		### remove c1, c2, Ho, Hf, oso for next week
		for i in (0, 1, 2, 3, 8):
			self.msgList[i] = None
			
		### remove d1 and d2
		if s == 52:
			self.msgList[4] = None
			self.msgList[5] = None
	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState(self, status='IDLE', sigma=INFINITY):
		self.state['status'] = status
		self.state['sigma'] = sigma

	def __str__(self):return "PumpManager"