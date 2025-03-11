# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:          		To_Stdout.py
 Model description:     <description>
 Authors:       		capocchi_l
 Organization:  		<your organization>
 Current date & time:   2024-03-01 18:48:48.080953
 License:       		GPL v3.0
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

import sys

### Model class ----------------------------------------------------------------
class To_Stdout(DomainBehavior):
	''' DEVS Class for the model To_Stdout
	'''

	def __init__(self, at_end=False, tag="output"):
		''' Constructor.

			@param at_end: if true, print at the end of the sim
			@param tag: used to tag the print
		'''
		DomainBehavior.__init__(self)

		self.at_end = at_end
		self.tag = tag

		if at_end:
			self.buffer = []

		self.initPhase('IDLE',INFINITY)

	def extTransition(self, *args):
		''' DEVS external transition function.
		'''
		
		for p in self.IPorts:
			msg = self.peek(p, *args)
			if msg:
				v = self.getMsgValue(msg)
				
				if self.at_end:
					self.buffer.append(v)
				else:
					print(f"{self.tag}:{v}")

		self.passivate()
		return self.getState()

	def outputFnc(self):
		''' DEVS output function.
		'''
		return {}

	def intTransition(self):
		''' DEVS internal transition function.
		'''
		self.passivate()
		return self.getState()

	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.getSigma()

	def finish(self, msg):
		''' Additional function which is lunched just before the end of the simulation.
		'''
		if self.at_end:
			print(f"{self.tag}: {self.buffer}")
