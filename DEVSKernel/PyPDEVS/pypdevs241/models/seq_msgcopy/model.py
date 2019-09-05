import sys
sys.path.append("../../src/")

from infinity import INFINITY
from simulator import Simulator
from DEVS import *
import random

class Event:
    def __init__(self, eventSize):
        self.eventSize = eventSize

    def copy(self):
        return Event(self.eventSize)

class ProcessorState:
    def __init__(self):
        self.event1_counter = INFINITY
        self.event1 = None
        self.queue = []

class Processor(AtomicDEVS):
    def __init__(self, name, randomta):
        AtomicDEVS.__init__(self, name)
        self.recv_event1 = self.addInPort("in_event1")
        self.send_event1 = self.addOutPort("out_event1")
        self.state = ProcessorState()
        self.randomta = randomta
                
    def timeAdvance(self):
        return self.state.event1_counter

    def intTransition(self):
        self.state.event1_counter -= self.timeAdvance()
        if self.state.event1_counter == 0 and self.state.queue == []:
            self.state.event1_counter = INFINITY
            self.state.event1 = None
        else:
            self.state.event1 = self.state.queue.pop()
            self.state.event1_counter = round(random.uniform(0.75, 1.25), 4) if self.randomta else 1.0
        return self.state

    def extTransition(self, inputs):
        self.state.event1_counter -= self.elapsed
        #Only one element, so exploit this
        ev1 = inputs[self.recv_event1][0]
        if self.state.event1 is not None:
            self.state.queue.append(ev1)
        else:
            self.state.event1 = ev1
            self.state.event1_counter = round(random.uniform(0.75, 1.25), 4) if self.randomta else 1.0
        return self.state

    def outputFnc(self):
        return {self.send_event1: [self.state.event1]}

class Generator(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "Generator")
        self.state = "gen_event1"
        self.send_event1 = self.addOutPort("out_event1")
                
    def timeAdvance(self):
        return 1

    def intTransition(self):
        return self.state

    def outputFnc(self):
        return {self.send_event1: [Event(1)]}

class CoupledRecursion(CoupledDEVS):
    def __init__(self, width, depth, randomta):
        CoupledDEVS.__init__(self, "Coupled" + str(depth))
        self.recv_event1 = self.addInPort("in_event1")
        self.send_event1 = self.addOutPort("out_event1")

        if depth > 1:
            self.recurse = self.addSubModel(CoupledRecursion(width, depth-1, randomta))
            self.connectPorts(self.recv_event1, self.recurse.recv_event1)

        for i in range(width):
            processor = self.addSubModel(Processor("Processor%s_%s" % (depth, i), randomta))
            if i == 0:
                if depth > 1:
                    self.connectPorts(self.recurse.send_event1, processor.recv_event1)
                else:
                    self.connectPorts(self.recv_event1, processor.recv_event1)
            else:
                self.connectPorts(prev.send_event1, processor.recv_event1)
            prev = processor
        self.connectPorts(prev.send_event1, self.send_event1)

class DEVStone(CoupledDEVS):
    def __init__(self, width, depth, randomta):
        random.seed(1)
        CoupledDEVS.__init__(self, "DEVStone")
        self.generator = self.addSubModel(Generator())
        self.recurse = self.addSubModel(CoupledRecursion(width, depth, randomta))

        self.connectPorts(self.generator.send_event1, self.recurse.recv_event1)
