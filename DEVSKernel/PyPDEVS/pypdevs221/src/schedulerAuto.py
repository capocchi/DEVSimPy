# -*- coding: Latin-1 -*-
"""
Automaticly polymorphic scheduler. It will automatically adapt to your scheduling requests, though at a slight overhead due to the indirection and statistics gathering. If you know what is your optimal scheduler, please choose this one. If the access pattern varies throughout the simulation, this scheduler is perfect for you. It will choose between the HeapSet and Minimal List scheduler.

.. warning:: Barely tested, certainly not with distribution and relocation!!! **Use with caution!!!***

"""
from .schedulerHS import SchedulerHS
from .schedulerML import SchedulerML

class SchedulerAuto(object):
    """
    The polymorphic scheduler class
    """
    def __init__(self, models, epsilon, totalModels):
        """
        Constructor

        :param models: the models to schedule
        :param epsilon: the allowed deviation
        """
        self.epsilon = epsilon
        self.models = list(models)
        self.totalModels = totalModels
        self.schedulerType = SchedulerHS
        self.subscheduler = SchedulerHS(self.models, self.epsilon, totalModels)

        # Statistics
        self.totalSchedules = 0
        self.collidingSchedules = 0

    def swapSchedulerTo(self, scheduler):
        """
        Swap the current subscheduler to the provided one. If the scheduler is already in use, no change happens.

        :param scheduler: the *class* to switch to
        """
        if scheduler == self.schedulerType:
            return
        self.schedulerType = scheduler
        self.subscheduler = scheduler(self.models, self.epsilon, self.totalModels)

    def schedule(self, model):
        """
        Schedule a model

        :param model: the model to schedule
        """
        self.models.append(model)
        return self.subscheduler.schedule(model)

    def unschedule(self, model):
        """
        Unschedule a model

        :param model: the mode to unschedule
        """
        self.models.remove(model)
        return self.subscheduler.unschedule(model)

    def massReschedule(self, reschedule_set):
        """
        Reschedule all models

        :param reschedule_set: the set of models to reschedule
        """
        self.collidingSchedules += len(reschedule_set)
        self.totalSchedules += 1
        if self.totalSchedules > 100:
            if self.collidingSchedules > 5 * len(self.models):
                # This means that 5/100 of the models is scheduled in every iteration
                self.swapSchedulerTo(SchedulerML)
            elif self.collidingSchedules < 500:
                self.swapSchedulerTo(SchedulerHS)
            self.collidingSchedules = 0
            self.totalSchedules = 0
        return self.subscheduler.massReschedule(reschedule_set)

    def readFirst(self):
        """
        Fetch the time of the first model

        :returns: (time, age) -- time of the first scheduled model
        """
        return self.subscheduler.readFirst()

    def getImminent(self, time):
        """
        Returns the imminent models for the provided time

        :param time: time to check for
        """
        return self.subscheduler.getImminent(time)
