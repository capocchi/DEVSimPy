# -*- coding: utf-8 -*-

"""
Name: SimpleLayer.py
Brief descritpion: two inputs and one output.

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
class SimpleLayer(DomainBehavior):
    """
    """

    def __init__(self):
        DomainBehavior.__init__(self)

        ### local copy

        self.state = {'status': 'IDLE', 'sigma': INFINITY }

        self.prec_msg = None
        self.flow_msg = None

    def intTransition(self):
        """
        """
        self.state['sigma'] = INFINITY
        self.state['status'] = 'IDLE'
        self.prec_msg=None
        self.flow_msg=None

    def outputFnc(self):
        """
        """
        assert self.prec_msg and self.flow_msg

        val = (self.prec_msg*20 + self.flow_msg*80)/100.0
        self.poke(self.OPorts[0], Message([val, 0, 0]), self.timeNext)

    def extTransition(self):
        """
        """
        self.prec_msg = peek(self.IPorts[0])
        self.flow_msg = peek(self.IPorts[1])

        if self.prec_msg and self.flow_msg:
            self.state['status'] = 'BUZY'
            self.state['sigma'] = 0
        else:
            self.state['sigma'] = INFINITY

    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return "SimpleLayer"
