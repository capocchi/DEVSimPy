# -*- coding: utf-8 -*-

"""
Name : To_Disk.py
Brief descritpion : Atomic Model writing results in text file on the disk
Author(s) : Laurent CAPOCCHI <capocchi@univ-corse.fr>
Version :  2.0
Last modified : 21/03/09
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

### just for python 2.5
from __future__ import with_statement

from Domain.Collector.QuickScope import *
import random
from decimal import *
import os

#  ================================================================    #
class To_Disk(QuickScope):
    """     Atomic Model writing on the disk.
    """

    ###
    def __init__(self, fileName = os.path.join(os.getcwd(),"result%d"%random.randint(1,100)), eventAxis = False, comma = " ", ext = '.dat', col = 0):
        """ Constructor.

                @param fileName : Name of output fileName
                @param eventAxis : Flag to plot depending events axis
                @param comma : Comma symbol
                @param ext : Output file extension
                @param col : Considered coloum
        """
        QuickScope.__init__(self)

        # local copy
        self.fileName = fileName
        self.comma = comma
        self.ext = ext
        self.col = col

        #decimal precision
        getcontext().prec = 6

        ### last time value for delete engine and
        self.last_time_value = {}

        ### buffer position with default lenght 100
        self.pos = [-1]*100

        ### event axis flag
        self.ea = eventAxis

        ### remove old files corresponding to 1000 presumed ports
        for np in range(1000):
            fn = "%s%d%s"%(self.fileName, np, self.ext)
            if os.path.exists(fn):
                os.remove(fn)
    ###
    def extTransition(self):
        """
        """

        n = len(self.IPorts)
        if len(self.pos) > n:
            self.pos = self.pos[0:n]

        for np in xrange(n):

            msg = self.peek(self.IPorts[np])

            ### filename
            fn = "%s%d%s"%(self.fileName, np, self.ext)

            ### remove all old file starting
            if self.timeLast == 0 and self.timeNext == INFINITY:
                self.last_time_value[fn] = 0.0

            if msg:

                # if step axis is choseen
                if self.ea:
                    self.ea += 1
                    t = self.ea
                    self.last_time_value.update({fn:-1})
                else:

                    if fn not in self.last_time_value:
                        self.last_time_value.update({fn:1})

                    t = Decimal(str(float(msg.time)))

                val = msg.value[self.col]
                if isinstance(val, int) or isinstance(val, float):
                    v = Decimal(str(float(val)))
                else:
                    v = val

                ### run only with python 2.6
                with open(fn, 'a') as f:

                    if t == self.last_time_value[fn]:
                        if self.pos[np] == -1:
                            self.pos[np] = 0
                        f.seek(self.pos[np], os.SEEK_SET)
                        f.truncate(self.pos[np])
                        f.write("%s%s%s\n"%(t,self.comma,v))

                    else:
                        self.pos[np] = f.tell()
                        f.write("%s%s%s\n"%(t,self.comma,v))
                        self.last_time_value[fn] = t

                del msg

        self.state["sigma"] = 0

    ###
    def __str__(self):return "To_Disk"
