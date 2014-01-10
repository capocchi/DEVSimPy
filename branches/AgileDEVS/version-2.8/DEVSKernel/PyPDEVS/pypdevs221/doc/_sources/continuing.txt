Continuing a stopped simulation
===============================

It is possible to continue a terminated simulation from the current state. An example use case of this is splitting the simulation in two 'phases'. The first phase is a kind of warmup period, in which tracing might not be necessary. If this phase only takes until a certain time, the termination time can be set to this time. As soon as the *simulate()* call returns, it is possible to perform some alterations to the model and to the simulation methods.

The syntax is as simple as recalling the *simulate()* method. Of course, if the termination time (or condition) is not altered, simulation will halt immediately. If this is changed, simulation will run until this condition is satisfied. All tracers from the original run will still be in effect and possible new tracers will be added. These new tracers wil only contain the data from the simulation run that happens after they are created. 

A small example, in which a model is contructed and runs until simulation time 100 is reached. After this, a tracer is set and simulation will runn up until simulation time 200::

    sim = Simulator(MyModel())
    sim.setTerminationTime(100)
    sim.simulate() # First simulation run; no tracers

    # We are at simulation time 100 now
    sim.setTerminationTime(200)
    sim.setVerbose() # Now add a tracer at time 100
    sim.simulate() # Simulate it for a second time; using the tracer

Altering the state
------------------

It is also possible to alter the state in between two calls to the simulate method. This allows you to e.g. enable internal logging only after a certain time, or clear all gathered statistics for the warm-up period. This uses the exact same syntax (and internally, it uses exactly the same methods) as the reinitialisation with the exception that no *reinit()* is called.

The available methods are:
* *setModelState(model, newState)*: modify the state of *model* and set it to *newState*. Use this to set a completely new state for the model. This is an optimized version of *setModelAttribute*.
* *setModelStateAttr(model, attr, value)*: modify the attribute *attr* of the state of *model* and set it to *value*. This will keep the original initialisation state, but alters only a single attribute.
* *setModelAttribute(model, attr, value)*: modify the attribute *attr* of the *model* and set it to *value*. This can be done to modify read-only attributes of the simulation model.

Such alterations will be visible in the *Verbose* logger as 'user events', signifying the attribute that was altered and to which value. This is done to prevent inconsistent trace files.

.. warning:: The time advance is **not** recalculated after a change to the state. This is because if no significant change happens and the timeAdvance returns the same value (as it should), it would signify a different absolute time due to the time advance function returning a relative file.
