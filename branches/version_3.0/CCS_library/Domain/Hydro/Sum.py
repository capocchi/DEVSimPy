# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        Sum.py

 Model:       Summmator Model
 Author:      L. Capocchi (capocchi@univ-corse.fr), J.F. Santucci (santucci@univ-corse.fr)

 Created:     2011-06-01
-------------------------------------------------------------------------------
"""

from DomainInterface.DomainBehavior import DomainBehavior

#    ======================================================================    #
class Sum(DomainBehavior):
	"""	Atomic model of summator wich wait all of the inputs messages before sending its output message
	"""
	
	###
	def __init__(self):

            DomainBehavior.__init__(self)

            self.msgLst = [None]*50
            
            self.state = {'status':'IDLE', 'sigma': INFINITY}

	def extTransition(self):
		zefzef
		self.msgLst = self.msgLst[0:len(self.IPorts)]
		
		### scan tout les messages
		for i,port in enumerate(self.IPorts):
			msg = self.peek(port)
			if msg != None:
				self.msgLst[i] = msg
		
		#self.debugger("%s"%str(self.msgLst))
		# changement d etat que lorsque tous les messages sont arrives
		if None not in self.msgLst:
			self.changeState('ACTIF',0)

	###
	def outputFnc(self):
		
		assert(None not in self.msgLst)

		msg = self.msgLst[0]
		
		### setting output data
		msg.time = self.timeNext
		msg.value[0] = sum(map(lambda msg: float(msg.value[0]), self.msgLst))
			
		### send output msg
		self.poke(self.OPorts[0], msg)
		
		### clear all msg list
		self.msgLst = [None]*len(self.IPorts)

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

	def __str__(self):return "Sum"
