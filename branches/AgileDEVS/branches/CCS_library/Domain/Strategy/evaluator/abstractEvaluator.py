# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

class AbstractEvaluator(DomainBehavior):

#DEVS
	def __init__(self):
            DomainBehavior.__init__(self)
            self.state = {	'status': 'IDLE',
				'sigma':0,
                         }

	def outputFnc(self):
            self.poke(self.OPorts[0], Message([self], self.timeNext))

	def intTransition(self):
            self.state["sigma"] = INFINITY

	def timeAdvance(self):
            return self.state['sigma']

#INTERNAL
	def __str__(self):
            return "abstractEvaluator"

        def __deepcopy__(self, visit):
            return self

#FUNCTION TO IMPLEMENT IN SUBCLASS
        def getNextPlacement(self, evaluated, location, angle):
            return (0,0)


        def getRangePlacement(self, evaluated, location):
            return []
