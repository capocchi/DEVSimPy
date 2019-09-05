import sys
import os.path

from pypdevs.infinity import *
from pypdevs.DEVS import AtomicDEVS, CoupledDEVS

class Event(object):
    def __init__(self, eventSize):
        self.eventSize = eventSize

    def __str__(self):
        return "Eventsize = " + str(self.eventSize)

class ModelState(object):
    def __init__(self):
        self.counter = INFINITY
        self.event = None

    def __str__(self):
        return str(self.counter)

    def toXML(self):
        return "<counter>" + str(self.counter) + "</counter>"

class ProcessorNPP(AtomicDEVS):
    def __init__(self, name = "Processor", t_event1 = 1):
        AtomicDEVS.__init__(self, name)
        self.t_event1 = t_event1
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")
        self.state = ModelState()
        
    def timeAdvance(self):
        return self.state.counter

    def intTransition(self):
        self.state.counter -= self.timeAdvance()
        if self.state.counter == 0:
            self.state.counter = INFINITY
            self.state.event = None
        return self.state

    def extTransition(self, inputs):
        self.state.counter -= self.elapsed
        ev1 = inputs[self.inport][0]
        if ev1 != None:
            self.state.event = ev1
            self.state.counter = self.t_event1
        return self.state

    def outputFnc(self):
        output = {}
        mini = self.state.counter
        if self.state.counter == mini:
            output[self.outport] = [self.state.event]
        return output

class RemoteDCProcessor(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "RemoteDCProcessor")
        mod = self.addSubModel(CoupledProcessor(1, 1), 2)
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")
        self.connectPorts(self.inport, mod.inport)
        self.connectPorts(mod.outport, self.outport)

class Processor(AtomicDEVS):
    def __init__(self, name = "Processor", t_event1 = 1):
        AtomicDEVS.__init__(self, name)
        self.t_event1 = t_event1
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")
        self.state = ModelState()
        
    def timeAdvance(self):
        return self.state.counter

    def intTransition(self):
        self.state.counter -= self.timeAdvance()
        if self.state.counter == 0:
            self.state.counter = INFINITY
            self.state.event = None
        return self.state

    def extTransition(self, inputs):
        self.state.counter -= self.elapsed
        ev1 = inputs[self.inport][0]
        if ev1 != None:
            self.state.event = ev1
            self.state.counter = self.t_event1
        return self.state

    def outputFnc(self):
        mini = self.state.counter
        if self.state.counter == mini:
            return {self.outport: [self.state.event]}
        else:
            return {}

class HeavyProcessor(AtomicDEVS):
    def __init__(self, name = "Processor", t_event1 = 1, iterations = 0):
        AtomicDEVS.__init__(self, name)
        self.t_event1 = t_event1
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")
        self.state = ModelState()
        self.iterations = iterations
        
    def timeAdvance(self):
        return self.state.counter

    def intTransition(self):
        self.state.counter -= self.timeAdvance()
        # Do lots of work now
        stupidcounter = 0
        for _ in range(self.iterations):
            pass
        if self.state.counter == 0:
            self.state.counter = INFINITY
            self.state.event = None
        return self.state

    def extTransition(self, inputs):
        self.state.counter -= self.elapsed
        ev1 = inputs[self.inport][0]
        stupidcounter = 0
        for _ in range(self.iterations):
            pass
        if ev1 != None:
            self.state.event = ev1
            self.state.counter = self.t_event1
        return self.state

    def outputFnc(self):
        mini = self.state.counter
        stupidcounter = 0
        for _ in range(self.iterations):
            pass
        if self.state.counter == mini:
            return {self.outport: [self.state.event]}

class NestedProcessor(Processor):
    def __init__(self, name = "NestedProcessor"):
        Processor.__init__(self, name)
        self.state.processed = 0
        self.state.event = Event(5)

    def extTransition(self, inputs):
        self.state = Processor.extTransition(self, inputs)
        self.state.processed += 1
        return self.state

    def timeAdvance(self):
        from pypdevs.simulator import Simulator
        model = CoupledGenerator()
        sim = Simulator(model)
        sim.setTerminationTime(self.state.processed)
        #sim.setVerbose(True)
        sim.simulate()
        result = max(sim.model.generator.state.generated, 1)
        return result

