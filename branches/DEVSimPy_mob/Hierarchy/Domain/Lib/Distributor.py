# -*- coding: utf-8 -*-

"""
Name: Distributor.py
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
class Distributor(DomainBehavior):
    """
    """

    def __init__(self):
        DomainBehavior.__init__(self)

        ### local copy


        self.state = {'status': 'IDLE', 'sigma': INFINITY }

        self.msg = None

    def intTransition(self):
        """
        """
        self.state['sigma'] = INFINITY
        self.state['status'] = 'IDLE'

    def outputFnc(self):
        """
        """
        val1 = self.msg.value[0]*45/100
        val2 = self.msg.value[0]*35/100
        val3 = self.msg.value[0]*20/100

        self.poke(self.OPorts[0], Message([val1,0,0], self.timeNext))
        self.poke(self.OPorts[1], Message([val2,0,0], self.timeNext))
        self.poke(self.OPorts[2], Message([val3,0,0], self.timeNext))

    def extTransition(self):
        """
        """
        self.msg = self.peek(self.IPorts[0])

        self.state['status'] = 'BUZY'
        self.state['sigma'] = 0

    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return self.__class__.__name__
