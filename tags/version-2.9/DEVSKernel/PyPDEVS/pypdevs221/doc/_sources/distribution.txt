Distribution
============

For the modeller, distribution of models is as simple as providing a model (either atomic or coupled) with the location where it should run and afterwards running it as a distributed simulation (as mentioned in :doc:`howto`).

.. note:: Since version 2.1, model distribution was simplified and a lot of restrictions on the model were dropped. Every model that was valid in local simulation, should now also be valid in distributed simulation.

Distributing the queue
----------------------

Let's extend the *CQueue* example from previous sections and add some distribution to it. Of course, this model only has two atomic models, which is clearly not an ideal model to distribute. Therefore, we will add some *Queue* atomic models in parallel, all taking the output from the single generator. Our model should look something like:

.. image:: distribution_local_model.png
   :alt: The model to distribute

We will start of with implementing this model locally. This implementation is simple and shouldn't be more difficult than the model in :doc:`examples`. It should look something like::

    class DQueue(CoupledDEVS):
        def __init__(self):
            CoupledDEVS.__init__(self, "DQueue")
            self.generator = self.addSubModel(Generator())
            self.queue1 = self.addSubModel(Queue())
            self.queue2 = self.addSubModel(Queue())
            self.connectPorts(self.generator.outport, self.queue1.inport)
            self.connectPorts(self.generator.outport, self.queue2.inport)

.. note:: Our original *Queue* atomic model was not written with multiple instances in mind. Therefore, the model name will **not** be unique in this simulation. In later versions of PyPDEVS, this doesn't pose a problem apart from possibly confusing trace output.

Now all that is left is performing the actual distribution. Suppose we run 3 different nodes, with every atomic model on a seperate node. Thus the *Generator* runs on node 0, the first *Queue* runs on node 1 and the final *Queue* runs on node 2. This is as simple as altering the *addSubModel* method calls and add the desired node of the model being added. This results in::

    class DQueue(CoupledDEVS):
        def __init__(self):
            CoupledDEVS.__init__(self, "DQueue")
            self.generator = self.addSubModel(Generator(), 0)
            self.queue1 = self.addSubModel(Queue(), 1)
            self.queue2 = self.addSubModel(Queue(), 2)
            self.connectPorts(self.generator.outport, self.queue1.inport)
            self.connectPorts(self.generator.outport, self.queue2.inport)

Setting the location of a model, will automatically set the location of all its submodels with an unspecified location to the same location.

.. note:: Models for location 0 do not necessarily need to be specified, as the default is node 0. Leaving this option open (or specifying the location as *None*) means that it should take the location of the parent.

Additional options
------------------

A *Simulator* object that is initialized with a distributed model has several extra options that can be configured. 

More advanced options are elaborated further on in their own :doc:`advanced` subsection.

+------------------------------------+-------------------------------------------------------+
|*setTerminationModel(model)*        | Marks *model* as being used in termination condition  |
+------------------------------------+-------------------------------------------------------+
|*registerState(variable, model)*    | Register a state to be fetched after simulation       |
+------------------------------------+-------------------------------------------------------+
|*setFetchAllAfterSimulation(fetch)* | Completely update the model after simulation          |
+------------------------------------+-------------------------------------------------------+
|*setGVTInterval(gvt_int)*           | Calculate the GVT after every *gvt_int* seconds       |
+------------------------------------+-------------------------------------------------------+
|*setCheckpointing(name, chk_int)*   | Create a checkpoint after every *chk_int* GVT creation|
+------------------------------------+-------------------------------------------------------+
|*setStateSaving(state_saving)*      | Change the method for state saving to *state_saving*  |
+------------------------------------+-------------------------------------------------------+

.. note:: If any of these options are set during a local simulation, they will either throw a Exception or will simply have no effect.

Automatic allocation
--------------------

Some models are very simple, but tedious, to distribute. As long as the actual allocation has no real importance, there is an additional option *setAutoAllocation(autoAllocate)* which will have the simulator distribute the models automatically. This distribution is rather efficient, though it is often suboptimal. It will simply try to balance the amount of atomic models at every node, not taking into account the actual activity of these models. Furthermore, it only works at the root level.

Even though it doesn't perform intelligent distribution, it will work in situations where root models can work in parallel without influencing each other. More information can be found in :doc:`Static Allocators <staticallocator>`

General tips
------------

The distributed simulation algorithm that is being used is Time Warp. This means that every node will simulate *optimistically* in the assumption that other models have progressed as far as itself. As soon as a message from the past arrives, simulation at that node will be rolled back. This implies that nodes should have an equal load and that as few as messages should be exchanged between different nodes.

Therefore, the following rules should be taken into account to maximize the performance in distributed simulation:

* Models that exchange lots of messages should be on the same node
* Balance the load between nodes, so that the deviation is minimal
* Use homogeneous nodes
* Use quantums where possible, thus reducing the amount of messages

.. note:: Due to time warp's property of saving (nearly) everything, it is possible to quickly run out of memory. It is therefore adviced to set the GVT calculation time to a reasonable number. Running the GVT algorithm frequently yields slightly worse performance, though it will clean up a lot of memory.
