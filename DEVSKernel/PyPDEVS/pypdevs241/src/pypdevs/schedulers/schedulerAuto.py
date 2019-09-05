# Copyright 2014 Modelling, Simulation and Design Lab (MSDL) at 
# McGill University and the University of Antwerp (http://msdl.cs.mcgill.ca/)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Automaticly polymorphic scheduler. It will automatically adapt to your scheduling requests, though at a slight overhead due to the indirection and statistics gathering. If you know what is your optimal scheduler, please choose this one. If the access pattern varies throughout the simulation, this scheduler is perfect for you. It will choose between the HeapSet and Minimal List scheduler.

.. warning:: Barely tested, certainly not with distribution and relocation!!! **Use with caution!!!***

"""
from pypdevs.schedulers.schedulerHS import SchedulerHS
from pypdevs.schedulers.schedulerML import SchedulerML

class SchedulerAuto(object):
    """
    The polymorphic scheduler class
    """
    def __init__(self, models, epsilon, total_models):
        """
        Constructor

        :param models: the models to schedule
        :param epsilon: the allowed deviation
        """
        self.epsilon = epsilon
        self.models = list(models)
        self.total_models = total_models
        self.scheduler_type = SchedulerHS
        self.subscheduler = SchedulerHS(self.models, self.epsilon, total_models)

        # Statistics
        self.total_schedules = 0
        self.colliding_schedules = 0

    def swapSchedulerTo(self, scheduler):
        """
        Swap the current subscheduler to the provided one. If the scheduler is already in use, no change happens.

        :param scheduler: the *class* to switch to
        """
        if scheduler == self.scheduler_type:
            return
        self.scheduler_type = scheduler
        self.subscheduler = scheduler(self.models, self.epsilon, self.total_models)

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
        self.colliding_schedules += len(reschedule_set)
        self.total_schedules += 1
        if self.total_schedules > 100:
            if self.colliding_schedules > 15.0 * len(self.models):
                # This means that 5/100 of the models is scheduled in every iteration
                self.swapSchedulerTo(SchedulerML)
            elif self.colliding_schedules < 500:
                self.swapSchedulerTo(SchedulerHS)
            self.colliding_schedules = 0
            self.total_schedules = 0
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
