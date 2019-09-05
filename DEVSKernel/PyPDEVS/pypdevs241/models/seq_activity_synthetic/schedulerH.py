# -*- coding: Latin-1 -*-
from heapq import heappush, heappop, heapify
from logger import *

class SchedulerH(object):
    """
    Scheduler class itself
    """
    def __init__(self, models, epsilon, totalModels):
        """
        Constructor

        :param models: all models in the simulation
        """
        self.heap = []
        self.id_fetch = [None] * totalModels
        for model in models:
            self.id_fetch[model.model_id] = [model.timeNext, model.model_id, True, model]
            heappush(self.heap, self.id_fetch[model.model_id])
        
        self.invalids = 0
        self.maxInvalids = len(models)*2
        self.epsilon = epsilon

    def schedule(self, model):
        """
        Schedule a model

        :param model: the model to schedule
        """
        #assert debug("Scheduling " + str(model))
        # Create the entry, as we have accepted the model
        elem = [model.timeNext, model.model_id, False, model]
        try:
            self.id_fetch[model.model_id] = elem
        except IndexError:
            # A completely new model
            self.id_fetch.append(elem)
            self.maxInvalids += 2
        # Check if it requires to be scheduled
        self.id_fetch[model.model_id][2] = True
        heappush(self.heap, self.id_fetch[model.model_id])

    def unschedule(self, model):
        """
        Unschedule a model

        :param model: model to unschedule
        """
        # Update the referece still in the heap
        self.id_fetch[model.model_id][2] = False
        # Remove the reference in our id_fetch
        self.id_fetch[model.model_id] = None

    def massReschedule(self, reschedule_set):
        """
        Reschedule all models provided. 
        Equivalent to calling unschedule(model); schedule(model) on every element in the iterable.

        :param reschedule_set: iterable containing all models to reschedule
        """
        #NOTE rather dirty, though a lot faster for huge models
        #assert debug("Mass rescheduling")
        inf = float('inf')
        for model in reschedule_set:
            event = self.id_fetch[model.model_id]
            if event[2]:
                if model.timeNext == event[0]:
                    continue
                self.invalids += 1
                event[2] = False
            self.id_fetch[model.model_id] = [model.timeNext, model.model_id, True, model]
            heappush(self.heap, self.id_fetch[model.model_id])
        #assert debug("Optimizing heap")
        if self.invalids >= self.maxInvalids:
            #assert info("Heap compaction in progress")
            self.heap = [i for i in self.heap if i[2]]
            heapify(self.heap)
            self.invalids = 0
            #assert info("Heap compaction complete")

    def readFirst(self):
        """
        Returns the time of the first model that has to transition

        :returns: timestamp of the first model
        """
        #assert debug("Reading first element from heap")
        self.cleanFirst()
        return self.heap[0][0]

    def cleanFirst(self):
        """
        Clean up the invalid elements in front of the list
        """
        #assert debug("Cleaning list")
        try:
            while not self.heap[0][2]:
                heappop(self.heap)
                self.invalids -= 1
        except IndexError:
            # Nothing left, so it as clean as can be
            #assert debug("None in list")
            pass

    def getImminent(self, time):
        """
        Returns a list of all models that transition at the provided time, with a specified epsilon deviation allowed.

        :param time: timestamp to check for models

        .. warning:: For efficiency, this method only checks the **first** elements, so trying to invoke this function with a timestamp higher than the value provided with the *readFirst* method, will **always** return an empty set.
        """
        #assert debug("Asking all imminent models")
        immChildren = []
        t, age = time
        try:
            # Age must be exactly the same
            first = self.heap[0]
            while (abs(first[0][0] - t) < self.epsilon) and (first[0][1] == age):
                # Check if the found event is actually still active
                if(first[2]):
                    # Active, so event is imminent
                    immChildren.append(first[3])
                    first[2] = False
                else:
                    # Wasn't active, but we will have to pop this to get the next
                    # So we can lower the number of invalids
                    self.invalids -= 1

                # Advance the while loop
                heappop(self.heap)
                first = self.heap[0]
        except IndexError:
            pass
        return immChildren
