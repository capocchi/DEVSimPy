"""
Base class for a relocator that supports boundary construction and maintenance
"""

class BoundaryRelocator(object):
    """
    Main class
    """
    def __init__(self):
        """
        Constructor
        """
        pass

    def setController(self, controller):
        """
        Set the controller of this relocator
        
        :param controller: the controller object which can be used to fetch all required information about the model
        """
        self.server = controller.server
        self.model_ids = controller.model_ids

        # All location queries should happen on this CACHE
        # This is NOT a live version of the locations and is only a temporary 
        # version for testing some possible relocations. 
        # However, this version SHOULD be stable, that is: it is never updated again
        self.locations = [model.location for model in self.model_ids]

        # Create all boundaries for all nodes
        self.boundaries = [{} for _ in range(controller.kernels)]
        self.constructBoundaries(self.model_ids)

    def fetchModelActivity(self, model): 
        """
        Get the activity of a specific model.

        It will also cache the activity of all models at the same node to make subsequent calls much faster.

        :param model: the model to fetch the activity of, can be remote
        :returns: the activity of the model
        """
        try:
            # Try locally
            return self.model_activities[model.model_id]
        except KeyError:
            # 'Cache miss'
            self.model_activities.update(self.server.getProxy(model.location).getCompleteActivity())
            return self.model_activities[model.model_id]

    def constructBoundaries(self, models):
        """
        Construct the boundaries for the specified models

        :param models: the models to be added to the boundary
        """
        for model in models:
            location = self.locations[model.model_id]
            for iport in model.IPorts:
                for port in iport.inLine:
                    if self.locations[port.hostDEVS.model_id] != location:
                        self.boundaries[location].setdefault(
                                self.locations[port.hostDEVS.model_id], set()).add(model)
            for oport in model.OPorts:
                for port, _ in oport.routingOutLine:
                    if self.locations[port.hostDEVS.model_id] != location:
                        self.boundaries[location].setdefault(
                                self.locations[port.hostDEVS.model_id], set()).add(model)

    def removeBoundaries(self, models):
        """
        Remove the boundaries provided by the specified models

        :param models: the models to be removed from the boundaries list
        """
        for model in models:
            location = self.locations[model.model_id]
            boundaries = self.boundaries[location]

            # Only here for efficiency
            ms = set([model])
            for dest in boundaries:
                boundaries[dest] -= ms

    def scheduleMove(self, model_id, destination):
        """
        Schedule the move of a model to another destination; this operation is reversible

        :param model_id: the model_id of the model to move
        :param destination: the destination of the model
        """
        self.relocate[model_id] = destination
        model = self.model_ids[model_id]
        source = self.locations[model_id]

        update = set([model])
        self.removeBoundaries(update)
        for iport in model.IPorts:
            for port in iport.inLine:
                update.add(port.hostDEVS)
        for oport in model.OPorts:
            for port, _ in oport.routingOutLine:
                update.add(port.hostDEVS)
        # Now update contains all the models that should be updated
        # Perform the update 'in cache'
        self.locations[model_id] = destination

        self.removeBoundaries(update)
        self.constructBoundaries(update)

        activity = self.fetchModelActivity(model)
        self.node_activities[source] -= activity
        self.node_activities[destination] += activity

    def getRelocations(self, GVT, activities, horizon):
        """
        Return all pending relocations

        :param GVT: current GVT
        :param activities: activities being passed on the GVT ring
        :param horizon: the activity horizon
        :returns: all relocations that should be executed
        """
        # This is only a base 'abstract' class
        raise NotImplementedError()

    def useLastStateOnly(self):
        """
        Determines whether or not the activities of all steps should be accumulated, or only a single state should be used.

        :returns: boolean -- True if the relocator works with a single state
        """
        raise NotImplementedError()
