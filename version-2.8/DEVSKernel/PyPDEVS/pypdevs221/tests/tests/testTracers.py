from testutils import *
from tracers import *
from tracerVCD import VCDRecord
import os

class StubTracers(Tracers):
    def __init__(self):
        self.called = []
        self.cell = False

    def verboseInternal(self, model):
        self.called.append(("verboseInternal", model))

    def xmlInternal(self, model):
        self.called.append(("xmlInternal", model))

    def vcdInternal(self, model):
        self.called.append(("vcdInternal", model))

    def verboseExternal(self, model):
        self.called.append(("verboseExternal", model))

    def xmlExternal(self, model):
        self.called.append(("xmlExternal", model))

    def vcdExternal(self, model):
        self.called.append(("vcdExternal", model))

    def verboseInit(self, model):
        self.called.append(("verboseInit", model))

    def xmlInit(self, model):
        self.called.append(("xmlInit", model))

    def vcdInit(self, model):
        self.called.append(("vcdInit", model))

    def verboseConfluent(self, model):
        self.called.append(("verboseConfluent", model))

    def xmlConfluent(self, model):
        self.called.append(("xmlConfluent", model))

    def vcdConfluent(self, model):
        self.called.append(("vcdConfluent", model))

    def initXML(self):
        self.called.append("initXML")

    def initVCD(self):
        self.called.append("initVCD")

