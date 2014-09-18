Activity Tracking
=================

Activity tracking will perform the most generic approach available: measuring the time every transition function takes, accumulating all these values and calculating the complete load of the node.

When using the *basic boundary relocator*, the current allocation will be mutated in such a way that every node gets approximately the same load. Sometimes this will not yield decent results, since the approach is too general and uses a greedy algorithm. It should therefore only be used in very simple situations where the number of possible mutations is rather limited. A simple example of this is a queue which has only one input and one output port.

The *basic boundary relocator* takes a single argument: the swappiness. This simply defines what threshold to use for 'unacceptable load distribution'. A swappiness of 2 for example, will only try to offload nodes that have an activity twice as big as the average activity. Setting a too low swappiness will cause many (often unnecessary) relocations, while setting a too high swappiness will prevent relocations completely.

To start a distributed simulation with *general activity tracking*, the configuration is::

    sim = Simulator(CQueue())
    swappiness = 1.3
    sim.setActivityRelocatorBasicBoundary(swappiness)
    sim.simulate()
