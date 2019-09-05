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

class Scheduler(object):
    def __init__(self, models, epsilon, totalModels):
        """
        Constructor

        :param models: all models in the simulation
        """
        # Do your initialisation and schedule all models that are passed in the 'models' parameter
        # NOTE: make a copy of these lists if you want to modify them
        pass

    def schedule(self, model):
        """
        Schedule a new model, that was NOT present in the scheduler before

        :param model: the model to schedule
        """
        pass

    def unschedule(self, model):
        """
        Unschedule a model, so remove it from the scheduler for good

        :param model: model to unschedule
        """
        pass

    def massReschedule(self, reschedule_set):
        """
        Reschedule all models provided, all of them should already be scheduled previously and all should still be left in the scheduler after the rescheduling.

        :param reschedule_set: iterable containing all models to reschedule
        """
        pass

    def readFirst(self):
        """
        Returns the time of the first model that has to transition

        :returns: timestamp of the first model
        """
        pass

    def getImminent(self, time):
        """
        Returns an iterable of all models that transition at the provided time, with the epsilon deviation (from the constructor) allowed.
        For efficiency, this method should only check the **first** elements, so trying to invoke this function with a timestamp higher 
        than the value provided with the *readFirst* method, will **always** return an empty iterable.

        :param time: timestamp to check for models
        :returns: iterable -- all models for that time
        """
        pass
