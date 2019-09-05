"""
Middleware detection and setup code
"""

import sys

def startupMiddleware():
    """
    Do the actual detection and startup, also defines all necessary globals

    :returns: tuple -- current server rank and total world size
    """
    if "MPI" in globals():
        # Force local simulation
        return 0, 1
    # Try loading MPI
    global COMM_WORLD
    global MPI

    try:
        from mpi4py import MPI
        COMM_WORLD = MPI.COMM_WORLD
    except ImportError:
        # No MPI4Py found, so force local MPI simulation
        from .MPIRedirect import MPIFaker
        COMM_WORLD = MPIFaker()

    # Now we should take care of the starting of the server
    rank = COMM_WORLD.Get_rank()
    if rank != 0:
        # We should stop immediately, to prevent multiple constructions of the model
        # This is a 'good' stop, so return with a zero
        from .server import Server
        server = Server(int(rank), COMM_WORLD.Get_size())
        sys.exit(0)
    else:
        # We should still shutdown every simulation kernel at exit by having the controller send these messages
        # Use the atexit code at the end
        if COMM_WORLD.Get_size() > 1:
            import atexit
            atexit.register(cleanupMPI)
        return 0, COMM_WORLD.Get_size()

def cleanupMPI():
    """
    Shut down the MPI backend by sending a termination message to all listening nodes
    """
    for i in range(COMM_WORLD.Get_size()):
        if i == COMM_WORLD.Get_rank():
            req = COMM_WORLD.isend(0, dest=i, tag=0)
        else:
            COMM_WORLD.send(0, dest=i, tag=0)
    if COMM_WORLD.Get_size() > 1:
        MPI.Request.wait(req)
