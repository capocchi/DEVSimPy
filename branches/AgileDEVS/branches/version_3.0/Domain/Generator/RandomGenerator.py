# -*- coding: utf-8 -*-

from Core.DomainInterface.DomainBehavior import DomainBehavior
from Core.DomainInterface.Object import Message

import random

class RandomGenerator(DomainBehavior):
    """
    @author: Bastien POGGI
    @organization: University Of Corsica
    @contact: bpoggi@univ-corse.fr
    @since: 2010.12.1
    @version: 1.0
    """

    def __init__(self,minValue=0,maxValue=10,minStep=1,maxStep=1):

        DomainBehavior.__init__(self)

        self.state = {
                        'sigma':0
                     }
        self.minValue = minValue
        self.maxValue = maxValue
        self.minStep = minStep
        self.maxStep = maxStep
        self.msg = Message(None,None)

#       def extTransition(self):
#            pass

    def outputFnc(self):

        numberMessage = random.randint(1,len(self.OPorts)) #Number message to send
        portsToSend = random.sample(self.OPorts,numberMessage) #The port with number message

        for port in portsToSend:
            value = random.randint(self.minValue,self.maxValue)
            self.msg.value = [value,0.0,0.0]
            self.msg.time = self.timeNext
            self.poke(port,self.msg)

    def intTransition(self):
        self.state['sigma'] = random.randint(self.minStep,self.maxStep)

    def __str__(self):
        return "RandomGenerator"

    def timeAdvance(self):
        return self.state['sigma']
