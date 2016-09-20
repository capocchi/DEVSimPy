# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:          ImgGen.py
 Model:         Image generator
 Authors:       L. Capocchi
 Organization:  UMR CNRS 6134
 Date:          06.15.2016
 License:       GPL v3.0
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

import os

### Model class ----------------------------------------------------------------
class ImgGen(DomainBehavior):
	''' DEVS Class for ImgGen model
	'''

	def __init__(self, filename="image.jpg"):
		''' Constructor.
		'''
		DomainBehavior.__init__(self)

		### local copy
		self.fn = filename

		self.state = {	'status': 'IDLE', 'sigma':0}

	def extTransition(self):
		''' DEVS external transition function.
		'''
		pass

	def outputFnc(self):
		''' DEVS output function.
		'''
		if os.path.isfile(self.fn):
			self.poke(self.OPorts[0], Message(self.fn, self.timeNext))

	def intTransition(self):
		''' DEVS internal transition function.
		'''
		self.state['sigma'] = INFINITY

	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.state['sigma']

	def finish(self, msg):
		''' Additional function which is lunched just before the end of the simulation.
		'''
		pass
