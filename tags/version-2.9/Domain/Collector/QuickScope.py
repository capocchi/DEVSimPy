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
		
		#  State variable
		self.state = {'status': 'INACTIF', 'sigma': INFINITY}
		
		# fusioning curve
		self.fusion = fusion
		# replace time axis with step axis
		self.eventAxis = eventAxis
		
		# results tab (results attribut must be defined in order to plot the data)
		self.results = {} #OrderedDict()
		
		self.t = INFINITY

	###
	def extTransition(self, *args):
		"""
		"""
		
		for np in xrange(len(self.IPorts)):
			if hasattr(self, 'peek'):
				msg = self.peek(self.IPorts[np])
			else:
				inputs = args[0]
				msg = inputs.get(self.IPorts[np])

			if msg is not None:
				# if step axis is chosen
				if self.eventAxis:
					self.eventAxis += 1
					self.t = self.eventAxis
				else:
					self.t = msg.time
					if not hasattr(self, 'peek'):
						self.t = self.t[0]

				#ecriture dans la liste pour affichier le QuickScope et le SpreadSheet
				# si il y a eu un changement du nombre de ports alors on creer la nouvelle entre dans results (on ne regenere pas d'instance)
				if np in self.results:
					self.results[np].append((self.t, msg.value[0]))
				else:
					self.results[np]=[(self.t, msg.value[0])]
					
				del msg
				
		self.state['sigma'] = 0
		return self.state

	###
	def intTransition(self):
		self.state["status"] = 'IDLE'
		self.state["sigma"] = INFINITY
		return self.state
			
	###
	def timeAdvance(self):return self.state['sigma']
	
	###
	def __str__(self):return "QuickScope"
