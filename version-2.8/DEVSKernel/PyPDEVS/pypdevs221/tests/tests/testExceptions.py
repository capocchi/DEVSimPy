from testutils import *
from util import DEVSException
from DEVS import BaseDEVS, AtomicDEVS, CoupledDEVS

class TestExceptions(unittest.TestCase):
    # Tests the externalInput function, which takes messages of the form:
    #   [[time, age], content, anti-message, UUID, color]
    def setUp(self):
        self.sim = basicSim()

    def tearDown(self):
        self.sim.runGVT = False

    def test_DEVS_model_exceptions(self):
        try:
            # Shouldn't allow instantiation of the base model
            junk = BaseDEVS("junk")
            self.fail() #pragma: nocover
        except DEVSException:
            pass
        try:
            # Shouldn't allow instantiation of the base model
            junk = AtomicDEVS("junk")
            self.fail() #pragma: nocover
        except DEVSException:
            pass
        try:
            # Shouldn't allow instantiation of the base model
            junk = CoupledDEVS("junk")
            self.fail() #pragma: nocover
        except DEVSException:
            pass
