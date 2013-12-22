from testutils import *
from basesimulator import BaseSimulator
from util import DEVSException
from DEVS import RootDEVS

class StubBaseSimulator(BaseSimulator):
    def __init__(self, name):
        BaseSimulator.__init__(self, name, None)
        self.reverted = False

    def receiveControl(self, msg):
        thrd = threading.Thread(target=BaseSimulator.receiveControl, args=[self, msg])
        thrd.start()

class StubRootDEVS(RootDEVS):
    def __init__(self, models, num):
        scheduler = "heapset"
        models[num].model_id = num
        RootDEVS.__init__(self, [models[num]], models, scheduler)

class TestGVT(unittest.TestCase):
    def setUp(self):
        self.sim = basicSim()

    def tearDown(self):
        self.sim.runGVT = False

    def test_GVT_notify_receive(self):
        self.assertTrue(self.sim.V == [{}, {}])

        self.sim.notifyReceive(False)
        self.assertTrue(self.sim.V == [{0: -1}, {}])

        self.sim.notifyReceive(False)
        self.sim.notifyReceive(False)
        self.sim.notifyReceive(False)
        self.sim.notifyReceive(False)
        self.assertTrue(self.sim.V == [{0: -5}, {}])

        self.sim.notifyReceive(True)
        self.assertTrue(self.sim.V == [{0: -5}, {}])

        self.sim.notifyReceive(True)
        self.sim.notifyReceive(True)
        self.sim.notifyReceive(True)
        self.assertTrue(self.sim.V == [{0: -5}, {}])

        self.sim.notifyReceive(False)
        self.sim.notifyReceive(True)
        self.sim.notifyReceive(False)
        self.assertTrue(self.sim.V == [{0: -7}, {}])
        self.sim.V = [{0: 10, 1: 5}, {}]

        self.sim.notifyReceive(False)
        self.assertTrue(self.sim.V == [{0: 9, 1: 5}, {}])

    def test_GVT_notify_send(self):
        self.assertTrue(self.sim.V == [{}, {}])
        self.assertTrue(self.sim.Tmin == float('inf'))

        self.sim.notifySend(1, 1, False)
        self.assertTrue(self.sim.V == [{1: 1}, {}])
        self.assertTrue(self.sim.Tmin == float('inf'))

        self.sim.notifySend(1, 1, False)
        self.assertTrue(self.sim.V == [{1: 2}, {}])
        self.assertTrue(self.sim.Tmin == float('inf'))

        self.sim.notifySend(2, 1, False)
        self.assertTrue(self.sim.V == [{1: 2, 2: 1}, {}])
        self.assertTrue(self.sim.Tmin == float('inf'))

        self.sim.notifySend(2, 3, False)
        self.sim.notifySend(1, 2, False)
        self.sim.notifySend(2, 1, False)
        self.assertTrue(self.sim.V == [{1: 3, 2: 3}, {}])
        self.assertTrue(self.sim.Tmin == float('inf'))

        self.sim.notifySend(1, 9, True)
        self.assertTrue(self.sim.V == [{1: 3, 2: 3}, {}])
        self.assertTrue(self.sim.Tmin == 9)

        self.sim.notifySend(1, 6, True)
        self.assertTrue(self.sim.V == [{1: 3, 2: 3}, {}])
        self.assertTrue(self.sim.Tmin == 6)

        self.sim.notifySend(2, 5, True)
        self.assertTrue(self.sim.V == [{1: 3, 2: 3}, {}])
        self.assertTrue(self.sim.Tmin == 5)

        self.sim.notifySend(1, 8, True)
        self.assertTrue(self.sim.V == [{1: 3, 2: 3}, {}])
        self.assertTrue(self.sim.Tmin == 5)

        self.sim.notifySend(2, 5, True)
        self.sim.notifySend(2, 1, False)
        self.sim.notifySend(2, 1, False)
        self.sim.notifySend(2, 6, True)
        self.assertTrue(self.sim.V == [{1: 3, 2: 5}, {}])
        self.assertTrue(self.sim.Tmin == 5)

    def test_setGVT(self):
        self.sim.GVT = 0
        models = [Generator()]
        from statesavers import CopyState
        models[0].oldStates = [CopyState((0, 1), (2, 1), None, 0, {}, 0), CopyState((2, 1), (6, 1), None, 0, {}, 0)]
        self.sim.model = StubRootDEVS(models, 0)
        # Prevent a loop
        self.sim.nextLP = self.sim
        self.assertTrue(self.sim.GVT == 0)
        self.sim.setGVT(5, [], False)
        self.assertTrue(self.sim.GVT == 5)
        # Try to set to a time before the current GVT
        try:
            self.sim.setGVT(1, [], False)
            self.fail()
        except DEVSException:
            pass
        # GVT shouldn't have changed
        self.assertTrue(self.sim.GVT == 5)
