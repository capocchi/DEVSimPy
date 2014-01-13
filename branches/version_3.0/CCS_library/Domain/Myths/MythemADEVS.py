 # -*- coding: utf-8 -*-

from Domain.Myths.MythDomainBehavior import MythDomainBehavior
from Domain.Myths.Object import Myth

import os, sys
import __builtin__

class MythemADEVS(MythDomainBehavior) :
	"""
	"""

	###
	def __init__(self, a="", x=""):
		"""Constructor.
		"""

		MythDomainBehavior.__init__(self)

		#local copy
		self.a=a.strip()
		self.x=x.strip()

		self.state = {'status':'IDLE', 'sigma':INFINITY}

		self.msg = None
		self.p = None

	###
	def intTransition(self):
			# Changement d'etat
			self.state['sigma'] = INFINITY

	###
	def extTransition(self):
			message = []
			# multi-port values version
			for p in range(len(self.IPorts)):
					msg = self.peek(self.IPorts[p])
					if msg != None:
							self.msg = msg
							self.p = p
			### TODO: MythVariant est le nom du modèle couplé contenant les MythemADEVS. Si simulation avec plusieurs .dsp ce sera le dernier context rentré qui sera appliqué à tous les .dsp
			#print "message"
			#print msg
			context = __builtin__.__dict__['MythVariant'] ### Attention, marche plus si le label des MythVaraint est different de 'MythVaraint'
			#print "CONTEXT///////////////////"
			#print context
			#print "end context"
			for code in self.msg.value:
				for k in context.keys():
					a= k.split(',')[0].strip()
					b= k.split(',')[1].strip()
					c= k.split(',')[2].strip()

					if code == a:
						if self.a == b and self.x == c:
							d,e = context[k].split(',')
							#print "d et e"
							#print d
							#print e
							#print code
							#self.msg.value= [code,d.strip().replace("'",""),e.strip().replace("'","")]
							message = message + [(code,d.strip().replace("'",""),e.strip().replace("'",""))]
							#print message

			# changement d'etat
			#print "message"
			#print message
			self.msg.value = message
			self.state['status']='ACTIF'
			self.state['sigma'] = 0


	###
	def outputFnc(self):
		assert(self.msg!=None)

		self.msg.time=self.timeNext

		if self.msg.value != []:
			self.poke(self.OPorts[self.p], self.msg)

	###
	def timeAdvance(self): return self.state['sigma']

	def __str__(self): return "MythemADEVS"
