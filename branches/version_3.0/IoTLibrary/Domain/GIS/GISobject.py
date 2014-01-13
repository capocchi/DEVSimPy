# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

class GISobject(DomainBehavior):
        """
        This class model a abstract geographical object
        @author: Laurent CAPOCCHI
        @author: Bastien POGGI
        @organization: University Of Corsica
        @contact: capocchi@univ-corse.fr
        @contact: bpoggi@univ-corse.fr
        @since: 2010.03.28
        @version: 1.0
        """

#INITIALISATION
	def __init__(self):
           DomainBehavior.__init__(self)

#DEVS
	def outputFnc(self):
            self.poke(self.OPorts[0], Message([self], self.timeNext))

	def intTransition(self):
            self.state["sigma"] = INFINITY

	def timeAdvance(self):
            return self.state['sigma']

#INTERNAL FUNCTIONS
	def __str__(self):
            return "GISobject"

        def __deepcopy__(self, visit):
            return self