class Generator(AtomicDEVS):
    def __init__(self, name = "Generator", t_gen_event1 = 1.0, binary = False):
        AtomicDEVS.__init__(self, name)
        self.state = ModelState()
        # Add an extra variable
        self.state.generated = 0
        self.state.counter = t_gen_event1
        self.state.value = 1
        self.t_gen_event1 = t_gen_event1
        self.outport = self.addOutPort("outport")
        self.inport = self.addInPort("inport")
        self.binary = binary
        
    def timeAdvance(self):
        return self.state.counter

    def intTransition(self):
        self.state.generated += 1
        return self.state

    def extTransition(self, inputs):
        self.state.counter -= self.elapsed
        return self.state

    def outputFnc(self):
        if self.binary:
            return {self.outport: ["b1"]}
        else:
            return {self.outport: [Event(self.state.value)]}

class GeneratorNPP(AtomicDEVS):
    def __init__(self, name = "Generator", t_gen_event1 = 1.0):
        AtomicDEVS.__init__(self, name)
        self.state = ModelState()
        # Add an extra variable
        self.state.generated = 0
        self.state.counter = t_gen_event1
        self.t_gen_event1 = t_gen_event1
        self.outport = self.addOutPort("outport")
        self.inport = self.addInPort("inport")
        
    def timeAdvance(self):
        return self.state.counter

    def intTransition(self):
        self.state.generated += 1
        return self.state

    def extTransition(self, inputs):
        self.state.counter -= self.elapsed
        return self.state

    def outputFnc(self):
        return {self.outport: [Event(1)]}

class CoupledGenerator(CoupledDEVS):
    def __init__(self, t_gen_event1 = 1, binary = False):
        CoupledDEVS.__init__(self, "CoupledGenerator")
        self.generator = self.addSubModel(Generator("Generator", t_gen_event1, binary))
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")

        self.connectPorts(self.inport, self.generator.inport)
        self.connectPorts(self.generator.outport, self.outport)

class CoupledGeneratorNPP(CoupledDEVS):
    def __init__(self, t_gen_event1 = 1):
        CoupledDEVS.__init__(self, "CoupledGenerator")
        self.generator = self.addSubModel(GeneratorNPP("Generator", t_gen_event1))
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")

        self.connectPorts(self.inport, self.generator.inport)
        self.connectPorts(self.generator.outport, self.outport)

class CoupledHeavyProcessor(CoupledDEVS):
    def __init__(self, t_event1_P1, levels, iterations, name = None):
        if name == None:
            name = "CoupledHeavyProcessor_" + str(levels)
        CoupledDEVS.__init__(self, name)
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")

        self.coupled = []
        for i in range(levels):
            self.coupled.append(self.addSubModel(HeavyProcessor("Processor" + str(i), t_event1_P1, iterations)))
        for i in range(levels-1):
            self.connectPorts(self.coupled[i].outport, self.coupled[i+1].inport)
        self.connectPorts(self.inport, self.coupled[0].inport)
        self.connectPorts(self.coupled[-1].outport, self.outport)

class CoupledProcessorNPP(CoupledDEVS):
    def __init__(self, t_event1_P1, levels):
        CoupledDEVS.__init__(self, "CoupledProcessor_" + str(levels))
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")

        self.coupled = []
        for i in range(levels):
            self.coupled.append(self.addSubModel(ProcessorNPP("Processor" + str(i), t_event1_P1)))
        for i in range(levels-1):
            self.connectPorts(self.coupled[i].outport, self.coupled[i+1].inport)
        self.connectPorts(self.inport, self.coupled[0].inport)
        self.connectPorts(self.coupled[-1].outport, self.outport)

