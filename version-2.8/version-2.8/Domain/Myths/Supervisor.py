# -*- coding: utf-8 -*-

from Domain.Myths.MythDomainBehavior import MythDomainBehavior
#from Domain.Myths.Object import Myth
from Domain.Myths import MythemADEVS

class Supervisor(MythDomainBehavior) :
	"""
	"""
	
	###
	def __init__(self, code_list=[]):
		"""Constructor.
		"""
		
		MythDomainBehavior.__init__(self)
		
		#local copy
		self.code_list = code_list
		
		self.state = {'status':'IDLE', 'sigma':INFINITY}

		self.msg = None
		self.p = None

	###
  	def intTransition(self):
		# Changement d'etat
		self.state['sigma'] = INFINITY

	###
	def extTransition(self):

		mv = self.OPorts[0].outLine[0].host
		

		# multi-port values version
		for p in range(len(self.IPorts)):
			msg = self.peek(self.IPorts[p])
			if msg != None:
				self.msg = msg
				self.p = p

		### supprimer tout les modeles du mythvariante
		mv.componentSet = []
		
		### creation des mythemADEVS
		for mythem in self.msg.value[0].mythemsList:
			m = MythemADEVS.MythemADEVS(mythem[0],mythem[1])
				
			m.timeNext = m.timeLast = m.myTimeAdvance = 0.
			m.addInPort()
			m.addOutPort()
			mv.addSubModel(m)
			mv.connectPorts(mv.IPorts[0],m.IPorts[0])
			mv.connectPorts(m.OPorts[0],mv.OPorts[0])
			
		# changement d'etat
		self.state['status']='ACTIF'
		self.state['sigma'] = 0
		
	###
  	def outputFnc(self):
		assert(self.msg!=None)
		
		self.msg.value = self.code_list
		self.msg.time=self.timeNext
		
		# envoie du message sur les ports de sortie
		self.poke(self.OPorts[self.p], self.msg)

	###
  	def timeAdvance(self): return self.state['sigma']
		
	###
	def __str__(self): return "Supervisor"
