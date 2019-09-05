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

class MyRelocator(object):
    """
    Main class
    """
    def __init__(self):
        """
        Initialize the relocator
        """
        pass

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
        :returns: dictionary containing all relocations
        """
        # Perform a relocation, for example move the model with ID 1 to node 2, and the model with ID 3 to node 0
        # Remaps are allowed to happen to the current location, as they will simply be discarded by the actual relocator
        relocate = {1: 2, 3: 0}
        return relocate

    def lastStateOnly(self):
        """
        Should the sum of all activities within this horizon be used, or simply the activity from the last state?
        This has no effect on performance, but defines which activities the relocator can read.

        Use 'last state only' if you require an abstracted view of the activities at a single timestep (equal to the GVT).
        Use 'all states' if you require all information to be merged, such as in activity tracking.
        """
        # "all states"
        return False
