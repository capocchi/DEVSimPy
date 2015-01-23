# -*- coding: utf-8 -*-

"""
Name: Folder.py
Brief description: Atomic Model which define a SIG Layer.
Author(s): L. Capocchi <capocchi@univ-corse.fr>, J.F. Santucci <santucci@univ-corse>, B. Poggi <poggi@univ-corse.fr>
Version: 0.1
Last modified: 10/07/2012
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS:
	- param: name, points, color, alpha
"""

### just for python 2.5
from __future__ import with_statement
from DomainInterface.DomainBehavior import DomainBehavior 
from Domain.Basic.Object import Message

import os

# ===================================================================   #
class Folder(DomainBehavior):
	""" Atomic Model which define a SIG polygon.
	"""

	###
	def __init__(self, name = "FolderName"):
		""" Constructor.
			
			@param name : polygon name
		"""
		
		DomainBehavior.__init__(self)

		### State variable
		self.state = {'status': 'INACTIF', 'sigma': INFINITY}

		### local copy
		self.name = name
		self.childs = []
		
	def extTransition(self):
		"""
		"""
		self.childs = []
		for port, msg in self.peek_all():
			elem = msg.value[0]
			self.childs.append(elem)

		self.state = {'status': 'INACTIF', 'sigma': 0}
		
	###
	def outputFnc(self):
		"""
		"""
		# send output message
		self.poke(self.OPorts[0], Message([self], self.timeNext))
	
	###
	def intTransition(self):
		self.state["status"] = 'IDLE'
		self.state["sigma"] = INFINITY
					
	###
	def timeAdvance(self):return self.state['sigma']
	
	###
	def __str__(self):return "Folder"
