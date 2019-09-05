# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# util.py --- Common utilities used in PyDEVS
#                     --------------------------------
#                            Copyright (c) 2013
#                             Hans  Vangheluwe
#                            Yentl Van Tendeloo
#                       McGill University (Montréal)
#                     --------------------------------
# Version 2.0                                        last modified: 18/02/13
#  - Split off some commonly used functions
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import sys
from . import middleware
from .MPIRedirect import MPIRedirect

EPSILON = 1E-6

try:
    import Pyro4
except ImportError:
    if middleware.USE_PYRO:
        print("Pyro used as a back-end, but Pyro not found")
        sys.exit(1)

try:
    from mpi4py import MPI
    COMM_WORLD = MPI.COMM_WORLD
except ImportError:
    from .MPIRedirect import MPIFaker
    COMM_WORLD = MPIFaker()

def getProxy(location):
    """ 
    Generates a (synchronous) proxy to the provided location
    Args:
        location - the location to which the proxy should point
    """
    if middleware.USE_MPI:
        return MPIRedirect(location)
    elif middleware.USE_PYRO:
        return Pyro4.Proxy("PYRONAME:" + str(location))

def makeOneway(proxy, funcname):
    """
    Make a specific proxy a one way function for a certain function
    Args:
        proxy - proxy to make one way
        funcname - string representation of the function that should be made one way
    """
    if middleware.USE_MPI:
        proxy.setOneWay(funcname)
    elif middleware.USE_PYRO:
        proxy._pyroOneway.add(str(funcname))

def toStr(inp):
    """
    Return a string representation of the input, enclosed with ' characters
    Args:
        inp - the input value
    """
    return "'" + str(inp) + "'"

def addDict(destination, source):
    """
    Adds 2 dicts together in the first dictionary
    Args:
        destination - the destination dictionary to merge the source into
        source - the dictionary to merge in
    """
    for i in list(source.keys()):
        destination[i] = destination.get(i, 0) + source[i]

def allZeroDict(source):
    """ 
    Checks whether or not a dictionary contains only 0 items
    Args:
        source - a dictionary to test
    Returns:
        boolean - whether or not all entries in the dictionary are zero
    """
    for i in list(source.items()):
        if i[1] != 0:
            return False
    return True

def execute(model, command, immediate=False):
    """ 
    Executes a command at the controller at the timeLast of the provided model
    Args:
        model - the model that executes the command
        command - the command to execute
        immediate - whether or not it should be executed immediatly
    """
    command = command.replace("\n", "\\n")
    proxy = getProxy(model.rootsim.controller_name)
    #NOTE could be done oneway, though this would be able to cause wrong 
    #     behaviour due to a message not being received and having the GVT 
    #     progressed.
    modelname = model.rootsim.model.getModelFullName()
    if immediate:
        proxy.action(command)
    else:
        proxy.delayedAction(model.timeLast, modelname, command)

def easyCommand(function, args):
    """ 
    Easy wrapper to create a string representation of function calls
    Args:
        function - the function that must be called
        args - list of all arguments
    """
    text = str(function) + "("
    for i in range(len(args)):
        if i != 0:
            text += ", "
        text += str(args[i])
    text += ")"
    return text

def updateBag(bigbag, smallbag):
    """ 
    Updates the bigbag with all values from smallbag. 
    Both bags should contain a LIST of values. 
    """
    if (bigbag == {}) and (smallbag is not None):
        return smallbag
    # Handle the case when the bag is actually None
    if smallbag is not None:
        for item in list(smallbag.items()):
            port, value = item
            # Either the content on the port, or the pickled representation of an empty list
            prev = bigbag.get(port, [])
            prev.extend(value)
            bigbag[port] = prev
    return bigbag

class DEVSException(Exception):
    """
    DEVS specific exceptions
    """
    def __init__(self, message="not specified in source"):
        """
        Constructor
        """
        Exception.__init__(self, message)

    def __str__(self):
        return "DEVS Exception: " + str(self.message)

class NestingException(Exception):
    """
    Exception for when nesting is not currently allowed
    """
    def __init__(self, message="not specified in source"):
        """
        Constructor
        """
        Exception.__init__(self, message)

    def __str__(self):
        return "Nesting Exception: " + str(self.message)