class CoupledProcessor(CoupledDEVS):
    def __init__(self, t_event1_P1, levels):
        CoupledDEVS.__init__(self, "CoupledProcessor_" + str(levels))
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")

        self.coupled = []
        for i in range(levels):
            self.coupled.append(self.addSubModel(Processor("Processor" + str(i), t_event1_P1)))
        for i in range(levels-1):
            self.connectPorts(self.coupled[i].outport, self.coupled[i+1].inport)
        self.connectPorts(self.inport, self.coupled[0].inport)
        self.connectPorts(self.coupled[-1].outport, self.outport)

class CoupledProcessorMP(CoupledDEVS):
    def __init__(self, t_event1_P1):
        CoupledDEVS.__init__(self, "CoupledProcessorMP")
        self.inport = self.addInPort("inport")

        p1 = self.addSubModel(Processor("Processor1", t_event1_P1))
        p2 = self.addSubModel(Processor("Processor2", t_event1_P1))
        p3 = self.addSubModel(Processor("Processor3", t_event1_P1))
        p4 = self.addSubModel(Processor("Processor4", t_event1_P1))
        self.connectPorts(self.inport, p1.inport)
        self.connectPorts(self.inport, p3.inport)
        self.connectPorts(p1.outport, p2.inport)
        self.connectPorts(p3.outport, p4.inport)

class Binary(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Binary")
        self.generator = self.addSubModel(CoupledGenerator(1.0, True))
        self.processor1 = self.addSubModel(CoupledProcessor(0.6, 2), 2)
        self.processor2 = self.addSubModel(CoupledProcessor(0.30, 3), 1)
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)

