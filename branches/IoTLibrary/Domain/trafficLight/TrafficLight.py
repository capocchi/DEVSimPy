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

from TrafficLightMode import TrafficLightMode

class TrafficLight(DomainBehavior):
	"""A traffic light
	"""

	###
	def __init__(self, name="TrafficLight"):
		"""Constructor (parameterizable).
		"""

		# Always call parent class' constructor FIRST:
		DomainBehavior.__init__(self, name)

		# STATE:
		#  Define 'state' attribute (initial sate):
		self.state = TrafficLightMode("red")

		# ELAPSED TIME:
		#  Initialize 'elapsed time' attribute if required
		#  (by default, value is 0.0):
		self.elapsed = 1.5
		# with elapsed time initially 1.5 and initially in
		# state "red", which has a time advance of 60,
		# there are 60-1.5 = 58.5time-units  remaining until the first
		# internal transition

		# PORTS:
		#  Declare as many input and output ports as desired
		#  (usually store returned references in local variables):
		#self.INTERRUPT = self.addInPort(name="INTERRUPT")
		#self.OBSERVED = self.addOutPort(name="OBSERVED")

	###
	def extTransition(self, inputs):
		"""External Transition Function."""

		# Compute the new state 'Snew' based (typically) on current
		# State, Elapsed time parameters and calls to 'self.peek(self.IN)'.
		input = inputs.get(self.IPorts[0])[0]
		#input = self.peek(self.INTERRUPT).values()[0]

		state = self.state.get()
		
		if input == "toManual":
			if state == "manual":
				return TrafficLightMode("manual")
				# staying in manual mode
				#self.state = TrafficLightMode("manual")
			if state in ("red", "green", "yellow"):
				return TrafficLightMode("manual")
				#self.state = TrafficLightMode("manual")
			else:
				print "unknown state <%s> in TrafficLight external transition function"% state

		if input == "toAutonomous":
			if state == "manual":
				return TrafficLightMode("red")
				#self.state = stTrafficLightMode("red")
			else:
				print "unknown state <%s> in TrafficLight external transition function"% state

	###
	def intTransition(self):
		"""Internal Transition Function.
		"""

		state = self.state.get()

		if state == "red":
			return TrafficLightMode("green")
			#self.state =  TrafficLightMode("green")
		elif state == "green":
			return TrafficLightMode("yellow")
			#self.state = TrafficLightMode("yellow")
		elif state == "yellow":
			return TrafficLightMode("red")
			#self.state = TrafficLightMode("red")
		else:
			print "unknown state <%s> in TrafficLight internal transition function"% state

	###
	def outputFnc(self):
		"""Output Funtion.
		"""

		# A colourblind observer sees "grey" instead of "red" or "green".

		# BEWARE: ouput is based on the OLD state
		# and is produced BEFORE making the transition.
		# We'll encode an "observation" of the state the
		# system will transition to !

		# Send messages (events) to a subset of the atomic-DEVS'
		# output ports by means of the 'poke' method, i.e.:
		# The content of the messages is based (typically) on current State.

		state = self.state.get()

		if state == "red":
			return {self.OPorts[0]: ["grey"]}
			#self.poke(self.OBSERVED, {self.OBSERVED: ["grey"]})
			# NOT self.poke(self.OBSERVED, "grey")
		elif state == "green":
			return {self.OPorts[0]: ["yellow"]}
			#self.poke(self.OBSERVED, {self.OBSERVED: ["yellow"]})
			# NOT self.poke(self.OBSERVED, "grey")
		elif state == "yellow":
			return {self.OPorts[0]: ["grey"]}
			#self.poke(self.OBSERVED, {self.OBSERVED: ["grey"]})
			# NOT self.poke(self.OBSERVED, "yellow")
		else:
			print "unknown state <%s> in TrafficLight external transition function"% state

	###
	def timeAdvance(self):
		"""Time-Advance Function.
		"""

		# Compute 'ta', the time to the next scheduled internal transition,
		# based (typically) on current State.

		state = self.state.get()

		if state == "red":
			return 60
		elif state == "green":
			return 50
		elif state == "yellow":
			return 10
		elif state == "manual":
			return INFINITY
		else:
			print "unknown state <%s> in TrafficLight time advance transition function"% state

def main():
    pass

if __name__ == '__main__':
    main()
