from pypdevs.DEVS import AtomicDEVS

# Define the state of the processor as a structured object
class ProcessorState(object):
    def __init__(self):
        # State only contains the current event
        self.evt = None

class Processor(AtomicDEVS):
    def __init__(self, nr, proc_param):
        AtomicDEVS.__init__(self, "Processor_%i" % nr)

        self.state = ProcessorState()
        self.in_proc = self.addInPort("in_proc")
        self.out_proc = self.addOutPort("out_proc")
        self.out_finished = self.addOutPort("out_finished")

        # Define the parameters of the model
        self.speed = proc_param
        self.nr = nr

    def intTransition(self):
        # Just clear processing event
        self.state.evt = None
        return self.state

    def extTransition(self, inputs):
        # Received a new event, so start processing it
        self.state.evt = inputs[self.in_proc]
        # Calculate how long it will be processed
        time = 20.0 + max(1.0, self.state.evt.size / self.speed)
        self.state.evt.processing_time = time
        return self.state

    def timeAdvance(self):
        if self.state.evt:
            # Currently processing, so wait for that
            return self.state.evt.processing_time
        else:
            # Idle, so don't do anything
            return float('inf')

    def outputFnc(self):
        # Output the processed event and signal as finished
        return {self.out_proc: self.state.evt,
                self.out_finished: self.nr}
