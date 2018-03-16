Dynamic Allocator
=================

Dynamic allocators are almost the same as the static allocators, with the exception that they make their allocation at a GVT calculation step instead of at the beginning.

Before the dynamic allocator gets to run, the model will have already simulated for some time. Due to this simulation, which will have happened completely locally, the simulator will have already collected activity information.

Since the simulation ran locally and with the pure intention of finding a decent allocation, the simulator will gather a lot more statistics such as the amount of transferred messages over a connection.

In dynamic allocation mode, the model drawing functionality will also mention the load on the connections.

Writing a custom allocator
--------------------------

Writing a dynamic allocator is the same as writing a static allocator, with the exception that the 2 arguments which were always *None* will now be filled in.

The *edges* argument will contain a dictionary with another dictionary in it. The value in it will be a message counter. This means that the value returned by *edges[a][b]* will be the amount of messages between *a* and *b*.

The *totalActivities* argument will be a dictionary containing the accumulated activity of every model in the complete simulation.

Which of this information is used (and how) is of course up to you.

The *getTerminationTime()* method will now be used to indicate how long a *warm-up* period takes for the simulator. This will not be done perfectly, but up to the first GVT calculation that goes beyond this termination time. If this method returns *0*, it becomes a static allocator and will not be able to use the 2 parameters that are dependent on the simulation run.

Using the allocator
-------------------

Using a dynamic allocator is identical to using a static one, so please refer to the explanation in the :doc:`previous section <staticallocator>`
