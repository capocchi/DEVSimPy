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
.. warning:: Do **not** use this scheduler!

This scheduler will only work if all models are scheduled at exactly the same time, or are not scheduled at all (scheduling at infinity is allowed though).
"""
from heapq import heappush, heappop
from pypdevs.logger import *

class SchedulerDT(object):
    """
    Scheduler class itself
    """
    def __init__(self, models, epsilon, total_models):
        """
        Constructor

        :param models: all models in the simulation
        """
        self.ready = set()
        self.infinite = float('inf')
        for m in models:
            if m.time_next[0] != self.infinite:
                self.ready.add(m)

    def schedule(self, model):
        """
        Schedule a model

        :param model: the model to schedule
        """
        if model.time_next[0] != self.infinite:
            self.ready.add(model)

    def unschedule(self, model):
        """
        Unschedule a model

        :param model: model to unschedule
        """
        try:
            self.ready.remove(model)
        except KeyError:
            pass

    def massReschedule(self, reschedule_set):
        """
        Reschedule all models provided. 
        Equivalent to calling unschedule(model); schedule(model) on every element in the iterable.

        :param reschedule_set: iterable containing all models to reschedule
        """
        for model in reschedule_set:
            try:
                if model.time_next[0] != self.infinite:
                    self.ready.add(model)
                else:
                    self.ready.remove(model)
            except KeyError:
                pass

    def readFirst(self):
        """
        Returns the time of the first model that has to transition

        :returns: timestamp of the first model
        """
        val = self.ready.pop()
        self.ready.add(val)
        return val.time_next

    def getImminent(self, time):
        """
        Returns a list of all models that transition at the provided time, with the specified epsilon deviation allowed.

        :param time: timestamp to check for models

        .. warning:: For efficiency, this method only checks the **first** elements, so trying to invoke this function with a timestamp higher than the value provided with the *readFirst* method, will **always** return an empty set.
        """
        t, age = time
        try:
            val = self.ready.pop()
            self.ready.add(val)
            cpy = self.ready
            self.ready = set()
            return cpy
        except KeyError:
            return []
