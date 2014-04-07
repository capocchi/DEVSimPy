Writing a custom scheduler
==========================

.. warning:: Writing a custom scheduler is potentially dangerous, as you could easily violate the DEVS formalism. Only trust your own schedulers after rigorous testing **and** (if you violate DEVS formalisms in the general case) make sure that such violating situations never happen.

A scheduler requires a simple interface, which will be explained here. If you require the scheduler to work distributed, you should allow for some kind of rollback to happen. This should be handled by the *massReschedule* method automatically.

Interface
---------

The interface, and thus the methods that need to be implemented, is rather small. Some of them might be skipped if you only want your scheduler to work for static structure without relocation. However, it is advised to implement all of them for future compliance.

.. function:: __init__(models, epsilon, totalModels)

   The constructor to be used for the scheduler. The argument *models* will contain a list of all models that are local to this scheduler. Argument *epsilon* contains the allowed floating point deviation when searching for imminent children. The *totalModels* argument can be ignored most of the time and is only useful if the scheduler needs some global information about all models, even those running remotely.

.. function:: schedule(model)

   Add a new model to the scheduler. The provided model will **not** have been passed in the constructor. It is only used in dynamic structure (when creating a new model) and distributed simulation with relocation (where a model is relocated to our node).

.. function:: unschedule(model)

   Remove a model from the scheduler. The provided model will have been either passed in the constructor or by the *schedule* method. Unscheduling a model should have the effect that it will never be returned by the *getImminent* method unless it is scheduled again.

.. function:: massReschedule(reschedule_set)

   Reschedules all models in the reschedule_set. This method is used to notify the scheduler that there is the possibility that the *timeNext* value of these models has been changed. Models that are not mentioned in the reschedule_set are guaranteed to have the same *timeNext* value. All models that are provided are guaranteed to either be passed in the constructor, or have the schedule method called for them. Performance wise, this is one of the most time-critical pieces of code.

.. function:: readFirst()

   Returns the time of the first model that is scheduled, as a tuple of the form (simulationtime, age). Since this is a read operation, nothing should change to the scheduled models and their order.

.. function:: getImminent(time)

   Return an iterable containing all models that are scheduled for this specific time, with an allowed deviation of *epsilon* (passed in the constructor). It is possible that there will be no imminent models! The internal state of the returned models is irrelevant, as they will afterwards have the *massReschedule* method called with (among others) them in the iterable.

   .. note:: The time should agree in both parts of the tuple: the simulation time (up to an *epsilon*) and the age field (*exact* equality only)

Example: sorted list scheduler
------------------------------

As an example, the sorted list scheduler is shown below. It simply contains an internal list of all models it has to take into account, sorts the list based on timeNext and returns the first elements that match.

.. code-block:: python

    class SchedulerSL(object):
        def __init__(self, models, epsilon, totalModels):
            self.models = list(models)
            self.epsilon = epsilon

        def schedule(self, model):
            self.models.append(model)
            self.models.sort(key=lambda i: i.timeNext)

        def unschedule(self, model):
            self.models.remove(model)

        def massReschedule(self, reschedule_set):
            self.models.sort(key=lambda i: i.timeNext)

        def readFirst(self):
            return self.models[0].timeNext

        def getImminent(self, time):
            immChildren = []
            t, age = time
            try:
                # Age must be exactly the same
                count = 0
                while (abs(self.models[count].timeNext[0] - t) < self.epsilon) and (self.models[count].timeNext[1] == age):
                    # Don't pop, as we want to keep all models in the list
                    immChildren.append(self.models[count])
                    count += 1
            except IndexError:
                pass
            return immChildren

Using your own scheduler
------------------------

Since the name of your custom scheduler is not known by me, there is no simple utility function like *setSchedulerSortedList()* provided, but you will have to use the more advanced interface. Note that all of these *setSchedulerX()* methods are simply utility functions which make exactly the same calls as you will be making. They are only provided to make the life of most users simpler.

Setting the custom scheduler requires 2 bits of information: the filename in which the class is defined and the name of the class. Take for example that we created the '*CustomScheduler*' class in the file '*myFirstScheduler*'. Using the scheduler is then as simple as::

    sim = Simulator(Queue())
    # Internally, this is evaluated as an import statement of the form
    #   from myFirstScheduler import CustomScheduler
    sim.setSchedulerCustom('myFirstScheduler', 'CustomScheduler')
    sim.simulate()
