# -*- coding: utf-8 -*-

"""
Name : QuickScope.py
Brief description : Atomic Model ploting the data results in windows.
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version : 1.0
Last modified : 23/06/09
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from DomainInterface.DomainBehavior import DomainBehavior

# ===================================================================   #
class QuickScope(DomainBehavior):
	"""	QuickScope(fusion, eventAxis)
		
		Atomic model ploting the data with some fonctionality.
	"""

	###
	def __init__(self, fusion = True, eventAxis = False):
		""" Constructor.
		
			@param fusion : Flag to plot all signals on one graphic
			@param eventAxis : Flag to plot depending event axis
		"""
		DomainBehavior.__init__(self)
		
		# fusioning curve
		self.fusion = fusion
		# replace time axis with step axis
		self.eventAxis = eventAxis
		
		# results tab (results attribut must be defined in order to plot the data)
		self.results = {} #OrderedDict()
		
		self.t = INFINITY

		self.initPhase('INACTIF',INFINITY)

	###
	def extTransition(self, *args):
		"""
		"""
		
		for np in range(len(self.IPorts)):
			msg = self.peek(self.IPorts[np], *args)
		
			if msg:
				### if step axis is chosen
				if self.eventAxis:
					self.eventAxis += 1
					self.t = self.eventAxis
				else:
					### adapted with PyPDEVS
					self.t = self.getMsgTime(msg)
					
				# ecriture dans la liste pour afficher le QuickScope et le SpreadSheet
				# si il y a eu un changement du nombre de ports alors on creer la nouvelle entre dans results (on ne regenere pas d'instance)				### adapted with PyPDEVS
				
				val = self.getMsgValue(msg) 
				if isinstance(msg.value, (list,tuple)):
					val = val[0]

				if np in self.results:
					self.results[np].append((self.t, val))
				else:
					self.results[np]=[(self.t, val)]

		self.holdIn('ACTIF',0.0)

		return self.getState()

	###
	def intTransition(self):
		self.passivate()
		return self.getState()
			
	###
	def timeAdvance(self):return self.getSigma()
	
	###
	def __str__(self):return "QuickScope"
