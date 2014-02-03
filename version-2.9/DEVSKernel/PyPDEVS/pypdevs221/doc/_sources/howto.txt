How to run PyPDEVS
==================

There are several ways to start up a PythonPDEVS simulation. The simplest of them all is simply by running the experiment file, as discussed in the :doc:`examples` section. For completeness, this method will also be mentioned as the first option.

Local simulation
----------------

The simplest method is simply by running the experiment file, which looks something like::

    model = MyModel()
    sim = Simulator(model)
    sim.simulate()

For a more elaborate approach, please see the :doc:`examples` section.

Distributed simulation with MPI
-------------------------------

Running the MPI version requires the *mpi4py* Python module.

Since version 2.1, running the MPI version was completely redesigned and severely simplified. PyPDEVS will now automatically detect the usage of MPI when the correct invocation is done.

.. code-block:: bash

   mpirun -np 3 python experiment.py

Depending on the MPI backend that is used, several additional options might be possible. Please consult the documentation of your MPI implementation for more information.

Distributed simulation with PyRO
--------------------------------

.. versionchanged:: 2.2.0
   PyRO support was dropped.

.. note:: This method is no longer advised or actively developed. Most special features are **only** supported on MPI due to limitations in PyRO. Furthermore, PyRO is dramatically slow in comparison to MPI.

Running the PyRO version requires the *PyRO4* Python module.

Starting a simulation in PyRO is almost as simple as starting it as if it was a local simulation. The only difference is that we require both a nameserver and (possibly multiple) simulation node(s).

A basic version of the nameserver can be started running:

.. code-block:: bash

   python -m Pyro4.naming

As soon as this nameserver is started up, each simulation node still needs to be set up. This can be done by running the :doc:`server` file with the name of the server as a parameter. For example:

.. code-block:: bash

   user@node-1$ python server.py 1
   user@node-2$ python server.py 2
   user@node-3$ python server.py 3

The name of the server should be incremental numbers, starting from 1. The server with name 0 is reserved for the controller, as is the common naming in MPI.

.. warning:: PyRO simulation is possibly started from several different folders, which might cause import problems. PyRO transfers models as pickles, so the user should make sure that the **exact** same file structure is visible for the referenced files.
