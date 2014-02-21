Reinitialisation
================

Starting from PyPDEVS 2.1.4, it is possible to run the *simulate()* method multiple times. If the *reinit()* method was called, the model will be restored to its initial state. This is done by completely saving the model in memory right before the actual simulation starts. Main problem with this approach is that it will require additional memory and for local simulation, it also increases the initialisation time as the copy will have to be made.

For these reasons, local simulation will have reinitialisation disabled by default and calling the *reinit()* method will result in a *DEVSException* stating this fact (and how to resolve it). Distributed simulation does not have this additional overhead and therefore it is always enabled.

So for remote simulation, it is as simple as::

    sim = Simulator(DQueue())
    sim.simulate() # Run it for the first time
    sim.reinit()   # Reinitialize 
    sim.simulate() # 'Continue' the simulation run (which was reset)

In local simulation, the option to allow reinitialisation needs to be set first, which simply gives::

    sim = Simulator(CQueue())
    sim.setAllowLocalReinit(True)
    sim.simulate() # Run it for the first time
    sim.reinit()   # Reinitialize
    sim.simulate() # 'Continue' the simulation run (which was reset)

Altering the model
------------------

Of course, simply rerunning the simulation is not really useful. Most of the time, reinitialisation is done to try the exact same simulation, but with a slightly different configuration. As long as the model structure is not altered, simply reinitializing is the best option. Note that these alterations should happen **before** the reinitialize call is made, as it implies network communication that is best done in a batch.

After a simulation run, the model will naturally still be in the post-simulation state and the model states will be the ones at the end of the simulation. Altering them has no effect on subsequent simulation runs, as the model will be reinitialised in a single step. Simply altering the model after a simulation run is not a viable option.

For these reasons, the only way to alter a model after simulation is through three methods of the *Simulator* object. These methods all serve a similar goal, though they are optimized for specific goals. They are:

* *setModelState(model, newState)*: modify the state of *model* and set it to *newState*. Use this to set a completely new state for the model. This is an optimized version of *setModelAttribute*.
* *setModelStateAttr(model, attr, value)*: modify the attribute *attr* of the state of *model* and set it to *value*. This will keep the original initialisation state, but alters only a single attribute. 
* *setModelAttribute(model, attr, value)*: modify the attribute *attr* of the *model* and set it to *value*. This can be done to modify read-only attributes of the simulation model.

For example, if you want to change the *processing_time* attribute of the queue, you can simply::
    
    model = CQueue()
    sim = Simulator(model)
    sim.setAllowLocalReinit(True)
    sim.simulate() # <-- Initial run with processing_time = 1.0
    sim.reinit()   # <-- Perform reinitialisation and perform all changes
    sim.setModelAttribute(model.queue, "processing_time", 2.0) # <-- Set it to 2.0
    sim.simulate() # <-- Now run with processing_time = 2.0

.. warning:: Altering the state should happen after reinitialisation, as otherwise your changes will be reverted too.
