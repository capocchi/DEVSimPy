# -*- coding: utf-8 -*-

"""
@author: Samuel TOMA
@organization: University of Corsica
@contact: toma@univ-corse.fr
@since: 2011.11.17
@version: 1.0
@depedns : sudo apt-get install python-hcluster
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior

### Model class ----------------------------------------------------------------
class Dendrogram(DomainBehavior):
  
	def __init__(self):
		DomainBehavior.__init__(self)
		self.state = {'status': 'Idle', 'sigma':INFINITY}
		self.vectors = []
		self.fn = ""
	
	def extTransition(self):
		msg = self.peek(self.IPorts[0])
		if msg != None:
			self.vectors.append(msg.value[0])
		self.state = {'status': 'Active', 'sigma': INFINITY}

	def intTransition(self):
	  self.state = {'status': 'Idle', 'sigma': INFINITY}
		
	def timeAdvance(self):
		return self.state['sigma']
