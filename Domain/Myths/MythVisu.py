# -*- coding: utf-8 -*-

from Domain.Myths.MythDomainBehavior import MythDomainBehavior
from Domain.Myths.Object import Myth
from Domain.Myths import PointMyth

class MythVisu(MythDomainBehavior) :
	"""
	"""
	
	###
	def __init__(self,fileName=""):
		"""Constructor.
		"""
		
		MythDomainBehavior.__init__(self)
		
		#local copy
		#self.code_list = code_list
		#modifs 14/11/2010
		#self.state = {'status':'IDLE', 'sigma':INFINITY}
		#fin modifs 14/11/2010

		self.msg = None
		#self.p = None
		#self.fileName = fileName

                #a inserer le 14/11/2010
		self.LAT = []		# Heros
		self.LONG = []
		self.state = {	'status':	'ACTIVE', 'sigma' : INFINITY}
                #fin insertion  le 14/11/2010

	def intTransition(self):
		# Changement d'etat
		
		self.state['sigma'] = INFINITY
		

	###
	def extTransition(self):
		
		mv = self.OPorts[0].outLine[0].host

			#f = open(self.fileName,'r')
			#CoordList = map(lambda line: line.split(' '), map(lambda l: l.strip('\n'), f.readlines()))
			#f.close()

			# multi-port values version

		msg = self.peek(self.IPorts[0])
		if msg != None:
			self.msg = msg
				

		### supprimer tout les modeles du mythvariante
		#mv.componentSet = []
		
		### creation des PointMyth de manière dynamique
		m = PointMyth.PointMyth(latitude = msg.value[1], longitude = msg.value[2], altitude = 0.0, description = msg.value[0][1], name = msg.value[0][0], range = 6000, tilt = 45, heading = 0, folder = msg.value[0][0])
		
		m.timeNext = m.timeLast = m.myTimeAdvance = 0.
		m.addInPort()
		m.addOutPort()
		mv.addSubModel(m)
		mv.connectPorts(mv.IPorts[0],m.IPorts[0])
		mv.connectPorts(m.OPorts[0],mv.OPorts[0])
	
		# changement d'etat
		self.state['status']='ACTIF'
		self.state['sigma'] = 0
		
		#self.state['sigma'] = self.msg
		
	###
	def outputFnc(self):
		assert(self.msg!=None)
		
		self.msg.value = 0
		self.msg.time= self.timeNext
		#self.msg.time= sigma + self.timeNext
		#self.debbuger("entre outtrans mythvisu")
		# envoie du message sur les ports de sortie
		
		#self.debbuger(self.msg)
		self.poke(self.OPorts[0], self.msg)
		
		#self.debbuger("sortie out trans mythvisu")

	###
	def timeAdvance(self): return self.state['sigma']
                
	def __str__(self): return "MythVisu"
