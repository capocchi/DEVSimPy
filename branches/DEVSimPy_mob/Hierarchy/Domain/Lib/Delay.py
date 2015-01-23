# -*- coding: utf-8 -*-

"""
Name: Delay.py
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
class Delay(DomainBehavior):
    """
    """

    def __init__(self, coef=0.0):
        """
            @param coef : time coef
        """

        DomainBehavior.__init__(self)

        ### local copy
        self.coef = coef

        self.state = {'status': 'IDLE', 'sigma': INFINITY}

        self.msg = None

    def intTransition(self):
        """
        """
        self.state['sigma'] = INFINITY
        self.state['status'] = 'IDLE'

    def outputFnc(self):
        """
        """
        self.poke(self.OPorts[0], self.msg)

    def extTransition(self):
        """
        """
        print "zdc"
        self.msg = self.peek(self.IPorts[0])

        self.state['sigma'] += self.coef
        self.state['status'] = 'BUZY'

    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return self.__class__.__name__
