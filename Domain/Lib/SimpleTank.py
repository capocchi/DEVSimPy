# -*- coding: utf-8 -*-

"""
Name: SimpleTank.py
Brief descritpion:
Author(s): L. Capocchi and JF. Santucci <{capocchi, santucci}@univ-corse.fr>
Version:  1.0
Last modified: 2014.11.24
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from __future__ import with_statement

from DomainInterface.DomainBehavior import DomainBehavior
from Domain.Basic.Object import Message

import os.path

#    ======================================================================    #
class SimpleTank(DomainBehavior):
    """
    """

    def __init__(self):
        DomainBehavior.__init__(self)

        ### local copy

        self.state = {'status': 'IDLE', 'sigma': INFINITY }

        self.msg1 = None
        self.msg2 = None

        ### tank buffer
        self.buffer = 0

    def intTransition(self):
        self.state['sigma'] = INFINITY
        self.state['status'] = 'IDLE'
        self.msg1=None
        self.msg2=None

    def outputFnc(self):

        ### test temp
        if self.msg1.value[0] > 0:
            self.buffer -= self.buffer/2.0
            flow = self.msg2.value[0]
            msg = Message([self.buffer+flow,0,0], self.timeNext)
        else:
            self.buffer += self.msg2.value[0]
            msg = Message([0,0,0], self.timeNext)

        self.poke(self.OPorts[0], msg)

    def extTransition(self):
        """
        """
        msg1 = self.peek(self.IPorts[0])
        msg2 = self.peek(self.IPorts[1])

        if msg1: self.msg1 = msg1
        if msg2: self.msg2 = msg2

        if self.msg1 and self.msg2:
            self.state['status'] = 'BUZY'
            self.state['sigma'] = 0
        else:
            self.state['sigma'] = INFINITY

    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return self.__class__.__name__
