# -*- coding: utf-8 -*-

"""
Name: Enumerate.py

Author(s): L.Capocchi (capocchi@univ-corse.fr), J.F. Santucci (santucci@univ-corse.fr)
Version: 0.1
Last modified: 06/06/2011 
GENERAL NOTES AND REMARKS: sans allert, + trubinage et - pompage
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior 
from Object import Message

import os

WEEKS = 53

class Enumerate(DomainBehavior):
	"""
	"""

	def __init__(self, 	fileName_asinao=os.path.join(os.getcwd(), "asinao.csv"), 
						fileName_oso=os.path.join(os.getcwd(), "oso.csv"), 
						fileName_orgone=os.path.join(os.getcwd(), "orgone.csv"), 
						fileName_conso_pv=os.path.join(os.getcwd(), "c1.csv"),
						fileName_conso_se=os.path.join(os.getcwd(), "c2.csv"), 
						s0 = 0.0, s1 = 5000000.0, s2 = 0.0, s3 = 3000000.0, d1 = 25, d2 = 40, comma = " "):
		""" Constructor
		"""
		DomainBehavior.__init__(self)
		
		### local copy
		self.asinao = fileName_asinao
		self.oso = fileName_oso
		self.orgone = fileName_orgone
		self.d1 = d1
		self.d2 = d2
		self.s0 = s0
		self.s1 = s1
		self.s2 = s2
		self.s3 = s3
		self.c1 = fileName_conso_pv
		self.c2 = fileName_conso_se
		
		self.V = {}
		
		self.comma = comma
		
		if os.path.exists(self.asinao) and os.path.exists(self.oso) and os.path.exists(self.orgone) and os.path.exists(self.c1) and os.path.exists(self.c2):
			for fn in [self.asinao, self.oso, self.orgone, self.c1, self.c2]:
				with open(fn,"rb") as f:
					for l in filter(lambda b: b != '' , map(lambda a: a.replace('\n', ''), f.readlines())):
						
						t = l.split(self.comma)[0]
						
						### ne commence pas par un vide (sinon forte chance de ligne vide)
						### TODO eviter les lignes vides
						if t[0] != '' and not self.V.has_key(float(t)):
							self.V[float(t)]=[]
						
						self.V[float(t)].append(l.split(self.comma)[1])
				
				### attention dico non ordonné
				tmp = self.V.keys()
				tmp.sort()
				sig = tmp[0] if tmp != [] else INFINITY
		else:
			sig = INFINITY

		self.posibility = [(a,b) for a in range(53) for b in range(53) if a!=b and a<b and abs(b-a) >= 8]
		
		#print len(self.posibility)
		### state dict with status and sigma values
		self.state = {'status':'IDLE','sigma':sig}
	###
  	def intTransition(self):
		# state change
		if len(self.posibility) >0:
			sig = 1
		else:
			sig = INFINITY
			
		self.changeState(sigma=sig)

	###
  	def outputFnc(self):		
		#assert(None not in self.msgList)
		
		s = self.timeNext%WEEKS
		
		self.debugger("%f"%s)
		
		### first value of message is the rate and second one is the week
		self.poke(self.OPorts[0], Message([self.V[s][0], s, 0.0], self.timeNext))	### asiano
		self.poke(self.OPorts[1], Message([self.V[s][1], s, 0.0], self.timeNext))	### oso
		self.poke(self.OPorts[2], Message([self.V[s][2], s, 0.0], self.timeNext))	### orgone
		self.poke(self.OPorts[7], Message([self.V[s][3], s, 0.0], self.timeNext))	### C1
		self.poke(self.OPorts[8], Message([self.V[s][4], s, 0.0], self.timeNext))	### C2
		
		if s == 0:
			
			self.d1, self.d2 = self.posibility.pop()
			
			self.poke(self.OPorts[3], Message([self.s0, s, 0.0], self.timeNext))
			self.poke(self.OPorts[4], Message([self.s1, s, 0.0], self.timeNext))
			self.poke(self.OPorts[5], Message([self.s2, s, 0.0], self.timeNext))
			self.poke(self.OPorts[6], Message([self.s3, s, 0.0], self.timeNext))
			self.poke(self.OPorts[9], Message([self.d1, s, 0.0], self.timeNext))
			self.poke(self.OPorts[10], Message([self.d2, s, 0.0], self.timeNext))
		
	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState(self, status='WAITING', sigma=INFINITY):
		self.state['status'] = status
		self.state['sigma'] = sigma

	def __str__(self):return "Enumerate"