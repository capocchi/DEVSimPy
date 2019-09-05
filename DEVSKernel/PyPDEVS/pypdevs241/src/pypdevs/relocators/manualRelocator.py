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
Relocator for user-provided relocation directives
"""

class ManualRelocator(object):
    """
    Main class
    """
    def __init__(self):
        """
        Initialize the relocator
        """
        self.directives = []

    def setController(self, controller):
        """
        Sets the controller
        """
        pass

    def getRelocations(self, gvt, activities, horizon):
        """
        Fetch the relocations that are pending for the current GVT

        :param gvt: current GVT
        :param activities: the activities being passed on the GVT ring
        :param horizon: the activity horizon that was used
        :returns: dictionary containing all relocations
        """
        relocate = {}
        for index, directive in enumerate(self.directives):
            if directive[0] < gvt:
                relocate[directive[1]] = directive[2]
            else:
                self.directives = self.directives[index:]
                break
        else:
            self.directives = []
        return relocate

    def addDirective(self, time, model, destination):
        """
        Add a relocation directive, this relocation will be scheduled and will be executed as soon as the GVT passes over the provided time.

        :param time: the time at which this should happen
        :param model: the model that has to be moved (its model_id)
        :param destination: the destination kernel to move it to
        """
        self.directives.append([time, model, destination])
        self.directives.sort()

    def useLastStateOnly(self):
        """
        Determines whether or not the activities of all steps should be accumulated, or only a single state should be used.

        :returns: boolean -- True if the relocator works with a single state
        """
        # Set to false to allow activity tracking plots
        return False
