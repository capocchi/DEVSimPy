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

from collections import defaultdict

class GreedyAllocator(object):
    """
    Allocate all models in a greedy manner: make the most heavy link local and extend from there on until an average load is reached.
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
        # Run over all edges to create the nodes and link in their edges
        nodes = {}
        remaining_edges = set()
        to_alloc = set()
        for source in edges:
            for destination in edges[source]:
                # A connection from 'source' to 'destination'
                edge = edges[source][destination]
                nodes.setdefault(source, []).append((edge, destination))
                nodes.setdefault(destination, []).append((edge, source))
                remaining_edges.add((edge, source, destination))
                to_alloc.add(destination)
            to_alloc.add(source)
        # OK, nodes are constructed

        # Allocate 1 node too much for spilling
        nr_nodes += 1

        # Find average activity (our target)
        avg_activity = sum([total_activities[i] for i in total_activities]) / nr_nodes

        # Get the strongest edge
        alloc_node = 0
        node_load = []
        allocation = {}
        allocation_rev = defaultdict(set)
        while alloc_node < (nr_nodes - 1):
            while remaining_edges:
                max_edge = max(remaining_edges)
                remaining_edges.remove(max_edge)
                edge_weight, source, destination = max_edge
                if source in to_alloc and destination in to_alloc:
                    break
            else:
                break
            activity_source = total_activities[source.model_id]
            activity_destination = total_activities[destination.model_id]
            node_load.append(activity_source + activity_destination)
            allocation[source.model_id] = alloc_node
            allocation[destination.model_id] = alloc_node
            allocation_rev[alloc_node].add(source)
            allocation_rev[alloc_node].add(destination)
            to_alloc.remove(source)
            to_alloc.remove(destination)
            while node_load[alloc_node] < average_activity:
                edge_search = []
                for edge in remaining_edges:
                    if ((edge[1] in allocation_rev[alloc_node] and
                         edge[2] in to_alloc) or
                        (edge[2] in allocation_rev[alloc_node] and
                         edge[1] in to_alloc)):
                        edge_search.append(edge)
                if not edge_search:
                    break
                # Allocate some more nodes
                max_edge = max(edge_search)
                remaining_edges.remove(max_edge)
                edge_weight, source, destination = max_edge
                # Ok, this is an unbound connection, so add it
                if source in to_alloc:
                    to_alloc.remove(source)
                    allocation[source.model_id] = alloc_node
                    allocation_rev[alloc_node].add(source.model_id)
                    node_load[alloc_node] += total_activities[source.model_id]
                if destination in to_alloc:
                    to_alloc.remove(destination)
                    allocation[destination.model_id] = alloc_node
                    allocation_rev[alloc_node].add(destination.model_id)
                    node_load[alloc_node] += total_activities[destination.model_id]
            alloc_node += 1

        # All unassigned nodes are for the spill node
        # Undo our spilling node
        while to_alloc:
            changes = False
            n = list(to_alloc)
            for model in n:
                options = set()
                for oport in model.OPorts:
                    for oline, _ in oport.routing_outline:
                        location = oline.host_DEVS.location
                        if oline.host_DEVS.location is not None:
                            options.add((node_load[location], location))
                for iport in model.IPorts:
                    for iline in oport.routing_inline:
                        location = iline.host_DEVS.location
                        if iline.host_DEVS.location is not None:
                            options.add((node_load[location], location))
                if not options:
                    continue
                # Get the best option
                _, loc = min(options)
                node_load[loc] += total_activities[model.model_id]
                allocation[model.model_id] = loc
                allocation_rev[loc].add(model.model_id)
                to_alloc.remove(model)
            if not changes:
                # An iteration without changes, means that we loop forever
                for m in to_alloc:
                    # Force an allocation to 0
                    allocation[m.model_id] = 0
                    # allocation_rev doesn't need to be updated
                break
        return allocation

    def getTerminationTime(self):
        """
        Returns the time it takes for the allocator to make an 'educated guess' of the advised allocation.
        This time will not be used exactly, but as soon as the GVT passes over it. While this is not exactly 
        necessary, it avoids the overhead of putting such a test in frequently used code.

        :returns: float -- the time at which to perform the allocations (and save them)
        """
        return 10.0
