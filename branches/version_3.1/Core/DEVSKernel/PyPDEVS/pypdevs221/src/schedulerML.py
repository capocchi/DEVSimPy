# -*- coding: Latin-1 -*-
"""
The Minimal List scheduler is the simplest scheduler available, 
though it has extremely bad performance in most cases.

It simply keeps a list of all models. As soon as a reschedule happens, 
the list is checked for the minimal value, which is stored. 
When the imminent models are requested, the lowest value that was found 
is used to immediatelly return [], 
or it iterates the complete list in search of models that qualify.
"""

class SchedulerML(object):
    """
    Scheduler class itself
    """
    def __init__(self, models, epsilon, totalModels):
        """
        Constructor

        :param models: all models in the simulation
        """
        # Make a copy!
        self.models = list(models)
        self.minval = (float('inf'), float('inf'))
        self.epsilon = epsilon
        self.massReschedule([])

    def schedule(self, model):
        """
        Schedule a model

        :param model: the model to schedule
        """
        self.models.append(model)
        if model.timeNext < self.minval:
            self.minval = model.timeNext

    def unschedule(self, model):
        """
        Unschedule a model

        :param model: model to unschedule
        """
        self.models.remove(model)
        if model.timeNext == self.minval:
            for m in self.models:
                if m.timeNext < self.minval:
                    self.minval = m.timeNext

    def massReschedule(self, reschedule_set):
        """
        Reschedule all models provided. 
        Equivalent to calling unschedule(model); schedule(model) on every element in the iterable.

        :param reschedule_set: iterable containing all models to reschedule
        """
        self.minval = (float('inf'), float('inf'))
        for m in self.models:
            if m.timeNext < self.minval:
                self.minval = m.timeNext

    def readFirst(self):
        """
        Returns the time of the first model that has to transition

        :returns: timestamp of the first model
        """
        return self.minval

    def getImminent(self, time):
        """
        Returns a list of all models that transition at the provided time, with the specified epsilon deviation allowed.

        :param time: timestamp to check for models

        .. warning:: For efficiency, this method only checks the **first** elements, so trying to invoke this function with a timestamp higher than the value provided with the *readFirst* method, will **always** return an empty set.
        """
        immChildren = []
        t, age = time
        for model in self.models:
            if abs(model.timeNext[0] - t) < self.epsilon and model.timeNext[1] == age:
                immChildren.append(model)
        return immChildren
