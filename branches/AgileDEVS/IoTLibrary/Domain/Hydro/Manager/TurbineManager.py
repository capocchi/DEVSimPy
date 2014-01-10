# -*- coding: utf-8 -*-

"""
Name: TurbineManager.py

Author(s):L. Capocchi (capocchi@univ-corse.fr), J.F. Santucci (santucci@univ-corse.fr)
Version: 0.1
Last modified: 05/31/2011
GENERAL NOTES AND REMARKS: 
	strategy 2: avantage le remplissage de figari au turbinage en hiver
	strategy 1: avantage le turbinage au remplissage de figari en hiver
	strategy 0: éviter les debordements de l'ospedale en turbinant (attention s3 est consédiéré coomme la capacite totale de l'ospedale)
	Ho+=asinao and Hf+=orgone because we applied a strategy that predict the asiano and orgone water quantities

GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior 

WEEKS = 53

class TurbineManager(DomainBehavior):
	"""
	"""

	def __init__(self, strategy=0):
		"""
			@strategy : strategy for efficient managment of the turbine process
		"""
		DomainBehavior.__init__(self)
		
		### liste des messages permettant de genere une sortie uniquement lorsque tout les msg sont arrives.
		self.msgList = [None]*20
		
		self.strategy = strategy
		
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
		
		### generation de la sortie si tout les msg sont arrives (Ho, Hf, asinao, orgone en regime permanent)
		if None not in self.msgList:
			# changement d'etat
			self.changeState('ACTIF',0)
		
	###
  	def outputFnc(self):		
		assert(None not in self.msgList)

		### 6 parce que le message vient d'un enumerate
		msg = self.msgList[6]
		
		### Ho, Hf : Hauteur ospedale et figari
		### d1: date Hiver/Ete
		### d2: date Ete/Hiver
		### s1 : seuil haut figari
		### s3 : seuil haut ospedale
		### Asinao et orgone
		
		### attention ordre des ports
		Ho, Hf, d1, d2, s1, s3, asinao, orgone = map(lambda m: float(m.value[0]), self.msgList)
		s = int(msg.value[1])
		
		### prevision des niveau avec les arrivees naturelles d'eau
		Ho+=asinao
		Hf+=orgone
		
		#self.debugger("%f %f %f %f %f %f %f %f"%(Ho, Hf, d1, d2, s1, s3, asinao, orgone))
		
		### pas de turbinage
		val = 0.0
		self.debugger("%f %f %f"%(d1,s,d2))
		
		### en ete : pas de turbinage
		if s < d2 and s > d1:
			self.debugger("En été pas de turbinage")
		else:
			### en hiver : turbinage dependant de la strategie et de la hauteur de l'ospedale
			if Ho > s3:
				###strategy 0: éviter les debordements de l'ospedale en turbinant (attention s3 est consédiéré coomme la capacite totale de l'ospedale)
				if self.strategy == 0:
					val =  Ho - s3
					self.debugger("strategy 0 : En hiver avec ospedal pas plein mais asinao fait deborder - > on complete ospedale et turbinage")		
				###strategy 2: avantage le remplissage de figari au turbinage en hiver
				elif self.strategy == 2:
					if Hf >= s1:
						val = asinao
						self.debugger("strategy 2 : En hiver avec figari plein - > turbinage")	
					else:
						self.debugger("strategy 2 : En hiver avec figari pas plein - > pas de turbinage")
				###strategy 1: avantage le turbinage au remplissage de figari en hiver
				elif self.strategy == 1:
					val = asinao
					self.debugger("strategy 1 : En hiver pas de remplissage de figari- > turbinage")	
				else:
					self.debugger("strategie inconnue !!!")	
			else:
				self.debugger("En hiver avec ospedale pas plein -> pas de turbinage")
			
		msg.time = self.timeNext
		msg.value = [val, s, 0.0]
		
		# envoie du message sur le port de sortie
		self.poke(self.OPorts[0], msg)

		### remove Ho, Hf, asinao, orgone for next week
		for i in (0,1,6,7):
			self.msgList[i] = None
			
		### remove d1 and d2
		if s == 52:
			self.msgList[2] = None
			self.msgList[3] = None
	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status']=status
		self.state['sigma']=sigma

	def __str__(self):return "TurbineManager"