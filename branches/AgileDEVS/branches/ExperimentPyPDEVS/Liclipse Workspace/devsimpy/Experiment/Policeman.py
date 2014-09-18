# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      capocchi_l
#
# Created:     17/11/2013
# Copyright:   (c) capocchi_l 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from DomainInterface.DomainBehavior import DomainBehavior
#import sys
#import os
#sys.path.append(os.path.join(os.getcwd(),'trafficLight'))

from PolicemanMode import PolicemanMode

class Policeman(DomainBehavior):
	"""A policeman producing "toManual" and "toAutonomous" events:
	  "toManual" when going from "idle" to "working" mode
	  "toAutonomous" when going from "working" to "idle" mode
	"""

	###
	def __init__(self, name="Policeman"):
		"""Constructor (parameterizable).
		"""

		# Always call parent class' constructor FIRST:
		DomainBehavior.__init__(self, name)

		# STATE:
		#  Define 'state' attribute (initial sate):
		self.state = PolicemanMode("idle")

		# ELAPSED TIME:
		#  Initialize 'elapsed time' attribute if required
		#  (by default, value is 0.0):
		self.elapsed = 0

		# PORTS:
		#  Declare as many input and output ports as desired
		#  (usually store returned references in local variables):
		#self.OUT = self.addOutPort(name='OUT')

		###
		# Autonomous system (no input ports),
		# so no External Transition Function required
		#

	###
	def intTransition(self):
		"""Internal Transition Function.
		   The policeman works forever, so only one mode.
		"""

		state = self.state.get()

		if state == "idle":
			return PolicemanMode("working")
			#self.state = PolicemanMode("working")
		elif state == "working":
			return PolicemanMode("idle")
			#self.state = PolicemanMode("idle")
		else:
			print "unknown state <%s> in Policeman internal transition function"% state

	###
	def outputFnc(self):
		"""Output Funtion.
		"""

		# Send messages (events) to a subset of the atomic-DEVS'
		# output ports by means of the 'poke' method, i.e.:
		# The content of the messages is based (typically) on current State.

		state = self.state.get()

		if state == "idle":
			#self.poke(self.OUT, {self.OUT: ["toManual"]})
			return {self.OPorts[0]: ["toManual"]}
		elif state == "working":
#			self.poke(self.OUT, {self.OUT: ["toAutonomous"]})
			return {self.OPorts[0]: ["toAutonomous"]}
		else:
			print "unknown state <%s> in Policeman output function"%state

	###
	def timeAdvance(self):
		"""Time-Advance Function.
		"""

		# Compute 'ta', the time to the next scheduled internal transition,
		# based (typically) on current State.

		state = self.state.get()

		if state == "idle":
			return 200
		elif state == "working":
			return 100
		else:
			print "unknown state <%s> in Policeman time advance function"% state

def main():
    pass

if __name__ == '__main__':
    main()
