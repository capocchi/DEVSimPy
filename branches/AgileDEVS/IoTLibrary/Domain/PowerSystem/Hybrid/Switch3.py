# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Switch3.py --- Switch à 3 entrées
#                     --------------------------------
#                        	 Copyright (c) 2007
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 21/03/07
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

try:
	from DomainInterface.PSDomainBehavior import DomainBehavior, Master
	from DomainInterface.Object import Message
except ImportError:
	import sys,os
	for spath in [os.pardir+os.sep]:
		if not spath in sys.path: sys.path.append(spath)
	from DomainInterface.DomainBehavior import DomainBehavior, Master
	from DomainInterface.Object import Message

#    ======================================================================    #

INFINITY=4e10

class Switch3(DomainBehavior):
	'''	Model atomique de la fonction "marche"
	'''

	###
	def __init__(self, time=0):
		'''	Constructeur
		'''
		DomainBehavior.__init__(self)

		# Declaration des variables d'état (actif tout de suite)
		self.state = {	'status':	'ACTIVE',
						'sigma':	Master.sdb.INFINITY}
		# Local copy
		self._time=time			# time to switch
		
		# chosing port number 
		self.outPort = 1
		
		# Declaration du port d'entrée et de sortie
		for i in range(3):
			self.addOutPort()
		self.IN = self.addInPort()
		
	###
  	def intTransition(self):

		self.changeState()
		return self.state
	
	###
	def extTransition(self):
		
		self.msg=self.peek(self.IN)
		
		if self.msg.time >= self._time:
			self.outPort=0
		else:
			print "TITI", self.msg.value
			self.outPort=1
			
		self.changeState('ACTIF',0)
		return self.state
		
	###
  	def outputFnc(self):
		
		# envoie du message le port de sortie
		
		self.poke(self.OPorts[self.outPort], self.msg)

	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state = { 'status':status, 'sigma':sigma}

	###
	def __str__(self):return "Switch3"
