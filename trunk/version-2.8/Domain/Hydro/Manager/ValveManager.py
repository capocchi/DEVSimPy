# -*- coding: utf-8 -*-

"""
Name: ValveManager.py

Author(s): L.Capocchi (capocchi@univ-corse.fr), J.F. Santucci (santucci@univ-corse.fr)
Version: 0.1
Last modified: 03/09/2011 
GENERAL NOTES AND REMARKS: 	model wait c1, c2, Ho, Hf, oso, asinao, orgone messages in order to compute output and send it.
							Ho+=asinao and Hf+=orgone because we applied a strategy that predict the asiano and orgone water quantities
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior 

WEEKS = 53

class ValveManager(DomainBehavior):
	"""
	"""

	def __init__(self, pourcentage=100.0):
		"""
			@pourcentage : pourcent of leak form asinao
		"""
		DomainBehavior.__init__(self)
		
		### msg list storing all input in order to drive the waiting mode.
		self.msgList = [None]*20

		### pourcentage de lachure à partir de l'asinao
		self.pourcentage = pourcentage
		
		### state dict with status and sigma values
		self.state = {'status':'WAITING','sigma':INFINITY}

	###
  	def intTransition(self):
		# state change
		self.changeState()

	###
	def extTransition(self):
		
		### msgList scale
		self.msgList = self.msgList[0:len(self.IPorts)]
		
		### scan port
		for i,port in enumerate(self.IPorts):
			msg = self.peek(port)
		
			if self.msgList[i] == None and msg != None:
				self.msgList[i] = msg
		
		### sending message when all input signals are received (c1, c2, Ho, Hf, oso, asinao, orgone)
		if None not in self.msgList:
			# state change
			self.changeState('ACTIF',0)
		
	###
  	def outputFnc(self):		
		assert(None not in self.msgList)

		### 10 parce que le message vient d'un enumerate
		msg = self.msgList[10]
		
		### c1: conso PV
		### c2: conso B
		### Ho , Hf: Hauteur ospedale et figari
		### d1: date Hiver/Ete
		### d2: date Ete/Hiver
		### s1: seuil haut figari
		### s2 : seuil bas ospedale
		### s3 : seuil haut ospedale
		### oso
		### asinao
		### orgone
		### turbine : quantite turbinee avant l'ospedale
		
		### warning with the port order
		c1, c2, Ho, Hf, d1, d2, s1, s2, s3, oso, asinao, orgone, turbine = map(lambda m: float(m.value[0]), self.msgList)
		s = int(msg.value[1])

		### prevision des niveau avec les arrivees naturelles d'eau
		Ho+=asinao
		Hf+=orgone
		
		self.debugger("%f"%s)
		
		val = 0.0
		### en hiver
		### lachure de l'ospedale pour consommation et remplissage eventuel de figari.
		if s < d1 or s > d2:
			if Ho >= s2:
				val = c1 + c2
			else:
				self.debugger("warning : bad strategy, dam ospedal is empty")
		
			### TODO: formule avec m3/s
			asinao_p = float(self.pourcentage*asinao)/100.0
			
			### figari pas plein et que le reste est positif et que ce que l'on rajoute ne fais pas déborder figari
			if (Hf < s1) and (asinao - val > 0) and (Hf + asinao_p - val < s1):
				### la totalité de l'asiano est laché dans la conso plus le remplissage de figari si ospedale est proche d'etre plein
				if Ho >= s3:
					### si turbinage en amont il faut le retrancher
					val += asinao_p - turbine
					self.debugger("consomation + remplissage de figari (turbine = %f)"%turbine)
				else:
					self.debugger("consomation")
			else:
				self.debugger("consomation sans remplissage de figari %f %f %d %d"%(Hf , s1,asinao - val > 0 ,Hf + orgone + asinao_p - val < s1))

		### ete
		elif Ho > s2:
			val = c1 + c2
			self.debugger("ete vanne")
		else:
			self.debugger("ete pas de vanne")
			
		msg.time = self.timeNext
		msg.value = [val, s, 0.0]
		
		# envoie du message sur le port de sortie
		self.poke(self.OPorts[0], msg)

		### remove c1, c2, Ho, Hf, oso, asinao, orgone, turbine for next week
		for i in (0, 1, 2, 3, 9, 10, 11, 12):
			self.msgList[i] = None
		
		### remove d1 and d2
		if s == 52:
			self.msgList[4] = None
			self.msgList[5] = None

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState(self, status='WAITING', sigma=INFINITY):
		self.state['status'] = status
		self.state['sigma'] = sigma

	def __str__(self):return "ValveManager"