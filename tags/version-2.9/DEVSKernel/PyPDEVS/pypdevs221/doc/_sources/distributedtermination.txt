Distributed Termination
=======================

Termination was simple in local, sequential simulation. All that had to be done was placing a simple check before each step in the simulation and check whether or not this simulation step should still be executed.

Distributed simulation on the other hand, should only terminate as soon as all nodes are able to quit. But due to the use of time warp, even if a node has stopped running, it might have to start again some time later. Clearly a global termination time is still relatively simple to use, as all nodes just compare their clocks to it, but a termination condition is a lot more difficult.

In this section, the two different ways of termination in a distributed setting will be discussed.

Termination time
----------------

A global termination time is clearly the most efficient solution. All nodes will receive this time at startup and will simply compare to it. It requires no inter-node communication whatsoever because every node can determine for itself whether or not simulation is finished. If at all possible, this approach is highly recommended over the other option.

Due to its simplicity, the exact same methods and semantics can be used as in sequential simulation::
    
    sim = Simulator(Model())
    sim.setTerminationTime(50.0)
    sim.simulate()

Termination condition: frequent state checks
--------------------------------------------

.. warning:: Due to the use of time warp, the *time* parameter of the function now returns a **tuple** instead of a **float**. Most often, only the first value of the tuple is used, which contains the actual simulation time. The second value is the so called *age* field, which indicates how often this exact same simulation time has already happened.

A termination condition is still possible in distributed simulation, albeit in a reduced form. First of all, the granularity of a termination condition is not guaranteed in distributed simulation. Since DEVS takes non-fixed timesteps, they are depending on the models that are present on the current node. This means that the termination condition will also be checked only at these steps. Generally, this should not be a big problem, though it is something to keep in mind.

Only a single node can be responsible for the termination condition, due to the model being completely distributed. This node is always the controller. The controller should thus have all models involved in the termination condition running, as otherwise invalid states will be read.

.. note:: PyPDEVS will **not** complain when reading an invalid state, as such readings are done behind the back of PyPDEVS. If you want certainty that the state you are accessing is local, check whether or not the *location* attribute is equal to zero.

To be able to cope with allocation and relocation, the simulator should have its *setTerminationModel(model)* method be called. This will mark the model as being used in the termination condition and will guarantee that this model stays on the controller, whatever allocation or relocation is given. Note though, that this could potentially move a single atomic model from a remote coupled model, causing many revertions.

As soon as the termination condition triggers the end of the simulation, the controller will send a termination message to all other nodes, which will then keep running until they have reached the same time as passed in the termination condition. Should the controller be reverted, its termination messages will also be cancelled.

If we want the generator atomic model of the queue to be used in the termination condition, we could write::

    def generatedEnough(time, model):
        return model.generator.state.generated > 5

    myQueue = CQueue()
    sim = Simulator(myQueue)
    sim.setTerminationCondition(generatedEnough)
    sim.setTerminationModel(myQueue.generator)
    sim.simulate()

Termination condition: sporadic state checks
--------------------------------------------

.. warning:: The complete *time* tuple should be passed to the *getState(time)* method!

If the model state is only required sporadically, it would be wasteful to run the model at the controller, simply for this one access. To cope with this, a *pull based* method is possible. Every atomic DEVS model will have a *getState(time)* method. If the model is non-local, this method can be called to retrieve the state of the model at that specific time. If this approach is used, the model need not be marked as a termination model.

.. note:: This time attribute is necessary due to time warp being used: it is very unlikely that the remote model is at exactly the same time in simulated time, so the time at which this call was made should be passed.

Such *getState(time)* calls are blocking, meaning that they will not return a result if the remote model is not yet at the simulated time that was requested. Furthermore, such requests cause artificial dependencies between different models. This pull based approach is thus only recommended if it is done (very) sporadically. It goes without saying that these remote calls also incur a latency due to the network delay.

To write the same as the previous example, we can write::

    def generatedEnough(time, model):
        return model.generator.getState(time).generated > 5

    myQueue = CQueue()
    sim = Simulator(myQueue)
    sim.setTerminationCondition(generatedEnough)
    sim.simulate()

Termination condition: mixed state checks
-----------------------------------------

Both approaches could be mixed if it is required, for example if the generator is checked at every iteration (and is running local). If the generator passed a certain check, then other remote models need to be checked, which will only be done very sporadically. This could give::

    def generatedEnough(time, model):
        # First a local check
        if model.generator.state.generated <= 5:
            return False
        else:
            # Now a remote check, but we know that this will only be called rarely
            return model.processor2.getState(time).processed > 5

    myQueue = CQueue()
    sim = Simulator(myQueue)
    sim.setTerminationCondition(generatedEnough)
    # Only mark the generator as a termination model
    sim.setTerminationModel(myQueue.generator)
    sim.simulate()
    
