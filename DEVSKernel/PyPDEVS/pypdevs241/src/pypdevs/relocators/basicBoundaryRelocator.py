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

from pypdevs.relocators.boundaryRelocator import BoundaryRelocator
from heapq import heappop, heappush, heapify

class BasicBoundaryRelocator(BoundaryRelocator):
    """
    Basic implementation of a boundary relocator
    """
    def __init__(self, swappiness):
        """
        Constructor

        :param swappiness: the swappiness
        """
        BoundaryRelocator.__init__(self)
        self.swappiness = swappiness

    def setController(self, controller):
        """
        Configures the controller of this relocator

        :param controller: the controller
        """
        BoundaryRelocator.setController(self, controller)

    def getRelocations(self, gvt, activities, horizon):
        """
        Return all pending relocations

        :param gvt: current GVT
        :param activities: activities being passed on the GVT ring
        :param horizon: the time over which the activities were gathered
        :returns: all relocations that should be executed
        """
        # Clear all 'semi-global' variables
        self.relocate = {}
        self.model_activities = {}
        self.node_activities = [i[1] for i in activities]
        avg_activity = sum(self.node_activities) / len(self.node_activities)

        reverts = set()

        iterlist = [(activity, node) 
                    for node, activity in enumerate(self.node_activities) 
                    if activity > self.swappiness * avg_activity]
        heapify(iterlist)

        if sum(self.locations) == 0:
            self.locations = [model.location for model in self.model_ids]
            self.boundaries = [{} for _ in range(self.kernels)]
            self.constructBoundaries(self.model_ids)

        while iterlist:
            # Keep going as long as there are nodes that are overloaded
            srcactivity, node = heappop(iterlist)
            # Might have changed in the meantime, though NEVER decreased
            srcactivity = self.node_activities[node]

            # Now 'node' contains the node that has the most activity of all, so try pushing something away
            boundaries = self.boundaries[node]
            destactivity, mindest = \
                min([(self.node_activities[destination], destination) 
                for destination in boundaries 
                if boundaries[destination]])
            boundary = boundaries[mindest]
            source_deviation = srcactivity - avg_activity
            destination_deviation = destactivity - avg_activity
            original_heuristic = abs(source_deviation) + \
                                 abs(destination_deviation)
            move = None
            for option in boundary:
                # Swapping the model would give us the following new 'heuristic'
                model_activity = self.fetchModelActivity(option)
                new_heuristic = abs(source_deviation - model_activity) + \
                                abs(destination_deviation + model_activity)

                if new_heuristic < original_heuristic:
                    move = option.model_id
                    original_heuristic = new_heuristic

            if move is not None:
                # Will migrate model 'move' to 'mindest'
                self.scheduleMove(move, mindest)
                if srcactivity - model_activity > avg_activity:
                    heappush(iterlist, (srcactivity - model_activity, node))
                if destactivity + model_activity > avg_activity:
                    # The destination now also became overloaded, so push from this node as well
                    heappush(iterlist, (destactivity + model_activity, mindest))
        return self.relocate

    def useLastStateOnly(self):
        """
        Determines whether or not the activities of all steps should be accumulated, or only a single state should be used.

        :returns: boolean -- True if the relocator works with a single state
        """
        return False