class Binary_local(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Binary")
        self.generator = self.addSubModel(CoupledGenerator(1.0, True))
        self.processor1 = self.addSubModel(CoupledProcessor(0.6, 2))
        self.processor2 = self.addSubModel(CoupledProcessor(0.30, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)

class Chain_local(CoupledDEVS):
    def __init__(self, ta):
        CoupledDEVS.__init__(self, "Chain")
        self.generator = self.addSubModel(CoupledGenerator(1.0))
        self.processor1 = self.addSubModel(CoupledProcessor(ta, 2))
        self.processor2 = self.addSubModel(CoupledProcessor(0.30, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)

class Chain(CoupledDEVS):
    def __init__(self, ta):
        CoupledDEVS.__init__(self, "Chain")
        self.generator = self.addSubModel(CoupledGenerator(1.0), 1)
        self.processor1 = self.addSubModel(CoupledProcessor(ta, 2), 2)
        self.processor2 = self.addSubModel(CoupledProcessor(0.30, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)

class Boundary(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Boundary")
        self.generator = self.addSubModel(CoupledGenerator(1.0), 1)
        self.processor1 = self.addSubModel(CoupledProcessor(0.60, 2), 2)
        self.processor2 = self.addSubModel(CoupledProcessor(0.30, 4), 3)
        self.processor3 = self.addSubModel(CoupledProcessor(0.30, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)
        self.connectPorts(self.processor1.outport, self.processor3.inport)
        self.connectPorts(self.processor2.outport, self.processor3.inport)

class Two(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Two")
        self.generator = self.addSubModel(CoupledGenerator(1.0), 1)
        self.processor1 = self.addSubModel(CoupledProcessor(0.30, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)

class DualChain_local(CoupledDEVS):
    def __init__(self, ta):
        CoupledDEVS.__init__(self, "DualChain")
        self.generator = self.addSubModel(CoupledGenerator(1.0))
        self.processor1 = self.addSubModel(CoupledProcessor(ta, 2))
        self.processor2 = self.addSubModel(CoupledProcessor(0.30, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.generator.outport, self.processor2.inport)

class DualChain(CoupledDEVS):
    def __init__(self, ta):
        CoupledDEVS.__init__(self, "DualChain")
        self.generator = self.addSubModel(CoupledGenerator(1.0), 1)
        self.processor1 = self.addSubModel(CoupledProcessor(ta, 2), 2)
        self.processor2 = self.addSubModel(CoupledProcessor(0.30, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.generator.outport, self.processor2.inport)

class DualChainMP_local(CoupledDEVS):
    def __init__(self, ta):
        CoupledDEVS.__init__(self, "DualChainMP")
        self.generator = self.addSubModel(CoupledGenerator(1.0))
        self.processor1 = self.addSubModel(CoupledProcessorMP(0.66))
        self.connectPorts(self.generator.outport, self.processor1.inport)

class DualChainMP(CoupledDEVS):
    def __init__(self, ta):
        CoupledDEVS.__init__(self, "DualChainMP")
        self.generator = self.addSubModel(CoupledGenerator(1.0), 1)
        self.processor1 = self.addSubModel(CoupledProcessorMP(0.66), 2)
        self.connectPorts(self.generator.outport, self.processor1.inport)

class DualDepthProcessor_local(CoupledDEVS):
    def __init__(self, ta):
        CoupledDEVS.__init__(self, "DualDepthProcessor")
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")
        self.processor1 = self.addSubModel(CoupledProcessor(ta, 1))
        self.processor2 = self.addSubModel(CoupledProcessor(ta, 2))
        self.connectPorts(self.inport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)
        self.connectPorts(self.processor2.outport, self.outport)

class DualDepthProcessor(CoupledDEVS):
    def __init__(self, ta):
        CoupledDEVS.__init__(self, "DualDepthProcessor")
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")
        self.processor1 = self.addSubModel(CoupledProcessor(ta, 1), 2)
        self.processor2 = self.addSubModel(CoupledProcessor(ta, 2))
        self.connectPorts(self.inport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)
        self.connectPorts(self.processor2.outport, self.outport)

class DualDepth_local(CoupledDEVS):
    def __init__(self, ta):
        CoupledDEVS.__init__(self, "DualDepth")
        self.generator = self.addSubModel(Generator("Generator", 1.0))
        self.processor = self.addSubModel(DualDepthProcessor_local(ta))
        self.connectPorts(self.generator.outport, self.processor.inport)

class DualDepth(CoupledDEVS):
    def __init__(self, ta):
        CoupledDEVS.__init__(self, "DualDepth")
        self.generator = self.addSubModel(Generator("Generator", 1.0))
        self.processor = self.addSubModel(DualDepthProcessor(ta), 1)
        self.connectPorts(self.generator.outport, self.processor.inport)

class Nested_local(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Nested")
        self.generator = self.addSubModel(Generator("Generator", 1))
        self.processor = self.addSubModel(NestedProcessor("NProcessor"))
        self.connectPorts(self.generator.outport, self.processor.inport)

class MultiNested(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "MultiNested")
        self.generator = self.addSubModel(Generator("Generator", 1))
        self.processor1 = self.addSubModel(NestedProcessor("NProcessor1"), 1)
        self.processor2 = self.addSubModel(NestedProcessor("NProcessor2"), 2)
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)

class Local(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Local")
        self.generator = self.addSubModel(Generator("Generator", 1))
        self.processor1 = self.addSubModel(CoupledProcessor(1, 2))
        self.processor2 = self.addSubModel(CoupledProcessor(1, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)

class OptimizableChain(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "OptimizableChain")
        self.generator = self.addSubModel(CoupledGenerator(1.0))
        self.processor1 = self.addSubModel(CoupledProcessor(0.66, 2), 1)
        self.processor2 = self.addSubModel(CoupledProcessor(0.30, 3), 2)
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)

class HugeOptimizableChain(CoupledDEVS):
    def __init__(self, iterations):
        CoupledDEVS.__init__(self, "HugeOptimizableChain")
        self.generator = self.addSubModel(CoupledGenerator(1.0))
        self.processor0 = self.addSubModel(CoupledHeavyProcessor(0.77, 10, iterations))
        self.processor1 = self.addSubModel(CoupledHeavyProcessor(0.66, 10, iterations), 1)
        self.processor2 = self.addSubModel(CoupledHeavyProcessor(0.30, 10, iterations), 2)
        self.connectPorts(self.generator.outport, self.processor0.inport)
        self.connectPorts(self.processor0.outport, self.processor1.inport)
        self.connectPorts(self.processor0.outport, self.processor2.inport)

class HugeOptimizableLocalChain(CoupledDEVS):
    def __init__(self, iterations):
        CoupledDEVS.__init__(self, "HugeOptimizableChain")
        self.generator = self.addSubModel(CoupledGenerator(1.0))
        self.processor0 = self.addSubModel(CoupledHeavyProcessor(0.77, 10, iterations))
        self.processor1 = self.addSubModel(CoupledHeavyProcessor(0.66, 10, iterations))
        self.processor2 = self.addSubModel(CoupledHeavyProcessor(0.30, 10, iterations))
        self.connectPorts(self.generator.outport, self.processor0.inport)
        self.connectPorts(self.processor0.outport, self.processor1.inport)
        self.connectPorts(self.processor0.outport, self.processor2.inport)

class LocalLong(CoupledDEVS):
    def __init__(self, name):
        CoupledDEVS.__init__(self, name)
        self.generator = self.addSubModel(Generator("Generator", 1))
        self.processor1 = self.addSubModel(CoupledProcessor(0.66, 20))
        self.connectPorts(self.generator.outport, self.processor1.inport)

class ParallelChain(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "ParallelChain")
        self.processor1 = self.addSubModel(LocalLong('Local1'), 1)
        self.processor2 = self.addSubModel(LocalLong('Local2'), 2)

class ParallelLocalChain(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "ParallelLocalChain")
        self.processor1 = self.addSubModel(LocalLong('Local1'))
        self.processor2 = self.addSubModel(LocalLong('Local2'))

class ChainNoPeekPoke(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "ChainNoPeekPoke")
        self.generator = self.addSubModel(CoupledGeneratorNPP(1.0))
        self.processor1 = self.addSubModel(CoupledProcessorNPP(0.66, 2))
        self.processor2 = self.addSubModel(CoupledProcessorNPP(0.30, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)

class ChainPeekPoke(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "ChainPeekPoke")
        self.generator = self.addSubModel(CoupledGenerator(1.0))
        self.processor1 = self.addSubModel(CoupledProcessor(0.66, 2))
        self.processor2 = self.addSubModel(CoupledProcessor(0.30, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)

class AutoDistChain(CoupledDEVS):
    def __init__(self, nodes, totalAtomics, iterations):
        CoupledDEVS.__init__(self, "AutoDistChain")
        self.generator = self.addSubModel(CoupledGenerator(1.0))
        self.processors = []
        have = 0
        ta = 0.66
        for i in range(nodes):
            shouldhave = (float(i+1) / nodes) * totalAtomics
            num = int(shouldhave - have)
            have += num
            if i == 0:
                self.processors.append(self.addSubModel(CoupledHeavyProcessor(ta, num, iterations, "HeavyProcessor_" + str(i))))
            else:
                self.processors.append(self.addSubModel(CoupledHeavyProcessor(ta, num, iterations, "HeavyProcessor_" + str(i)), i))
        self.connectPorts(self.generator.outport, self.processors[0].inport)
        for i in range(len(self.processors)-1):
            self.connectPorts(self.processors[i].outport, self.processors[i+1].inport)

class RemoteDC(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Root")
        self.generator = self.addSubModel(CoupledGenerator(1.0))
        self.processor1 = self.addSubModel(RemoteDCProcessor(), 1)
        self.processor2 = self.addSubModel(CoupledProcessor(0.30, 3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)

class MultipleInputs(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "MultipleInputs")
        self.generator = self.addSubModel(Generator(1.0))
        self.processors1 = []
        for i in range(5):
            self.processors1.append(self.addSubModel(Processor("1-" + str(i), 0.3), 1))
            self.connectPorts(self.generator.outport, self.processors1[-1].inport)
        self.processors2 = []
        for i in range(2):
            self.processors2.append(self.addSubModel(Processor("2-" + str(i), 0.3), 2))
            for s in self.processors1:
                self.connectPorts(s.outport, self.processors2[-1].inport)

class MultipleInputs_local(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "MultipleInputs")
        self.generator = self.addSubModel(Generator(1.0))
        self.processors1 = []
        for i in range(5):
            self.processors1.append(self.addSubModel(Processor("1-" + str(i), 0.3)))
            self.connectPorts(self.generator.outport, self.processors1[-1].inport)
        self.processors2 = []
        for i in range(2):
            self.processors2.append(self.addSubModel(Processor("2-" + str(i), 0.3)))
            for s in self.processors1:
                self.connectPorts(s.outport, self.processors2[-1].inport)

class DoubleLayer1(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Layer1")
        self.inport = self.addInPort("inport")
        self.processor = self.addSubModel(Processor("Processor", 0.3))
        self.connectPorts(self.inport, self.processor.inport)

class DoubleLayer2(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Layer2")
        self.lower = self.addSubModel(DoubleLayer1())
        self.inport1 = self.addInPort("inport1")
        self.inport2 = self.addInPort("inport2")
        self.connectPorts(self.inport1, self.lower.inport)
        self.connectPorts(self.inport2, self.lower.inport)

class DoubleLayerRoot(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Root")
        self.lower = self.addSubModel(DoubleLayer2())
        self.generator = self.addSubModel(Generator("Generator", 1))
        self.connectPorts(self.generator.outport, self.lower.inport1)
        self.connectPorts(self.generator.outport, self.lower.inport2)

class DSDEVSRoot(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Root")
        self.submodel = self.addSubModel(GeneratorDS())
        self.submodel2 = self.addSubModel(Processor())
        self.submodel3 = self.addSubModel(Processor())
        self.connectPorts(self.submodel.outport, self.submodel2.inport)
        self.connectPorts(self.submodel2.outport, self.submodel3.inport)
        self.connectPorts(self.submodel.outport, self.submodel3.inport)

    def modelTransition(self, state):
        self.removeSubModel(self.submodel2)
        self.submodel2 = self.addSubModel(Processor())
        self.connectPorts(self.submodel2.outport, self.submodel3.inport)
        self.submodel4 = self.addSubModel(CoupledProcessor(0.2, 3))
        self.connectPorts(self.submodel3.outport, self.submodel4.inport)
        self.submodelX = self.addSubModel(ElapsedNothing())
        return False

class ElapsedNothing(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "ElapsedNothing")
        self.elapsed = 0.3
        self.state = 1

    def intTransition(self):
        return 0

    def timeAdvance(self):
        return self.state if self.state > 0 else float('inf')

class GeneratorDS(Generator):
    def __init__(self):
        Generator.__init__(self, "GEN")
        self.elapsed = 0.5

    def outputFnc(self):
        if self.state.generated < 1:
            return Generator.outputFnc(self)
        else:
            return {}
        
    def modelTransition(self, state):
        if self.state.generated == 1:
            self.removePort(self.outport)
            del self.outport
        return self.state.generated == 1

class ClassicGenerator(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "Generator")
        self.state = None
        self.outport = self.addOutPort("outport")

    def intTransition(self):
        return None

    def outputFnc(self):
        return {self.outport: 1}

    def timeAdvance(self):
        return 1

class ClassicProcessor(AtomicDEVS):
    def __init__(self, name):
        AtomicDEVS.__init__(self, "Processor_%s" % name)
        self.state = None
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")
        
    def intTransition(self):
        return None

    def outputFnc(self):
        return {self.outport: self.state}

    def extTransition(self, inputs):
        self.state = inputs[self.inport]
        return self.state

    def timeAdvance(self):
        return (1.0 if self.state is not None else INFINITY)

class ClassicCoupledProcessor(CoupledDEVS):
    def __init__(self, it, namecounter):
        CoupledDEVS.__init__(self, "CoupledProcessor_%s_%s" % (it, namecounter))
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")
        if it != 0:
            self.subproc = self.addSubModel(ClassicCoupledProcessor(it-1, 0))
        else:
            self.subproc = self.addSubModel(ClassicProcessor(0))
        self.subproc2 = self.addSubModel(ClassicProcessor(1))
        if it != 0:
            self.subproc3 = self.addSubModel(ClassicCoupledProcessor(it-1, 2))
        else:
            self.subproc3 = self.addSubModel(ClassicProcessor(2))
        self.connectPorts(self.inport, self.subproc.inport)
        self.connectPorts(self.subproc.outport, self.subproc2.inport)
        self.connectPorts(self.subproc2.outport, self.subproc3.inport)
        self.connectPorts(self.subproc3.outport, self.outport)

    def select(self, immChildren):
        if self.subproc3 in immChildren:
            return self.subproc3
        elif self.subproc2 in immChildren:
            return self.subproc2
        elif self.subproc in immChildren:
            return self.subproc
        else:
            return immChildren[0]

class ClassicCoupled(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Coupled")
        self.generator = self.addSubModel(ClassicGenerator())
        self.processor = self.addSubModel(ClassicCoupledProcessor(3, 0))
        self.connectPorts(self.generator.outport, self.processor.inport)

    def select(self, immChildren):
        if self.processor in immChildren:
            return self.processor
        else:
            return immChildren[0]

class RandomProcessorState(object):
    def __init__(self, seed):
        from pypdevs.randomGenerator import RandomGenerator
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

class RandomCoupled(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Coupled")
        self.generator = self.addSubModel(Generator())
        self.processor1 = self.addSubModel(RandomProcessor(1), 1)
        self.processor2 = self.addSubModel(RandomProcessor(2), 2)
        self.processor3 = self.addSubModel(RandomProcessor(3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)
        self.connectPorts(self.processor2.outport, self.processor3.inport)

class RandomCoupled_local(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Coupled")
        self.generator = self.addSubModel(Generator())
        self.processor1 = self.addSubModel(RandomProcessor(1))
        self.processor2 = self.addSubModel(RandomProcessor(2))
        self.processor3 = self.addSubModel(RandomProcessor(3))
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)
        self.connectPorts(self.processor2.outport, self.processor3.inport)

class Chain_bad(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Chain")
        self.generator = self.addSubModel(CoupledGenerator(1.0), 0)
        self.processor1 = self.addSubModel(CoupledProcessor(0.66, 2), 1)
        self.processor2 = self.addSubModel(CoupledProcessor(0.66, 3), 2)
        self.processor3 = self.addSubModel(CoupledProcessor(0.66, 4), 1)
        self.processor4 = self.addSubModel(CoupledProcessor(0.66, 5), 0)
        self.processor5 = self.addSubModel(CoupledProcessor(0.30, 6), 2)
        self.connectPorts(self.generator.outport, self.processor1.inport)
        self.connectPorts(self.processor1.outport, self.processor2.inport)
        self.connectPorts(self.processor2.outport, self.processor3.inport)
        self.connectPorts(self.processor3.outport, self.processor4.inport)
        self.connectPorts(self.processor4.outport, self.processor5.inport)

class GeneratorClassic(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "Gen")
        self.outport = self.addOutPort("outport")
        self.state = True

    def intTransition(self):
        return False

    def outputFnc(self):
        return {self.outport: 3}

    def timeAdvance(self):
        return 1.0 if self.state else INFINITY

class ProcessorClassic1(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "P1")
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")
        self.state = None

    def intTransition(self):
        return None

    def extTransition(self, inputs):
        return inputs[self.inport]

    def outputFnc(self):
        return {self.outport: self.state}

    def timeAdvance(self):
        return 1.0 if self.state is not None else INFINITY

class ProcessorClassic2(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "P2")
        self.inport1 = self.addInPort("inport1")
        self.inport2 = self.addInPort("inport2")
        self.outport = self.addOutPort("outport")
        self.state = (None, None)

    def intTransition(self):
        return (None, None)

    def extTransition(self, inputs):
        inp1 = inputs.get(self.inport1, None)
        inp2 = inputs.get(self.inport2, None)
        return (inp1, inp2)

    def outputFnc(self):
        return {self.outport: self.state}

    def timeAdvance(self):
        return 1.0 if self.state[0] is not None or self.state[1] is not None else INFINITY

class ProcessorClassicO2(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "PO2")
        self.inport = self.addInPort("inport")
        self.outport1 = self.addOutPort("outport1")
        self.outport2 = self.addOutPort("outport2")
        self.state = None

    def intTransition(self):
        return None

    def extTransition(self, inputs):
        return inputs[self.inport]

    def outputFnc(self):
        return {self.outport1: self.state, self.outport2: self.state}

    def timeAdvance(self):
        return 1.0 if self.state is not None else INFINITY

class ProcessorCoupledClassic(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Coupled")
        self.inport1 = self.addInPort("inport1")
        self.inport2 = self.addInPort("inport2")
        self.outport = self.addOutPort("outport")

        self.proc1 = self.addSubModel(ProcessorClassic1())
        self.proc2 = self.addSubModel(ProcessorClassic1())

        self.connectPorts(self.inport1, self.proc1.inport)
        self.connectPorts(self.inport2, self.proc2.inport)
        self.connectPorts(self.proc1.outport, self.outport)
        self.connectPorts(self.proc2.outport, self.outport)

class AllConnectClassic(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "Root")
        self.model1 = self.addSubModel(GeneratorClassic())
        self.model2 = self.addSubModel(ProcessorCoupledClassic())
        self.model3 = self.addSubModel(ProcessorClassic2())
        self.model4 = self.addSubModel(ProcessorClassic1())
        self.model5 = self.addSubModel(ProcessorClassicO2())
        self.connectPorts(self.model1.outport, self.model2.inport1)
        self.connectPorts(self.model1.outport, self.model2.inport2)
        self.connectPorts(self.model2.outport, self.model3.inport1)
        self.connectPorts(self.model2.outport, self.model3.inport2)
        self.connectPorts(self.model3.outport, self.model5.inport)
        self.connectPorts(self.model2.outport, self.model4.inport)
        self.connectPorts(self.model4.outport, self.model5.inport)

def trans1(inp):
    inp.eventSize += 1
    return inp

def trans2(inp):
    inp.eventSize = 0
    return inp

class ZCoupledProcessor(CoupledDEVS):
    def __init__(self, num):
        CoupledDEVS.__init__(self, "CoupledProcessor_" + str(num))
        self.inport = self.addInPort("inport")
        self.outport = self.addOutPort("outport")

        self.coupled = []
        levels = 4
        for i in range(levels):
            self.coupled.append(self.addSubModel(Processor("Processor" + str(i), 1.0)))
        for i in range(levels-1):
            self.connectPorts(self.coupled[i].outport, self.coupled[i+1].inport, trans1)
        self.connectPorts(self.inport, self.coupled[0].inport)
        self.connectPorts(self.coupled[-1].outport, self.outport)

class ZChain_local(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "ROOT")
        self.gen = self.addSubModel(Generator())
        self.proc1 = self.addSubModel(ZCoupledProcessor(1))
        self.proc2 = self.addSubModel(ZCoupledProcessor(2))

        self.connectPorts(self.gen.outport, self.proc1.inport)
        self.connectPorts(self.gen.outport, self.proc2.inport, trans2)

class ZChain(CoupledDEVS):
    def __init__(self):
        CoupledDEVS.__init__(self, "ROOT")
        self.gen = self.addSubModel(Generator())
        self.proc1 = self.addSubModel(ZCoupledProcessor(1), 1)
        self.proc2 = self.addSubModel(ZCoupledProcessor(2), 2)

        self.connectPorts(self.gen.outport, self.proc1.inport)
        self.connectPorts(self.gen.outport, self.proc2.inport, trans2)
