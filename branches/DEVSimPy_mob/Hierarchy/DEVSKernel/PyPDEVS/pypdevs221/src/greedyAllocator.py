from collections import defaultdict

class GreedyAllocator(object):
    """
    Allocate all models in a greedy manner: make the most heavy link local and extend from there on until an average load is reached.
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
        # Run over all edges to create the nodes and link in their edges
        nodes = {}
        remainingEdges = set()
        toAlloc = set()
        for source in edges:
            for destination in edges[source]:
                # A connection from 'source' to 'destination'
                nodes.setdefault(source, []).append((edges[source][destination], destination))
                nodes.setdefault(destination, []).append((edges[source][destination], source))
                remainingEdges.add((edges[source][destination], source, destination))
                toAlloc.add(destination)
            toAlloc.add(source)
        # OK, nodes are constructed

        # Allocate 1 node too much for spilling
        nrnodes += 1

        # Find average activity (our target)
        averageActivity = sum([totalActivities[i] for i in totalActivities])/nrnodes

        # Get the strongest edge
        allocNode = 0
        nodeLoad = []
        allocation = {}
        allocation_rev = defaultdict(set)
        while allocNode < (nrnodes - 1):
            while remainingEdges:
                maxEdge = max(remainingEdges)
                remainingEdges.remove(maxEdge)
                edgeWeight, source, destination = maxEdge
                if source in toAlloc and destination in toAlloc:
                    break
            else:
                break
            nodeLoad.append(totalActivities[source.model_id] + totalActivities[destination.model_id])
            allocation[source.model_id] = allocNode
            allocation[destination.model_id] = allocNode
            allocation_rev[allocNode].add(source)
            allocation_rev[allocNode].add(destination)
            toAlloc.remove(source)
            toAlloc.remove(destination)
            while nodeLoad[allocNode] < averageActivity:
                edgeSearch = [edge for edge in remainingEdges if (edge[1] in allocation_rev[allocNode] and edge[2] in toAlloc) or (edge[2] in allocation_rev[allocNode] and edge[1] in toAlloc)]
                if not edgeSearch:
                    break
                # Allocate some more nodes
                maxEdge = max(edgeSearch)
                remainingEdges.remove(maxEdge)
                edgeWeight, source, destination = maxEdge
                # Ok, this is an unbound connection, so add it
                if source in toAlloc:
                    toAlloc.remove(source)
                    allocation[source.model_id] = allocNode
                    allocation_rev[allocNode].add(source.model_id)
                    nodeLoad[allocNode] += totalActivities[source.model_id]
                if destination in toAlloc:
                    toAlloc.remove(destination)
                    allocation[destination.model_id] = allocNode
                    allocation_rev[allocNode].add(destination.model_id)
                    nodeLoad[allocNode] += totalActivities[destination.model_id]
            allocNode += 1

        # All unassigned nodes are for the spill node
        # Undo our spilling node
        while toAlloc:
            changes = False
            n = list(toAlloc)
            for model in n:
                options = set()
                for oport in model.OPorts:
                    for oline, _ in oport.routingOutLine:
                        if oline.hostDEVS.location is not None:
                            options.add((nodeLoad[oline.hostDEVS.location], oline.hostDEVS.location))
                for iport in model.IPorts:
                    for iline in oport.routingInLine:
                        if iline.hostDEVS.location is not None:
                            options.add((nodeLoad[iline.hostDEVS.location], iline.hostDEVS.location))
                if not options:
                    continue
                # Get the best option
                _, loc = min(options)
                nodeLoad[loc] += totalActivities[model.model_id]
                allocation[model.model_id] = loc
                allocation_rev[loc].add(model.model_id)
                toAlloc.remove(model)
            if not changes:
                # An iteration without changes, this means that we would loop forever
                for m in toAlloc:
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
