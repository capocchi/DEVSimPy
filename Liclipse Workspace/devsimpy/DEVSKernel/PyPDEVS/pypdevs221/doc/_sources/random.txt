Random Number Generation
========================

Using the normal *random* library during simulation is not recommended in situations where repeatability is desired. Even though the *random* library uses a seed to guarantee determinism, this seed is part of a global state and is thus **not** allowed in pure DEVS. In sequential classic DEVS, this most likely doesn't pose a real problem, though even then it is possible that it might go wrong.

To solve these problems, a very basic *random number generator* is included in the simulator. The model that needs random numbers should create an instantiation of this generator and save it **in its state**. All random numbers should afterwards be requested from this object. The random number generator class will take special measures to ensure that the seed is actually encapsulated in the object itself and doesn't rely on the global seed.

.. note:: Even though the random number generator classes are not influenced by calls to the *random* library, the reverse is true. This is due to the class simply being a wrapper, which still redirects its calls to the library function. This should not pose a problem, as the use of the library function in its pure form should be avoided at all costs.

.. note:: While the random number generator class simply redirects its calls to the *random* library, the returned values will **not** be equal to those provided by the *random* library through direct access. This is due to the fact that another random number is generated to be used as a seed.

.. warning:: Making calls to the random number generator will alter its state. This means that it is only allowed to make calls on the object from within the *intTransition*, *extTransition*, *confTransition* and *__init__* methods!

Overridable
-----------

Like many parts of the simulator, this random number generator is only provided for convenience. The user might want to have its own special random number generator, one with more functionality, ... This is all possible, though if this is done, it should be similar to the one provided with the simulator. At least, it should implement the *__eq__*, *__hash__* and *copy* methods, with the expected behaviour. Furthermore, such implementations should also encapsulate the seed in one way or the other. Simply relying on the *random* library to have a correct seed is **unacceptable**.

Example
-------

A simple example is provided by this processor, which takes a random time to process a message. While this code is not that spectacular, the importance is that this code will **always** return the same traces, independent of the use of distribution, the presence of revertions, indeterminism in execution order of transition functions, ...

Such a processor and its state look like::

    class RandomProcessorState(object):
        def __init__(self, seed):
            from randomGenerator import RandomGenerator
            self.randomGenerator = RandomGenerator(seed)
            self.queue = []
            self.proctime = self.randomGenerator.uniform(0.3, 3.0)

        def __str__(self):
            return "Random Processor State -- " + str(self.proctime)

    class RandomProcessor(AtomicDEVS):
        def __init__(self, seed):
            AtomicDEVS.__init__(self, "RandomProcessor_" + str(seed))
            self.inport = self.addInPort("inport")
            self.outport = self.addOutPort("outport")
            self.state = RandomProcessorState(seed)

        def intTransition(self):
            self.state.queue = self.state.queue[1:]
            self.state.proctime = self.state.randomGenerator.uniform(0.3, 3.0)
            return self.state

        def extTransition(self, inputs):
            if self.state.queue:
                self.state.proctime -= self.elapsed
            self.state.queue.extend(inputs[self.inport])
            return self.state

        def outputFnc(self):
            return {self.outport: [self.state.queue[0]]}

        def timeAdvance(self):
            if self.state.queue:
                return self.state.proctime
            else:
                return INFINITY

As long as the same seed is passed, the results will always be the same.
