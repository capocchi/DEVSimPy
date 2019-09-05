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
The Sorted List scheduler is the simplest scheduler available, though it has extremely bad performance in several situations.

It simply keeps a list of all models, which is sorted on time_next. No operations have any influence on this heap itself, as there is no real internal representation. As soon as the imminent models are requested, this list is sorted again and the first elements are returned.
"""
from pypdevs.logger import *

class SchedulerSL(object):
    """
    Scheduler class itself
    """
    def __init__(self, models, epsilon, totalModels):
        """
        Constructor

        :param models: all models in the simulation
        """
        self.models = list(models)
        self.epsilon = epsilon
                                
    def schedule(self, model):
        """
        Schedule a model

        :param model: the model to schedule
        """
        self.models.append(model)
        self.models.sort(key=lambda i: i.time_next)

    def unschedule(self, model):
        """
        Unschedule a model

        :param model: model to unschedule
        """
        self.models.remove(model)

    def massReschedule(self, reschedule_set):
        """
        Reschedule all models provided. 
        Equivalent to calling unschedule(model); schedule(model) on every element in the iterable.

        :param reschedule_set: iterable containing all models to reschedule
        """
        self.models.sort(key=lambda i: i.time_next)

    def readFirst(self):
        """
        Returns the time of the first model that has to transition

        :returns: timestamp of the first model
        """
        return self.models[0].time_next

    def getImminent(self, time):
        """
        Returns a list of all models that transition at the provided time, with the specified epsilon deviation allowed.

        :param time: timestamp to check for models

        .. warning:: For efficiency, this method only checks the **first** elements, so trying to invoke this function with a timestamp higher than the value provided with the *readFirst* method, will **always** return an empty set.
        """
        imm_children = []
        t, age = time
        try:
            # Age must be exactly the same
            count = 0
            while (abs(self.models[count].time_next[0] - t) < self.epsilon and 
                    self.models[count].time_next[1] == age):
                # Don't pop, as we want to keep all models in the list
                imm_children.append(self.models[count])
                count += 1
        except IndexError:
            pass
        return imm_children
