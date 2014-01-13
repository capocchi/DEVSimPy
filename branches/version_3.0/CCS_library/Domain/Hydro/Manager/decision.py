# -*- coding: utf-8 -*-

"""
Name: decision.py

Author(s): L.Capocchi (capocchi@univ-corse.fr), J.F. Santucci (santucci@univ-corse.fr)
Version: 0.1
Last modified: 06/06/2011 
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior 

import os
import copy

class Decision(DomainBehavior):
	"""
	"""

	def __init__(self):
		""" Constructor
		"""
		DomainBehavior.__init__(self)
		
		### state dict with status and sigma values
		self.state = {'status':'IDLE','sigma':INFINITY}
		
		self.c1_real = {}
		self.c2_real = {}
		self.c1 = {}
		self.c2 = {}
		self.turbine = {}
		self.pumpe = {}
		self.ho = {}
		self.hf = {}
		
		self.msgList = [None]*50
		
	###
  	def intTransition(self):
		# state change
		self.changeState()

	###
	def extTransition(self):
		
		### msgList scale
		self.msgList = self.msgList[0:len(self.IPorts)]

		for port,msg in self.peek_all():
			i = port.myID
			if self.msgList[i] == None:
				self.msgList[i] = msg
				
		### scan port
		#for i,port in enumerate(self.IPorts):
			#msg = self.peek(port)
		
			#if self.msgList[i] == None and msg != None:
				#self.msgList[i] = msg

		### sending message when all input signals are received
		if None not in self.msgList:
			## state change
			self.changeState('ACTIF',0)
		
	###
  	def outputFnc(self):		
		assert(None not in self.msgList)

		msg = self.msgList[-1]
		
		### TODO faire le modèle de decision
		d1, d2, c1, c2, c1_real, c2_real, ho, hf, turbine, pumpe = map(lambda m: float(m.value[0]), self.msgList)
		
		s = msg.value[1]
		
		if not self.c1.has_key((d1,d2)):
			self.c1[(d1,d2)]=[c1]
			self.c2[(d1,d2)]=[c2]
		else:
			self.c1[(d1,d2)].append(c1)
			self.c2[(d1,d2)].append(c2)
				
			#if c1_real != None or c2_real != None:
		if not self.c1_real.has_key((d1,d2)):
			self.c1_real[(d1,d2)]=[c1_real]
			self.c2_real[(d1,d2)]=[c2_real]
		else:
			self.c1_real[(d1,d2)].append(c1_real)
			self.c2_real[(d1,d2)].append(c2_real)
				
			#if self.ho == {} and ho != None or self.hf != {} and hf != None:
		if not self.ho.has_key((d1,d2)):
			self.ho[(d1,d2)]=[ho]
			self.hf[(d1,d2)]=[hf]
		else:
			self.ho[(d1,d2)].append(ho)
			self.hf[(d1,d2)].append(hf)
			
			#if self.turbine == {} and turbine != None or self.pumpe != {} and pumpe != None:
		if not self.turbine.has_key((d1,d2)):
			self.turbine[(d1,d2)]=[turbine]
			self.pumpe[(d1,d2)]=[pumpe]
		else:
			self.turbine[(d1,d2)].append(turbine)
			self.pumpe[(d1,d2)].append(pumpe)
		
		for i in (2,3,4,5,6,7,8,9):
			self.msgList[i] = None
		
		if s == 52:
			self.msgList[0] = None
			self.msgList[1] = None
	
	def finish(self, msg):
			
		### -------------------------- critère de consomation
			
		### determine les mauvaises années dans false_list
		false_list = []
		for k in self.c1_real:
			for i,val in enumerate(self.c1[k]):
				if val > self.c1_real[k][i]:
					false_list.append(k)
					break
		
		### suppression des mauvaises années
		for k1 in false_list:
			del self.c1_real[k1]
		
		### determine les mauvaises années dans false_list
		false_list = []
		for k in self.c2_real:
			for i,val in enumerate(self.c2[k]):
				if val > self.c2_real[k][i]:
					false_list.append(k)
					break
		
		### suppression des mauvaises années
		for k2 in false_list:
			del self.c2_real[k2]

		### les clees doivent etre dans c1_real et c2_real
		cmp_list = [k for k in self.c1_real if k in self.c2_real]
	
		for k1 in copy.copy(self.c1_real):
			if k1 not in cmp_list:
				del self.c1_real[k1]
		
		for k2 in copy.copy(self.c2_real):
			if k2 not in cmp_list:
				del self.c2_real[k2]
		
		###----------------- critère de turbinage
		
		### dico des différences entre pompage et turbinage
		### C1_real ou c2 real puisqu'il ont les memes cles
		D = {}
		
		for k in filter(lambda a: a in self.c1_real, self.turbine.keys()):
			for i,val in enumerate(self.turbine[k]):
				D[k] = val - self.pumpe[k][i]
		
		max_trubine = max(D.values())
		
		L = filter(lambda a: D[a]==max_trubine, D)
		
		print "sans critere de hauteur de bassin: ", L, max_trubine, D
		
		### ------------------- critère de hauteur de bassin
		
		for key in copy.copy(self.ho):
			if key not in L:
				del self.ho[key]
		
		#for key in self.ho:
			#print key, self.ho[key]
		
		max_ospedale = max([val[-1] for val in self.ho.values()])
		
		ospedale_list = filter(lambda a: self.ho[a][-1]==max_ospedale, self.ho)
		
		result = filter(lambda a: a in ospedale_list, L)
		
		print "avec critere de hauteur de bassin:", max_ospedale, result
				
	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState(self, status='IDLE', sigma=INFINITY):
		self.state['status'] = status
		self.state['sigma'] = sigma

	def __str__(self):return "Decision"