# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# simulator.py --- 'Plain' DEVS Model Simulator
#                     --------------------------------
#                            Copyright (c) 2000
#                             Hans  Vangheluwe
#                            Yentl Van Tendeloo
#                       McGill University (Montréal)
#                     --------------------------------
# Version 2.0                                        last modified: 30/01/13
#  - Split up the scheduler to a seperate file
#    
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
from heapq import *
from .logger import *

from .DEVS import *

class Scheduler(object):
    """
    The scheduler class for events
    """
    def __init__(self, id_fetch):
        """
        Constructor.
        Args:
                id_fetch - list of all models that should be usable
        """
        self.heap = []
        self.id_fetch = id_fetch
        self.invalids = 0
                                
    def schedule(self, model):
        #debug("Scheduling " + str(model))
        self.id_fetch[model.model_id][0] = model.timeNext
        if model.timeNext[0] != float('inf') and not (isinstance(model, RemoteCDEVS)):
            heappush(self.heap, self.id_fetch[model.model_id])

    def unschedule(self, model):
        #debug("Unscheduling " + str(model))
        event = self.id_fetch[model.model_id]
        if event[0] != float('inf'):
            self.invalids += 1
        event[2] = False
        self.id_fetch[model.model_id] = [model.timeNext, event[1], True, event[3]]

    def readFirst(self):
        #debug("Reading first element from heap")
        self.cleanFirst()
        return self.heap[0]

    def cleanFirst(self):
        #debug("Cleaning list")
        try:
            while not self.heap[0][2]:
                heappop(self.heap)
                self.invalids -= 1
        except IndexError:
            # Nothing left, so it as clean as can be
            #debug("None in list")
            pass

    def optimize(self, maxLength):
        #debug("Optimizing heap")
        if self.invalids >= 2 * maxLength:
            assert info("Heap compaction in progress")
            newheap = []
            for i in self.heap:
                if i[2] and (i[0] != float('inf')):
                    newheap.append(i)
            self.heap = newheap
            heapify(self.heap)
            self.invalids = 0
            assert info("Heap compaction complete")

    def getImminent(self, time, epsilon):
        #debug("Asking all imminent models")
        immChildren = []
        try:
            # Age must be exactly the same
            while (abs(self.heap[0][0][0] - time[0]) < epsilon) and (self.heap[0][0][1] == time[1]):
                # Check if the found event is actually still active
                if(self.heap[0][2]):
                    # Active, so event is imminent
                    immChildren.append(self.heap[0][3])
                else:
                    # Wasn't active, but we will have to pop this to get the next
                    # So we can lower the number of invalids
                    self.invalids -= 1

                # Advance the while loop
                heappop(self.heap)
        except IndexError:
            pass
        return immChildren
