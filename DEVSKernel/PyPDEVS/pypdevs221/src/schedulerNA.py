# -*- coding: Latin-1 -*-
"""
The No Age scheduler is based on the Heapset scheduler, though it does not take age into account.

.. warning:: This scheduler does not take the age into account, making it **unusable** in simulations where the *timeAdvance* function can return (exactly) 0. If unsure, do **not** use this scheduler, but the more general Heapset scheduler.

The heap will contain only the timestamps of events that should happen. One of the dictionaries will contain the actual models that transition at the specified time. The second dictionary than contains a reverse relation: it maps the models to their timeNext. This reverse relation is necessary to know the *old* timeNext value of the model. Because as soon as the model has its timeNext changed, its previously scheduled time will be unknown. This 'previous time' is **not** equal to the *timeLast*, as it might be possible that the models wait time was interrupted.

For a schedule, the model is added to the dictionary at the specified timeNext. In case it is the first element at this location in the dictionary, we also add the timestamp to the heap. This way, the heap only contains *unique* timestamps and thus the actual complexity is reduced to the number of *different* timestamps. Furthermore, the reverse relation is also updated.

Unscheduling is done similarly by simply removing the element from the dictionary.

Rescheduling is a slight optimisation of unscheduling, followed by scheduling.

This scheduler does still schedule models that are inactive (their timeNext is infinity), though this does not influence the complexity. The complexity is not affected due to infinity being a single element in the heap that is always present. Since a heap has O(log(n)) complexity, this one additional element does not have a serious impact.

The main advantage over the Activity Heap is that it never gets dirty and thus doesn't require periodical cleanup. The only part that gets dirty is the actual heap, which only contains small tuples. Duplicates of these will also be reduced to a single element, thus memory consumption should not be a problem in most cases.

This scheduler is ideal in situations where most transitions happen at exactly the same time, as we can then profit from the internal structure and simply return the mapped elements. It results in sufficient efficiency in most other cases, mainly due to the code base being a lot smaller then the Activity Heap.
"""
from heapq import heappush, heappop
from .logger import *

class SchedulerNA(object):
    """
    Scheduler class itself
    """
    def __init__(self, models, epsilon, totalModels):
        """
        Constructor

        :param models: all models in the simulation
        """
        self.heap = []
        self.reverse = [None] * totalModels
        self.mapped = {}
        self.infinite = float('inf')
        # Init the basic 'inactive' entry here, to prevent scheduling in the heap itself
        self.mapped[self.infinite] = set()
        self.epsilon = epsilon
        for m in models:
            self.schedule(m)

    def schedule(self, model):
        """
        Schedule a model

        :param model: the model to schedule
        """
        try:
            self.mapped[model.timeNext[0]].add(model)
        except KeyError:
            self.mapped[model.timeNext[0]] = set([model])
            heappush(self.heap, model.timeNext[0])
        try:
            self.reverse[model.model_id] = model.timeNext[0]
        except IndexError:
            self.reverse.append(model.timeNext[0])

    def unschedule(self, model):
        """
        Unschedule a model

        :param model: model to unschedule
        """
        try:
            self.mapped[self.reverse[model.model_id]].remove(model)
        except KeyError:
            pass
        self.reverse[model.model_id] = None

    def massReschedule(self, reschedule_set):
        """
        Reschedule all models provided. 
        Equivalent to calling unschedule(model); schedule(model) on every element in the iterable.

        :param reschedule_set: iterable containing all models to reschedule
        """
        #NOTE the usage of exceptions is a lot better for the PyPy JIT and nets a noticable speedup
        #     as the JIT generates guard statements for an 'if'
        for model in reschedule_set:
            model_id = model.model_id
            try:
                self.mapped[self.reverse[model_id]].remove(model)
            except KeyError:
                # Element simply not present, so don't need to unschedule it
                pass
            self.reverse[model_id] = tn = model.timeNext[0]
            try:
                self.mapped[tn].add(model)
            except KeyError:
                # Create a tuple with a single entry and use it to initialize the mapped entry
                self.mapped[tn] = set((model, ))
                heappush(self.heap, tn)

    def readFirst(self):
        """
        Returns the time of the first model that has to transition

        :returns: timestamp of the first model
        """
        first = self.heap[0]
        while len(self.mapped[first]) == 0:
            del self.mapped[first]
            heappop(self.heap)
            first = self.heap[0]
        # The age was stripped of
        return (first, 1)

    def getImminent(self, time):
        """
        Returns a list of all models that transition at the provided time, with the specified epsilon deviation allowed.

        :param time: timestamp to check for models

        .. warning:: For efficiency, this method only checks the **first** elements, so trying to invoke this function with a timestamp higher than the value provided with the *readFirst* method, will **always** return an empty set.
        """
        t, age = time
        immChildren = set()
        try:
            first = self.heap[0]
            if (abs(first - t) < self.epsilon):
                #NOTE this would change the original set, though this doesn't matter as it is no longer used
                immChildren = self.mapped.pop(first)
                heappop(self.heap)
                first = self.heap[0]
                while (abs(first - t) < self.epsilon):
                    immChildren |= self.mapped.pop(first)
                    heappop(self.heap)
                    first = self.heap[0]
        except IndexError:
            pass
        return immChildren
