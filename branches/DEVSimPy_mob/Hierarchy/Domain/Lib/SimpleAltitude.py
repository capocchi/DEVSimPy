# -*- coding: utf-8 -*-

"""
Name: SimpleAltitude.py
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
class SimpleAltitude(DomainBehavior):
    """
    """

    def __init__(self):
        DomainBehavior.__init__(self)

        ### local copy

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

        ### 50%
        self.msg.value[0] = 50*self.msg.value[0]
        self.msg.time = self.timeNext

        self.poke(self.OPorts[0], self.msg)

    def extTransition(self):
        """
        """
        self.msg = peeks(self.IPorts[0])

        self.state['status'] = 'BUZY'
        self.state['sigma'] = 0

    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return self.__class__.__name__
