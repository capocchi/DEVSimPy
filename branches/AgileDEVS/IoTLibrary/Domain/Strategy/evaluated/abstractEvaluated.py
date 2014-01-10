# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

class AbstractEvaluated(DomainBehavior):

	def __init__(self,maxInfluence=0.0):
            DomainBehavior.__init__(self)

            self.state = {'status': 'IDLE','sigma':0}
            self.maxInfluence = maxInfluence


	def __deepcopy__(self, visit):
            return self


	def outputFnc(self):
            self.poke(self.OPorts[0], Message([self], self.timeNext))


	def intTransition(self):
            self.state["sigma"] = INFINITY


	def timeAdvance(self):
            return self.state['sigma']


	def __str__(self):
            return "abstractEvaluated"
        

