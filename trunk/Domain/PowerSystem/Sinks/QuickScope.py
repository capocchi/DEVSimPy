# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# QhickScope.py --- Atomic Model ploting the data results in windows.
#                     --------------------------------
#                        	 Copyright (c) 2009
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified: 23/06/09
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

from DomainInterface.DomainBehavior import DomainBehavior
	
# ===================================================================   #
class QuickScope(DomainBehavior):
	"""	QuickScope(fusion, eventAxis)
			
		Atomic model ploting the data with some fonctionality.
	"""

	###
	def __init__(self, fusion=True, eventAxis=False):
		DomainBehavior.__init__(self)
		
		#  State variable
		self.state = {'status': 'INACTIF', 'sigma': INFINITY}
		
		# fusioning curve
		self.fusion = fusion
		# replace time axis with step axis
		self.eventAxis = eventAxis

		#results tab
		self.results = {}

	###
	def extTransition(self):
		activePort = self.myInput.keys()[0]
		np = activePort.myID
		msg= self.peek(activePort)

		# if step axis is choseen
		if self.eventAxis:
			self.eventAxis += 1
			t = self.eventAxis
		else:
			t = msg.time

		v = msg.value[0]

		#ecriture dans la liste pour affichier le QuickScope et le SpreadSheet
		# si il y a eu un changement du nombre de ports alors on creer la nouvelle entre dans results (on ne regenere pas d'instance)
		try:
			self.results[np].append((t,v))
		except KeyError:
			self.results.update({np:[(t,v)]})

		self.state['sigma'] = 0
	
	###
  	def intTransition(self):
		self.state["status"] = 'IDLE'
		self.state["sigma"] = INFINITY
			
	###
	def timeAdvance(self):return self.state['sigma']
	
	###
	def __str__(self):return "QuickScope"
