# -*- coding: utf-8 -*-

"""
Name: Snow.py
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
class Snow(DomainBehavior):
    """
    """

    def __init__(self):
        DomainBehavior.__init__(self)

        ### local copy


        self.state = {'status': 'IDLE', 'sigma': INFINITY }

    def intTransition(self):
        pass

    def outputFnc(self):
        pass

    def extTransition(self):
        pass

    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return self.__name__
