# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

class Buffer(DomainBehavior):
        """
        This class model a standard Buffer
        @author: Celine NICOLAI
        @organization: University Of Corsica
        @contact: cnicolai@univ-corse.fr
        @since: 2011.03.15
        @version: 1.1
        """

	def __init__(self,status='ACTIF',content=0.0,capacity=0.0,flowOp=0.0):
		"""
                @param status : ACTIF or INACTIF
                @param content : The water stock
                @param capacity : The maximum content
                """

                DomainBehavior.__init__(self)

		self.state = {	'status': status,
				'sigma':0,
                                'content':content,
                                'capacity':capacity,
                                'flowOp':flowOp
                                }


	def extTransition(self):

                #Input Ports
                self.gain = self.IPorts[0]

                #Gain
                msg = self.peek(self.gain)
                if(msg!=None):
                    gain = msg.value[0]
                    if gain > 0:
                        self.state['content'] += gain


	def outputFnc(self):

            #Output Ports
            self.flowOP = self.OPorts[0]


            msg = Message()
            if self.state['status'] == 'OPEN':
                if self.state['content'] >= self.state['capacity']:
                    msg.value = [self.state['flowOp']]
                    msg.time = self.timeNext
                    self.state['content'] -= self.state['flowOpen']
                    self.poke(self.flowOP,msg)



	def intTransition(self):
            self.evaporation()
            self.leak()
            self.state['sigma']=1

            """
            Pump
            """
            self.state['content'] -= self.state['waterPump']
            self.state['waterPump'] = 0

        def __str__(self):
		return "Buffer"

	def timeAdvance(self):
		return self.state['sigma']
