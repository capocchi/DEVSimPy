# -*- coding: Latin-1 -*-
"""
The Activity Heap is based on a heap, though allows for reschedules. 

To allow reschedules to happen, a model is accompagnied by a flag to 
indicate whether or not it is still valid. 
As soon as a model is rescheduled, the flag of the previously scheduled 
time is set and another entry is added. This causes the heap to become *dirty*, 
requiring a check for the flag as soon as the first element is requested.

Due to the possibility for a dirty heap, the heap will be cleaned up as 
soon as the number of invalid elements becomes too high. 
This cleanup method has O(n) complexity and is therefore only 
ran when the heap becomes way too dirty.

Another problem is that it might consume more memory than other schedulers, 
due to invalid elements being kept in memory. 
However, the actual model and states are not duplicated as they are references. 
The additional memory requirement should not be a problem in most situations.

The 'activity' part from the name stems from the fact that only models where 
the *timeNext* attribute is smaller than infinity will be scheduled. 
Since these elements are not added to the heap, they aren't taken into account 
in the complexity. This allows for severe optimisations in situations where 
a lot of models can be scheduled for infinity.

Of all provided schedulers, this one is the most mature due to it being the 
oldest and also the default scheduler. It is also applicable in every situation 
and it offers sufficient performance in most cases.

This scheduler is ideal in situations where (nearly) no reschedules happen 
and where most models transition at a different time.

It results in slow behaviour in situations requiring lots of rescheduling, 
and thus lots of dirty elements.

This method is also applied in the VLE simulator and is the common approach 
to heap schedulers that require invalidation. It varies from the scheduler in 
ADEVS due to the heap from the heapq library being used, which doesn't offer 
functions to restructure the heap. 
Reimplementing these methods in pure Python would be unnecessarily slow.
"""
from heapq import heappush, heappop, heapify
from .logger import *

class SchedulerAH(object):
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
            if model.timeNext[0] != float('inf'):
                self.id_fetch[model.model_id] = [model.timeNext, model.model_id, True, model]
                heappush(self.heap, self.id_fetch[model.model_id])
            else:
                self.id_fetch[model.model_id] = [model.timeNext, model.model_id, False, model]
        
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
        if model.timeNext[0] != float('inf'):
            self.id_fetch[model.model_id][2] = True
            heappush(self.heap, self.id_fetch[model.model_id])

    def unschedule(self, model):
        """
        Unschedule a model

        :param model: model to unschedule
        """
        #assert debug("Unscheduling " + str(model))
        if model.timeNext != float('inf'):
            self.invalids += 1
        # Update the referece still in the heap
        self.id_fetch[model.model_id][2] = False
        # Remove the reference in our id_fetch
        self.id_fetch[model.model_id] = None
        self.maxInvalids -= 2

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
                elif event[0][0] != inf:
                    self.invalids += 1
                event[2] = False
            if model.timeNext[0] != inf:
                self.id_fetch[model.model_id] = [model.timeNext, model.model_id, True, model]
                heappush(self.heap, self.id_fetch[model.model_id])
        #assert debug("Optimizing heap")
        if self.invalids >= self.maxInvalids:
            #assert info("Heap compaction in progress")
            self.heap = [i for i in self.heap if i[2] and (i[0][0] != inf)]
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
