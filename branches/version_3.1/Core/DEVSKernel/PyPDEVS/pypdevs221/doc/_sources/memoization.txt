Memoization
===========

PyPDEVS supports memoization for the most heavyweight functions that are called during simulation.

What is memoization?
--------------------

Memoization simply means that the return values of a function call will be cached. 
As soon as the function is called again with exactly the same parameters, the cached value will be 
returned instead of the function being reevaluated again.
The advantage is clearly that it has the potential to speed up computation in situations where
the value is likely to be cached **and** if the function takes a relatively long time.

How does it apply to PyPDEVS?
-----------------------------

The PyPDEVS code is significantly optimized, though a certain part of the code is inoptimizable by
the simulator itself. This code is the *user code*, which defines e.g. the transition functions of
the model. These transition functions have the potential to computationally intensive. For example,
most distributed simulation benchmarks have a transition function which takes in the terms of milliseconds.

The only remaining requirement is then that the value is *likely* to be cached. For this reason, memoization
is only used in distributed simulation. In distributed simulation, a complete node might have to revert
all of its computation due to another (unrelated) model requesting such a revertion. Most of the time,
this model is not influenced by the change directly, therefore the input parameters of the function are
likely to be identical.

It is therefore possible to assume that distributed simulation is likely to profit from this optimization,
certainly in the case of relocations. When a relocation happens, the node is reverted to the current GVT,
even though no real causality violation happened. These transitions can then be recalculated immediately with
the use of memoization.

Why not enable it by default?
-----------------------------

Even though memoization seems a way to quickly increase performance, it also has several downsides. The most
important downside is the high space complexity that it incurs. Time warp simulation is already extremely
space consuming, so also caching the inputs and their response is not going to be of much help to that.
This problem is partially mitigated by having time warp and memoization refer to the same state in memory,
though this still requires additional lists, input dictionaries, ...

Another problem is the datastructure management. As soon as a revertion happens, the list of old states is
reverted and used to check for equality. Without memoization, this list would be discarded, freeing up lots
of space. Therefore, this problem again relates to space complexity.

A final problem is the requirement to check the states for equality. These checks can take arbitrarily long,
depending on how the user defined the equality method. In the worst case, the user might not have defined such
a method, causing every comparison to result in *False*. This is clearly problematic, as the memoization speedup 
will then never be visible. Furthermore, memoization is unlikely to have an impact in simulations where nearly
no revertions happen.

For these reasons, memoization is not enabled by default, but only when the user enables it explicitly.

Implementation hints
--------------------

Due to the way memoization is implemented in PyPDEVS, some considerations apply:

1. As soon as an inequal state is found, memoization code is aborted because the chance of further equality becomes too small.
2. Memoization code is only triggered after a revertion happened.
3. Due to memoization, side-effects of the transition function are not performed. This includes printing, random number generation, ... Note that transition functions with side effects are already a bad idea in time warp simulationn.

Requirements
------------

Two requirements exist to use memoization. The first one is simply to enable it in the configuration, the second one 
requires a little more explanation.

By default, Python provides equality methods on two objects, but they always return *False* if the objects are different 
(even though their content might be equal). 
The user should thus add the *__eq__(self, other)* and *__hash__(self)* function, to provide user-defined equality.

Technically, it is required that the output is **exactly** the same when the current state (and input message, in case
of *external* and *confluent transitions*) are equal according to these methods.

Example
-------

Simply enabling memoization is not that difficult and is simply::

    sim = Simulator(MyModel())
    sim.setMemoization(True)
    sim.simulate()

Defining the equality method on a state can be::
    
    class MyState(object):
        def __init__(self, var1, var2):
            self.var1 = var1
            self.var2 = var2

        def __eq__(self, other):
            return self.var1 == other.var1 and self.var2 == other.var2

        def __hash__(self):
            return hash(hash(self.var1) + hash(self.var2))
