Static Allocator
================

Assigning locations directly within the model might be tedious or even impossible in some situations.
In some other cases, the number of nodes might be variable, thus requiring more code in the model itself to determine the correct location.
To solve these problems, an allocator can be defined.

This section will handle about the static allocators.
The static signifies that they use no run-time information, in contrast to the :doc:`Dynamic Allocators <dynamicallocator>` discussed later on.
Allocation will happen as soon as the model is direct connected.

As a result of allocation, a file *locationsave.txt* is created, which contains the allocation that was found.
In future runs, it is then possible to load from this file instead of doing the allocation process all over again.

Writing a custom allocator
--------------------------

Writing an allocator is rather simple. The class has a simple method called *allocate*,
which will return a dictionary with a model_id as its key and the node to place it on as the value.
For the allocators, it is required that all model_ids are assigned a location, as otherwise they will not appear in the saved allocation file.

The *allocate* has the following parameters:

#. *models*: an iterable containing all models to allocate
#. *edges*: **must** be ignored, as it is constantly *None*
#. *nrnodes*: the number of nodes to allocate over
#. *totalActivities*: **must** be ignored, as it is constantly *None*

Furthermore, a method *getTerminationTime* is also required, but it should always return 0 for a static allocator.

This gives the following template::

    class MyAllocator():
        def allocate(self, models, edges, nrnodes, totalActivities):
            # Do NOT use the edges and totalActivities arguments
            # To allocate model_ids 0, 1 and 2 to node 0 and model_id 3 to node 1
            return {0: 0, 1: 0, 2: 0, 3: 1}

        def getTerminationTime(self):
            return 0

Using the allocator
-------------------

Using the static allocator that is provided in the PyPDEVS distribution is as simple as calling::

    sim = Simulator(Model())
    sim.setAutoAllocation()
    sim.simulate()

Running a custom allocator uses the same methodology as a custom scheduler.
For the allocator with classname *MyAllocator*, in the file *myAllocator*, the configuration is as follows::

    sim = Simulator(Model())
    sim.setInitialAllocator("myAllocator", "MyAllocator")
    sim.simulate()
