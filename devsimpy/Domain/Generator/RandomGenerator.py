# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

import sys
import random

class RandomGenerator(DomainBehavior):
    """
    """

    def __init__(self, minValue=0, maxValue=10, minStep=1, maxStep=1, start=0, choice=[]):
        """ Constructor.

            @param minValue: minimum value
            @param maxValue: maximum value
            @param minStep: minimum step
            @param maxStep: maximum step
			@param start: time start
			@param choice: list of items 

        """
        DomainBehavior.__init__(self)

        self.minValue = minValue
        self.maxValue = maxValue
        self.minStep = minStep
        self.maxStep = maxStep
        self.choice = choice

        self.msg = Message(None, None)

        self.initPhase('START',float(start))

    def outputFnc(self):
        """ lambda DEVS function
        """
        numberMessage = random.randint(1, len(self.OPorts))  # Number message to send
        portsToSend = random.sample(self.OPorts, numberMessage)  # The port with number message

        outputs = {}
        for port in portsToSend:
            value = random.choice(self.choice) if self.choice else random.randint(self.minValue, self.maxValue)
            self.msg.value = [value, 0.0, 0.0]
            self.msg.time = self.timeNext
            #adapted with PyPDEVS
            o = self.poke(port, self.msg)
            if o:
               outputs.update(o)

        return outputs

    def intTransition(self):
        """ DEVS Transition function
        """
        self.holdIn('START',random.randint(self.minStep, self.maxStep))
        return self.getState()

    def __str__(self):
        """ str function
        """
        return "RandomGenerator"

    def timeAdvance(self):
        """ Time advance function
        """
        return self.getSigma()