class TestTracers(unittest.TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        try:
            os.remove("devstrace.xml")
        except OSError:
            pass
        try:
            os.remove("devstrace.vcd")
        except OSError:
            pass
        try:
            os.remove("devstrace.out")
        except OSError:
            pass

    def test_VCDRecord(self):
        a = VCDRecord(1, "abc.def", "inport")
        self.assertTrue(a.modelName == "abc.def")
        self.assertTrue(a.bitSize == None)
        self.assertTrue(a.identifier == 1)
        self.assertTrue(a.portName == "inport")

    def test_tracers_internal(self):
        model = Generator()

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = False
        tracer.tracesInternal(model)
        self.assertTrue(tracer.called.count(("verboseInternal", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlInternal", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdInternal", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = True
        tracer.xml = False
        tracer.vcd = False
        tracer.tracesInternal(model)
        self.assertTrue(tracer.called.count(("verboseInternal", model)) == 1)
        self.assertTrue(tracer.called.count(("xmlInternal", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdInternal", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = True
        tracer.vcd = False
        tracer.tracesInternal(model)
        self.assertTrue(tracer.called.count(("verboseInternal", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlInternal", model)) == 1)
        self.assertTrue(tracer.called.count(("vcdInternal", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = True
        tracer.tracesInternal(model)
        self.assertTrue(tracer.called.count(("verboseInternal", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlInternal", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdInternal", model)) == 1)

        tracer = StubTracers()
        tracer.verbose = True
        tracer.xml = True
        tracer.vcd = True
        tracer.tracesInternal(model)
        self.assertTrue(tracer.called.count(("verboseInternal", model)) == 1)
        self.assertTrue(tracer.called.count(("xmlInternal", model)) == 1)
        self.assertTrue(tracer.called.count(("vcdInternal", model)) == 1)

    def test_tracers_init(self):
        model = Generator()

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = False
        tracer.tracesInit(model)
        self.assertTrue(tracer.called.count(("verboseInit", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlInit", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdInit", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = True
        tracer.xml = False
        tracer.vcd = False
        tracer.tracesInit(model)
        self.assertTrue(tracer.called.count(("verboseInit", model)) == 1)
        self.assertTrue(tracer.called.count(("xmlInit", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdInit", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = True
        tracer.vcd = False
        tracer.tracesInit(model)
        self.assertTrue(tracer.called.count(("verboseInit", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlInit", model)) == 1)
        self.assertTrue(tracer.called.count(("vcdInit", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = True
        tracer.tracesInit(model)
        self.assertTrue(tracer.called.count(("verboseInit", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlInit", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdInit", model)) == 1)

        tracer = StubTracers()
        tracer.verbose = True
        tracer.xml = True
        tracer.vcd = True
        tracer.tracesInit(model)
        self.assertTrue(tracer.called.count(("verboseInit", model)) == 1)
        self.assertTrue(tracer.called.count(("xmlInit", model)) == 1)
        self.assertTrue(tracer.called.count(("vcdInit", model)) == 1)

    def test_tracers_external(self):
        model = Generator()

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = False
        tracer.tracesExternal(model)
        self.assertTrue(tracer.called.count(("verboseExternal", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlExternal", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdExternal", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = True
        tracer.xml = False
        tracer.vcd = False
        tracer.tracesExternal(model)
        self.assertTrue(tracer.called.count(("verboseExternal", model)) == 1)
        self.assertTrue(tracer.called.count(("xmlExternal", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdExternal", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = True
        tracer.vcd = False
        tracer.tracesExternal(model)
        self.assertTrue(tracer.called.count(("verboseExternal", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlExternal", model)) == 1)
        self.assertTrue(tracer.called.count(("vcdExternal", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = True
        tracer.tracesExternal(model)
        self.assertTrue(tracer.called.count(("verboseExternal", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlExternal", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdExternal", model)) == 1)

        tracer = StubTracers()
        tracer.verbose = True
        tracer.xml = True
        tracer.vcd = True
        tracer.tracesExternal(model)
        self.assertTrue(tracer.called.count(("verboseExternal", model)) == 1)
        self.assertTrue(tracer.called.count(("xmlExternal", model)) == 1)
        self.assertTrue(tracer.called.count(("vcdExternal", model)) == 1)

    def test_tracers_confluent(self):
        model = Generator()

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = False
        tracer.tracesConfluent(model)
        self.assertTrue(tracer.called.count(("verboseConfluent", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlConfluent", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdConfluent", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = True
        tracer.xml = False
        tracer.vcd = False
        tracer.tracesConfluent(model)
        self.assertTrue(tracer.called.count(("verboseConfluent", model)) == 1)
        self.assertTrue(tracer.called.count(("xmlConfluent", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdConfluent", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = True
        tracer.vcd = False
        tracer.tracesConfluent(model)
        self.assertTrue(tracer.called.count(("verboseConfluent", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlConfluent", model)) == 1)
        self.assertTrue(tracer.called.count(("vcdConfluent", model)) == 0)

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = True
        tracer.tracesConfluent(model)
        self.assertTrue(tracer.called.count(("verboseConfluent", model)) == 0)
        self.assertTrue(tracer.called.count(("xmlConfluent", model)) == 0)
        self.assertTrue(tracer.called.count(("vcdConfluent", model)) == 1)

        tracer = StubTracers()
        tracer.verbose = True
        tracer.xml = True
        tracer.vcd = True
        tracer.tracesConfluent(model)
        self.assertTrue(tracer.called.count(("verboseConfluent", model)) == 1)
        self.assertTrue(tracer.called.count(("xmlConfluent", model)) == 1)
        self.assertTrue(tracer.called.count(("vcdConfluent", model)) == 1)

    def test_initXML(self):
        tracer = Tracers()
        tracer.setXML(True, "devstrace.xml")
        tracer.initXML()
        tracer.xml_file.close()
        f = open("devstrace.xml", 'r')
        c = 0
        for l in f:
            if c == 0: e = '<?xml version="1.0"?>'
            elif c == 1: e = '<trace>'
            c += 1
            e = e + "\n"
            self.assertTrue(e == l)

    def test_startTracers(self):
        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = False
        tracer.startTracers()
        self.assertTrue(tracer.called.count("initXML") == 0)
        self.assertTrue(tracer.called.count("initVCD") == 0)

        tracer = StubTracers()
        tracer.verbose = True
        tracer.xml = True
        tracer.vcd = True
        tracer.startTracers()
        self.assertTrue(tracer.called.count("initXML") == 1)
        self.assertTrue(tracer.called.count("initVCD") == 1)

        tracer = StubTracers()
        tracer.verbose = True
        tracer.xml = False
        tracer.vcd = False
        tracer.startTracers()
        self.assertTrue(tracer.called.count("initXML") == 0)
        self.assertTrue(tracer.called.count("initVCD") == 0)

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = True
        tracer.vcd = False
        tracer.startTracers()
        self.assertTrue(tracer.called.count("initXML") == 1)
        self.assertTrue(tracer.called.count("initVCD") == 0)

        tracer = StubTracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = True
        tracer.startTracers()
        self.assertTrue(tracer.called.count("initXML") == 0)
        self.assertTrue(tracer.called.count("initVCD") == 1)

    def test_stopTracers(self):
        class CheckFlush(object):
            def __init__(self):
                self.flushed = False
            def flush(self):
                self.flushed = True
            def write(self, text):
                pass

        # Just provide some coverage and check that all files get flushed
        tracer = Tracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = False
        tracer.verb_file = CheckFlush()
        tracer.xml_file = CheckFlush()
        tracer.vcd_file = CheckFlush()
        tracer.stopTracers()
        self.assertTrue(tracer.verb_file.flushed == False)
        self.assertTrue(tracer.xml_file.flushed == False)
        self.assertTrue(tracer.vcd_file.flushed == False)

        tracer = Tracers()
        tracer.verbose = True
        tracer.xml = False
        tracer.vcd = False
        tracer.verb_file = CheckFlush()
        tracer.xml_file = CheckFlush()
        tracer.vcd_file = CheckFlush()
        tracer.stopTracers()
        self.assertTrue(tracer.verb_file.flushed == True)
        self.assertTrue(tracer.xml_file.flushed == False)
        self.assertTrue(tracer.vcd_file.flushed == False)

        tracer = Tracers()
        tracer.verbose = False
        tracer.xml = True
        tracer.vcd = False
        tracer.verb_file = CheckFlush()
        tracer.xml_file = CheckFlush()
        tracer.vcd_file = CheckFlush()
        tracer.stopTracers()
        self.assertTrue(tracer.verb_file.flushed == False)
        self.assertTrue(tracer.xml_file.flushed == True)
        self.assertTrue(tracer.vcd_file.flushed == False)

        tracer = Tracers()
        tracer.verbose = False
        tracer.xml = False
        tracer.vcd = True
        tracer.verb_file = CheckFlush()
        tracer.xml_file = CheckFlush()
        tracer.vcd_file = CheckFlush()
        tracer.stopTracers()
        self.assertTrue(tracer.verb_file.flushed == False)
        self.assertTrue(tracer.xml_file.flushed == False)
        self.assertTrue(tracer.vcd_file.flushed == True)

        tracer = Tracers()
        tracer.verbose = True
        tracer.xml = True
        tracer.vcd = True
        tracer.verb_file = CheckFlush()
        tracer.xml_file = CheckFlush()
        tracer.vcd_file = CheckFlush()
        tracer.stopTracers()
        self.assertTrue(tracer.verb_file.flushed == True)
        self.assertTrue(tracer.xml_file.flushed == True)
        self.assertTrue(tracer.vcd_file.flushed == True)
