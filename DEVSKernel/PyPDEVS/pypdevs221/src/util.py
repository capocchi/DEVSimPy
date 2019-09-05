# -*- coding: Latin-1 -*-
"""
Common utility functions used in PyPDEVS
"""
from . import middleware
from .MPIRedirect import MPIRedirect
from collections import defaultdict

EPSILON = 1E-6

try:
    import pickle as pickle
except ImportError:
    import pickle

def broadcastModel(data, proxies, allowReinit, schedulerLocations):
    """
    Broadcast the model to simulate to the provided proxies

    :param data: data to be broadcasted to everywhere
    :param proxies: iterable containing all proxies
    :param allowReinit: should reinitialisation be allowed
    """
    if (len(proxies) == 1) and not allowReinit:
        # Shortcut for local simulation with the garantee that no reinits will happen
        proxies[0].sendModel(data, schedulerLocations[0])
        return
    # Otherwise, we always have to pickle
    pickled_data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
    if len(proxies) == 1:
        proxies[0].saveAndProcessModel(pickled_data, schedulerLocations[0])
    else:
        for i, proxy in enumerate(proxies[1:]):
            # Prepare by setting up the broadcast receiving
            proxy.prepare(schedulerLocations[i])
        # Pickle the data ourselves, to avoid an MPI error when this goes wrong (as we can likely back-up from this error)
        # Broadcast the model to everywhere
        middleware.COMM_WORLD.bcast(pickled_data, root=0)
        # Immediately wait for a barrier, this will be OK as soon as all models have initted their model
        # Still send to ourselves, as we don't receive it from the broadcast
        # Local calls, so no real overhead
        proxies[0].sendModel(data, schedulerLocations[0])
        proxies[0].setPickledData(pickled_data)
        middleware.COMM_WORLD.barrier()

def broadcastCancel():
    """
    Cancel the broadcast receiving in a nice way, to prevent MPI errors
    """
    middleware.COMM_WORLD.bcast(None, root=0)

def toStr(inp):
    """
    Return a string representation of the input, enclosed with ' characters

    :param inp: the input value
    :returns: string -- input value, enclosed by ' characters
    """
    return "'%s'" % inp

def addDict(destination, source):
    """
    Adds 2 dicts together in the first dictionary

    :param destination: the destination dictionary to merge the source into
    :param source: the dictionary to merge in

    .. note:: the *destination* parameter will be modified and no return value is provided. The *source* parameter is not modified.
    """
    for i in source:
        destination[i] = destination.get(i, 0) + source[i]

def allZeroDict(source):
    """ 
    Checks whether or not a dictionary contains only 0 items

    :param source: a dictionary to test
    :returns: bool -- whether or not all entries in the dictionary are equal to zero
    """
    for i in list(source.values()):
        if i != 0:
            return False
    return True

def runTraceAtController(server, uid, model, args):
    """
    Run a trace command on our version that is running at the constroller

    :param server: the server to ask the proxy from
    :param uid: the UID of the tracer (identical throughout the simulation)
    :param model: the model that transitions
    :param args: the arguments for the trace function
    """
    toRun = easyCommand("self.tracers.getByID(%i).trace" % uid, args).replace("\n", "\\n")
    if server.getName() == 0:
        server.getProxy(0).delayedAction(model.timeLast, model.model_id, toRun)
    else:
        server.queueMessage(model.timeLast, model.model_id, toRun)

def easyCommand(function, args):
    """ 
    Easy wrapper to create a string representation of function calls

    :param function: the function should be called
    :param args: list of all the arguments for the function
    :returns: str -- string representation to be passed to *exec*
    """
    text = str(function) + "("
    for i in range(len(args)):
        if i != 0:
            text += ", "
        text += str(args[i])
    text += ")"
    return text

class DEVSException(Exception):
    """
    DEVS specific exceptions
    """
    def __init__(self, message="not specified in source"):
        """
        Constructor

        :param message: error message to print
        """
        Exception.__init__(self, message)

    def __str__(self):
        """
        String representation of the exception
        """
        return "DEVS Exception: " + str(self.message)

class QuickStopException(Exception):
    """
    An exception specifically to stop the simulation and perform a relocation ASAP
    """
    def __init__(self):
        Exception.__init__(self, "(none)")

    def __str__(self):
        """
        Should be unused
        """
        return "Quick Stop Exception"

def saveLocations(filename, modellocations, model_ids):
    """
    Save an allocation specified by the parameter.

    :param filename: filename to save the allocation to
    :param modellocations: allocation to save to file
    :param model_ids: all model_ids to model mappings
    """
    # Save the locations
    f = open(filename, 'w')
    for model_id in modellocations:
        # Format:
        #   model_id location fullname
        f.write("%s %s %s\n" % (model_id, modellocations[model_id], model_ids[model_id].getModelFullName()))
    f.close()

def constructGraph(models):
    """
    Construct a graph from the model, containing the weight (= number of messages) on a connection
    between two components.

    :param models: the root model to use for graph construction
    :returns: dict -- all from-to edges with their number of events
    """
    edges = defaultdict(lambda: defaultdict(int))
    for model in models.componentSet:
        for outport in model.OPorts:
            for inport in outport.routingOutLine:
                edges[outport.hostDEVS][inport.hostDEVS] += outport.msgcount
    return edges
