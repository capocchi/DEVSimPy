Nested simulation
=================

.. versionchanged:: 2.1.3
   Nested simulation is only possible if **both** the nested simulation and the invoking simulation are **local** simulations.

.. versionchanged:: 2.2.0
   Allow nested local simulations in distributed simulations.

Nested simulation allows a simulation to be influenced by the results of another simulation. This functionality is very simple to use, as it just works as expected. In one of the user-defined functions of the model, it is thus possible to create another model and another simulator and simulate that new simulator. The only difference is that some specific configurations do not work on the nested simulation, such as using a logging server.

An example of nesting is provided in the remainder of this subsection.

Suppose we want to create a *Processor* which has a state of how many messages it has already processed. This amount of messages is then used to determine the *timeAdvance*, but in a very specific way that is determined by another DEVS simulation. This example is somewhat contrived, though the example is supposed to be as small as possible to only show how it works, not the utility of the feature.

The following code implements such behaviour::

    class State(object):
        def __init__(self):
            self.processed = 0
            self.processing = False

    class NestedProcessor(AtomicDEVS):
        def __init__(self):
            AtomicDEVS.__init__(self, "Nested")
            self.state = State()
            self.inport = self.addInPort("inport")
            self.outport = self.addOutPort("outport")

        def extTransition(self, inputs):
            self.state.processing = True
            return self.state

        def intTransition(self):
            self.state.processed += 1
            return self.state

        def outputFnc(self):
            return {self.outport: [1]}

        def timeAdvance(self):
            if self.state.processing:
                # Determine the time based on another simulation
                from simulator import Simulator
                from myqueue import CQueue
                model = CQueue()
                # The processed attribute of the state is used to determine the processing time in our example
                model.queue.processing_time = self.state.processed
                sim = Simulator(model)
                sim.setTerminationTime(5.0)
                sim.simulate()
                return max(1, model.queue.state)
            else:
                return INFINITY

In our example, we only used nested simulation in the *timeAdvance* function, though it is possible everywhere.
