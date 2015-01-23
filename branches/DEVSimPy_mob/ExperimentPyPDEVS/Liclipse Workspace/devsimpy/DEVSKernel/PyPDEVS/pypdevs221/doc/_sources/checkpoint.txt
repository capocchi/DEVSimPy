Checkpointing
=============

.. note:: Checkpointing is only possible in distributed simulation and only if the MPI backend is used.

Checkpointing offers the user the possibility to resume a computation from a previous simulation run. This previous simulation run might have been interrupted, with only a partial simulation as a result. Furthermore, all possible tracers will only have parts of their actual output being written. Restarting the simulation from scratch might be unacceptable due to the long time that was already spent on simulation. Checkpointing offers a solution to this problem, because it will save the current simulation state to a file after a fixed amount of GVT computations.

The checkpointing algorithm is closely linked to the GVT algorithm, as this allows for several optimisations. At the GVT, it is possible to know that no message will arrive from before, so all states from before can be removed. Since after a checkpoint recovery all nodes will revert to the GVT, no future state needs to be saved too.

The only data that is thus stored is the model itself. To allow for somewhat easier implementation, some other data is also stored, such as configuration options. Basically it boils down to a selective *pickle* of the kernels at every location.

Now how do you actually use checkpointing? The first step is of course to enable it in the configuration options, like this::

    sim = Simulator(DQueue())
    sim.setCheckpointing("myQueue", 1)
    sim.simulate()

The *setCheckpointing* function takes a name as its first parameter, which is simply used to identify the checkpoints and it will be used as a filename. The second parameter is the amount of GVT computations that should pass before a checkpoint is made. It might be possible to calculate the GVT frequently (e.g. after 10 seconds of simulation), but only create a checkpoint after a few minutes of simulation. This is because the GVT calculation frees up memory and might therefore be necessary. On the other hand, creating checkpoints very often is I/O intensive and when restoring a checkpoint, it will probably not be a matter of seconds.

.. warning:: The first parameter of the *setCheckpointing* function is used as a filename, so make sure that this would create a valid file name.

When simulation is running with these options, files will be created at every checkpoint step that are placed in the current directory. The created files will have the PDC extension, which stands for PythonDEVS Checkpoint. There will be as many files as there are nodes running: one for each kernel. Furthermore, a basic file will be created at the start, which contains the simulator that oversees the simulation. This file doesn't change with simulation, so it is not altered during simulation itself.

Now that we have our checkpoints, we only need to be able to recover from them. This is again as simple as running the *loadCheckpoint* function **before** recreating a simulator and model. It is not completely necessary to do this before, though the work would be useless... This *loadCheckpoint* call will automatically resume simulation as soon as all nodes are recovered. The call will return *None* in case no recovery is possible (e.g. when there are no checkpoint files), or will return a simulator object when simulation has finished. It is therefore **only** necessary to create a new model and simulator if this fails. This gives the following code::

    sim = loadCheckpoint("myQueue")
    if sim is None:
        sim = Simulator(DQueue())
        sim.setCheckpointing("myQueue", 1)
        sim.simulate()
    # Here, the simulation is finished and the Simulator object can be used as normally in both cases

The *loadCheckpoint* will automatically search for the latest available checkpoint that is completely valid. If certain files are missing, then the next available option will be tried until a usable one is found. Note that it is possible for a checkpoint file to be corrupt, for example when the simulation crashes while writing the checkpoint file. This will be seen by the user as a seemingly random *PicklingError*. In this case it is necessary to remove at least one of these files and retry. For this reason, older checkpoints are still kept.

.. note:: On-the-fly recovery of a crashed node is not possible, all nodes will have to stop and restart the simulation anew.
