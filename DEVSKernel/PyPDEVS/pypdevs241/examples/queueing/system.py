from pypdevs.DEVS import CoupledDEVS

# Import all models to couple
from generator import Generator
from queue import Queue
from processor import Processor
from collector import Collector

class QueueSystem(CoupledDEVS):
    def __init__(self, mu, size, num, procs):
        CoupledDEVS.__init__(self, "QueueSystem")

        # Define all atomic submodels of which there are only one
        generator = self.addSubModel(Generator(mu, size, num))
        queue = self.addSubModel(Queue(len(procs)))
        collector = self.addSubModel(Collector())

        self.connectPorts(generator.out_event, queue.in_event)

        # Instantiate desired number of processors and connect
        processors = []
        for i, param in enumerate(procs):
            processors.append(self.addSubModel(
                              Processor(i, param)))
            self.connectPorts(queue.out_proc[i],
                              processors[i].in_proc)
            self.connectPorts(processors[i].out_finished,
                              queue.in_finish)
            self.connectPorts(processors[i].out_proc,
                              collector.in_event)

        # Make it accessible outside of our own scope
        self.collector = collector
