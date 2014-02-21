Activity prediction
===================

One of the remaining problems with the previous two solutions is that they use a general relocator, instead of a custom one. A custom relocator has several advantages, of which the most important is addition of domain specific information. A relocator might not only know how to perform the best relocations (instead of simply mutating the border), but might also be able to predict how the activity will evolve in the future and already take some measures to speed up the future.

A custom relocator also allows us to have a radically different concept of activity than was previously possible. As a simple example, models might return their energy consumption as their activity and the relocator then tries to minimise this value by performing some (domain-specific) relocations.

An example of how to use a user-defined relocator (located in the file "relocatorFile", with classname "Relocator")::

    sim = Simulator(MyModel())
    # Note that additional parameters can be passed to the method
    #   these will then be passed to the constructor of the provided relocator
    sim.setActivityRelocatorCustom("relocatorFile", "Relocator")

Writing a relocator
-------------------

Writing a relocator yourself is somewhat more difficult, as it offers a lot of possibilities. There are 2 important methods to define: *getRelocations(GVT, activities, horizon)* and *useLastStateOnly()*.

The *useLastStateOnly()* is simple and should return a boolean. If the boolean is *False*, all activities within the passed time will be accumulated into a single value, which indicates the activity of this model. This is required if the activity is e.g. the total time taken by the transition functions.

Should the boolean be *True*, only the final state will be used to determine the activity. This will effectively drop all information that was gathered during the simulation and only return the activity that was determined at the final simulation step (up to the GVT). While it does not show complete behaviour of the model, it provides a (consistent!) snapshot of the complete model. A simple use case could be when modelling a road, where the amount of cars on the road determine the activity. If every road then returns 1 if there is a car on it and 0 otherwise, the activity information can be used to fetch all models that contained a car.

TODO: *getRelocations()*
