Common problems and their solution
==================================

The most important parts in PyPDEVS are guarded by a *DEVSException*. Such an exception being thrown is probably due to a modelling error (or more likely: a bug in the simulator). These exceptions should contain enough information about what went wrong and should normally only be seen if violations of DEVS were written (or a simulator bug).

Other problems are often caused due to an ommission of the modeller. This section tries to provide an overview of common problems for first-time modellers using PyPDEVS.

ImportError: No module named X
------------------------------

This indicates that PyPDEVS isn't imported correctly. While this is actually just a Python error, it is still handled here as this is one of the most common questions.

To import PyPDEVS, you need to do one of the following:

* Extend your search path (recommended)
* Set a PYTHONPATH environment variable
* Put the *contents* of the *src* folder in the same folder as your model (**NOT** recommended)

Assume you have the following directory structure::

    PyPDEVS
    |- src
       |- basesimulator.py
       |- colors.py
       |- controller.py
       |- ...
    |- myExperiments
       |- myModel.py
       |- myExperiment.py

In order to use the Python files from the *src* directory, it is necessary to extend your search path from the (default) *myExperiments* folder, to the *src* folder. This can be done using the syntax::

    import sys
    sys.path.append('../src/')

Of course, this syntax assumes that you are running this from the *myExperiments* folder. Python will not complain on unknown paths, so you can add as many as you like for every possible situation that you want to call it. Another option (though less flexible) is to use an absolute path, for example::

    import sys
    sys.path.append('/home/user/PyPDEVS/src')

.. note::
   You should include the *src* folder and not simply the *PyPDEVS* folder!

AttributeError: 'X' object has no attribute 'IPorts' (or 'OPorts' or 'componentSet')
------------------------------------------------------------------------------------

This problem indicates that you forgot to initialize the superclass of your own DEVS models as the **first** instruction. For example::

    class MyAtomicDEVSModel(AtomicDEVS):
        def __init__(self):
            AtomicDEVS.__init__(self, 'name') # <-- you probably forgot this line
            # Remainder of your initialisation

The same should happen for CoupledDEVS models::
    
    class MyCoupledDEVSModel(CoupledDEVS):  
        def __init__(self):
            CoupledDEVS.__init__(self, 'name') # <-- you probably forgot this line
            # Remainder of your initialisation

TypeError: 'NoneType' object is not iterable
--------------------------------------------

This most likely indicates that you forgot to return a dictionary in the *outputFnc* function. Even if no output is generated, it is mandatory to return a dictionary::

    def outputFnc(self):
        return {} # <-- This is required

TypeError: 'X' object is not iterable
-------------------------------------

.. note:: This solution is not valid in Classic DEVS simulation, as here it is allowed to be a simple value.

Probably, you forgot to return the values in your dicationary as a list, as is required in parallel DEVS. For example::

    def outputFnc(self):
        # return {self.outport: myMessage} <-- WRONG
        return {self.outport: [myMessage]}

AttributeError: 'List' object has no attribute 'X'
--------------------------------------------------

.. note:: This solution is not valid in Classic DEVS simulation, as here it is allowed to be a simple value.

This is equivalent to the previous error: the values of the inputs dictionary are lists instead of the actual values::

    def extTransition(self, inputs):
        # processMessage(inputs[self.inport]) <-- WRONG
        for msg in inputs[self.inport]:
            processMessage(msg)

.. warning:: To be complete, it is not sufficient to just take the first element from the list, as there might be more elements. Always using [0] carelessly is therefore discouraged.

AttributeError: 'NoneType' has no attribute 'X'
-----------------------------------------------

You probably forgot to return the new state in one of the transition functions. Transition functions should always return the new state. In case only state attributes are updated, it is necessary to return the *self.state* variable::

    def intTransition(self):
        self.state.message = 5 # <-- OK, state is updated
        return self.state # <-- Don't forget this

Alternatively::
    
    def intTransition(self):
        return State(5) # <-- Simply create a completely new state

New state: <X object at 0xXXXXXXX>
----------------------------------

Not actually a problem, though it is worth noting that you can have custom string output by defining a *__str__(self)* function for your state in case it is a class.

AttributeError: 'module' object has no attribute 'YourCoupledDEVSClass'
-----------------------------------------------------------------------

This means that you have a wrong import order. Due to the way MPI runs, it starts up the same file multiple times. To get around this problem, PyPDEVS will stop execution at the server nodes as soon as they are started up. However, they still need to have the actual model to be simulated loaded. For this reason, the import of the *simulator* file should happend after the import of the models. In case you have your model and experiment in the same file, you should add the import to simulator right before creating the model, preferably even in a conditional::

    class MyCoupledDEVSModel(CoupledDEVS):
        def __init__(self):
            ...

    if __name__ == "__main__":
        from simulator import Simulator
        model = MyCoupledDEVSModel()
        sim = Simulator(model)
        sim.simulate()

The execution of the file will stop as soon as the *simulator* file is imported, so make sure that all your models are imported by that time. The simplest way to solve this problem is by creating seperate model and experiment files.
