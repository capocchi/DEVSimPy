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
        from pypdevs.MPIRedirect import MPIFaker
        COMM_WORLD = MPIFaker()

    # Now we should take care of the starting of the server
    rank = COMM_WORLD.Get_rank()
    if rank != 0:
        # We should stop immediately, to prevent multiple constructions of the model
        # This is a 'good' stop, so return with a zero
        from pypdevs.server import Server
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
