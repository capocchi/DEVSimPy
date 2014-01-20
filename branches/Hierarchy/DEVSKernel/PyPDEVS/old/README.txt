PyPDEVS: a Parallel DEVS simulator in Python
-------

1) Using PyRO:

1.a) Requirements:
- PyRO 4.11, other versions should be supported, though performance drops
  severely in higher versions and nested simulation seems buggy due to the way
  PyRO handles the threadpool

1.b) Running:
It is necessary to start the necessary servers before starting the simulation.
This can be done by executing the server.py file, followed by the tag of this
simulation kernel. This tag can be anything, though it is suggested to use
numbers starting from 1, since 0 is reserved for the controller.
Example: "python server.py 1" will start a simulation kernel with tag 1. Note
that it is required to have a PyRO nameserver running ("python -m
Pyro4.naming").
More information about this can be found on the PyRO wiki.

1.c) Limitations:
- Due to the way PyRO objects are implemented, checkpointing is not supported.

2) Using MPI:

2.a) Requirements:
- MPI4Py
- A working MPI implementation, the simulator was developed using MPICH2 and
  sporadically tested using OpenMPI. This MPI implementation should support
  MPI_MULTIPLE (allow for multiple MPI threads).

2.b) Running:
To profit from MPI simulation, it is necessary to start the experiment using
the 'mpirun' command (supplied with the MPI implementation). This should call
the file mpirunner.py, which will call the necessary commands.
Example: "mpirun -np 3 python mpirunner.py experiment" will start 3 MPI
processes and import the file 'experiment.py' in which the function 'sim' will
be called.

2.c) Checkpointing:
Saving checkpoints require the user to specify a non-negative checkpoint
interval in the call to the 'simulate' function. This will cause '.pdc'
(PyDEVS Checkpoint) files to be generated.
Restoring from these checkpoints requires a call to the 'mpirunner.py' file
with the --restore flag.
Example: "mpirun -np 3 python mpirunner.py --restore 10.2" will restore a
simulation to GVT 10.2. This requires the files 'checkpoint_10.2_1.pdc',
'checkpoint_10.2_2.pdc', 'checkpoint_10.2_3.pcd' and 'checkpoint_SIM.pdc' to
be present. Simulation will then be continued starting from this GVT.

3) Using neither:
Currently, the only supported way to run non-distributed simulation is to
either start PyRO (only the nameserver and the simulation itself), or MPI with
only a single core.

4) Running tests:
All tests are simply called by running the file 'tests.py'. Note that for the
PyRO tests it is required that no nameserver is currently running (or still
bound to a port) to prevent conflicting nameservers.
