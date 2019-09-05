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
The Minimal List scheduler is the simplest scheduler available, 
though it has extremely bad performance in most cases.

It simply keeps a list of all models. As soon as a reschedule happens, 
the list is checked for the minimal value, which is stored. 
When the imminent models are requested, the lowest value that was found 
is used to immediatelly return [], 
or it iterates the complete list in search of models that qualify.
"""

class SchedulerChibiList(object):
    """
    Scheduler class itself
    """
    def __init__(self, models, epsilon, total_models):
        """
        Constructor

        :param models: all models in the simulation
        """
        # Make a copy!
        self.models = list(models)
        self.minval = float('inf')
        self.epsilon = epsilon
        self.massReschedule([])

    def schedule(self, model):
        """
        Schedule a model

        :param model: the model to schedule
        """
        self.models.append(model)
        if model.time_next < self.minval:
            self.minval = model.time_next

    def unschedule(self, model):
        """
        Unschedule a model

        :param model: model to unschedule
        """
        self.models.remove(model)
        if model.time_next == self.minval:
            self.minval = (float('inf'), float('inf'))
            for m in self.models:
                if m.time_next < self.minval:
                    self.minval = m.time_next

    def massReschedule(self, reschedule_set):
        """
        Reschedule all models provided. 
        Equivalent to calling unschedule(model); schedule(model) on every element in the iterable.

        :param reschedule_set: iterable containing all models to reschedule
        """
        self.minval = float('inf')
        for m in self.models:
            if m.time_next < self.minval:
                self.minval = m.time_next

    def readFirst(self):
        """
        Returns the time of the first model that has to transition

        :returns: timestamp of the first model
        """
        return self.minval

    def getImminent(self, t):
        """
        Returns a list of all models that transition at the provided time, with the specified epsilon deviation allowed.

        :param time: timestamp to check for models

        .. warning:: For efficiency, this method only checks the **first** elements, so trying to invoke this function with a timestamp higher than the value provided with the *readFirst* method, will **always** return an empty set.
        """
        imm_children = []
        for model in self.models:
            if abs(model.time_next - t) < self.epsilon:
                imm_children.append(model)
        return imm_children
