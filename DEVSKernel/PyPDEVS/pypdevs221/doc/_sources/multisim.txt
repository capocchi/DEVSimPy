Multiple Simulators
===================

In some situations, having multiple models (and their respective simulator) in the same Python script is useful for comparing the performance. 

Local simulation
----------------

In local simulation, it is possible to create multiple Simulator instances without any problems::
    
    sim1 = Simulator(Model1())
    # Any configuration you want on sim1
    sim1.simulate()

    sim2 = Simulator(Model2())
    # Any configuration you want on sim2
    sim2.simulate()

Distributed simulation
----------------------

Starting up multiple Simulator classes is not supported in distributed simulation. This is because starting a simulator will also impose the construction of different MPI servers, resulting in an inconsistency.

It is supported in distributed simulation to use :doc:`reinitialisation <reinitialisation>`, simply because it is the same model and is coordinated by the same simulator.
