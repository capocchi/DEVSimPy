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

class MyAllocator(object):
    """
    Allocate all models at the start of the simulation. After this, model relocation is handed over to a relocator.
    """
    def allocate(self, models, edges, nrnodes, totalActivities):
        """
        Calculate allocations for the nodes, using the information provided.

        :param models: the models to allocte
        :param edges: the edges between the models
        :param nrnodes: the number of nodes to allocate over. Simply an upper bound!
        :param totalActivities: activity tracking information from each model
        :returns: allocation that was found
        """
        # Return something of the form: {0: 0, 1: 0, 2: 0, 3: 1}
        # To allocate model_ids 0, 1 and 2 to node 0 and model_id 3 to node 1
        return {0: 0, 1: 0, 2: 0, 3: 1}

    def getTerminationTime(self):
        """
        Returns the time it takes for the allocator to make an 'educated guess' of the advised allocation.
        This time will not be used exactly, but as soon as the GVT passes over it. While this is not exactly 
        necessary, it avoids the overhead of putting such a test in frequently used code.

        :returns: float -- the time at which to perform the allocations (and save them)
        """
        # No need for any run time information means 0.0
        return 0.0
