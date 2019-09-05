from pypdevs.DEVS import AtomicDEVS

# Define the state of the collector as a structured object
class CollectorState(object):
    def __init__(self):
        # Contains received events and simulation time
        self.events = []
        self.current_time = 0.0

class Collector(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "Collector")
        self.state = CollectorState()
        # Has only one input port
        self.in_event = self.addInPort("in_event")

    def extTransition(self, inputs):
        # Update simulation time
        self.state.current_time += self.elapsed
        # Calculate time in queue
        evt = inputs[self.in_event]
        time = self.state.current_time - evt.creation_time - evt.processing_time
        inputs[self.in_event].queueing_time = max(0.0, time)
        # Add incoming event to received events
        self.state.events.append(inputs[self.in_event])
        return self.state

    # Don't define anything else, as we only store events.
    # Collector has no behaviour of its own.
