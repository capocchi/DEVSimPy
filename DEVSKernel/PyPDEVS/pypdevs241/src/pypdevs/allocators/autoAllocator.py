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

class AutoAllocator(object):
    """
    Allocate all models in a static manner, simply trying to divide the number of models equally.
    Our 'heuristic' is to allocate in chunks as defined in the root coupled model.
    """
    def allocate(self, models, edges, nr_nodes, total_activities):
        """
        Calculate allocations for the nodes, using the information provided.

        :param models: the models to allocte
        :param edges: the edges between the models
        :param nr_nodes: the number of nodes to allocate over. Simply an upper bound!
        :param total_activities: activity tracking information from each model
        :returns: allocation that was found
        """
        allocation = {}

        allocated_topmost = {}
        current_node = 0

        total_models = len(models)

        for model in models:
            # Not yet allocated, so allocate it somewhere
            child = model
            searchmodel = model
            while searchmodel.parent is not None:
                child = searchmodel
                searchmodel = searchmodel.parent
            # searchmodel is now the root model
            # child is its 1st decendant, on which we will allocate
            try:
                node = allocated_topmost[child]
            except KeyError:
                current_node = (current_node + 1) % nr_nodes
                allocated_topmost[child] = current_node
                node = current_node
            allocation[model.model_id] = node

        return allocation

    def getTerminationTime(self):
        """
        Returns the time it takes for the allocator to make an 'educated guess' of the advised allocation.
        This time will not be used exactly, but as soon as the GVT passes over it. While this is not exactly 
        necessary, it avoids the overhead of putting such a test in frequently used code.

        :returns: float -- the time at which to perform the allocations (and save them)
        """
        # No need for any run time information
        return 0.0
