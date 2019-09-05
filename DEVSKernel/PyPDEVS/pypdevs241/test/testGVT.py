# Copyright 2014 Modelling, Simulation and Design Lab (MSDL) at 
# McGill University and the University of Antwerp (http://msdl.cs.mcgill.ca/)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .testutils import *
from pypdevs.basesimulator import BaseSimulator
from pypdevs.util import DEVSException
from pypdevs.DEVS import RootDEVS

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
        self.sim.run_gvt = False

    def test_GVT_notify_receive(self):
        self.assertTrue(self.sim.V == [{}, {}, {}, {}])

        self.sim.notifyReceive(0)
        self.assertTrue(self.sim.V == [{0: -1}, {}, {}, {}])

        self.sim.notifyReceive(0)
        self.sim.notifyReceive(0)
        self.sim.notifyReceive(0)
        self.sim.notifyReceive(0)
        self.assertTrue(self.sim.V == [{0: -5}, {}, {}, {}])

        self.sim.notifyReceive(1)
        self.assertTrue(self.sim.V == [{0: -5}, {0: -1}, {}, {}])

        self.sim.notifyReceive(1)
        self.sim.notifyReceive(1)
        self.sim.notifyReceive(1)
        self.assertTrue(self.sim.V == [{0: -5}, {0:-4}, {}, {}])

        self.sim.notifyReceive(0)
        self.sim.notifyReceive(1)
        self.sim.notifyReceive(3)
        self.sim.notifyReceive(2)
        self.sim.notifyReceive(3)
        self.sim.notifyReceive(3)
        self.sim.notifyReceive(0)
        self.assertTrue(self.sim.V == [{0: -7}, {0: -5}, {0: -1}, {0: -3}])
        self.sim.V = [{0: 10, 1: 5}, {}, {}, {}]

        self.sim.notifyReceive(0)
        self.assertTrue(self.sim.V == [{0: 9, 1: 5}, {}, {}, {}])

    def test_GVT_notify_send(self):
        self.assertTrue(self.sim.V == [{}, {}, {}, {}])
        self.assertTrue(self.sim.Tmin == float('inf'))

        self.sim.notifySend(1, 1, 0)
        self.assertTrue(self.sim.V == [{1: 1}, {}, {}, {}])
        self.assertTrue(self.sim.Tmin == float('inf'))

        self.sim.notifySend(1, 1, 0)
        self.assertTrue(self.sim.V == [{1: 2}, {}, {}, {}])
        self.assertTrue(self.sim.Tmin == float('inf'))

        self.sim.notifySend(2, 1, 0)
        self.assertTrue(self.sim.V == [{1: 2, 2: 1}, {}, {}, {}])
        self.assertTrue(self.sim.Tmin == float('inf'))

        self.sim.notifySend(2, 3, 0)
        self.sim.notifySend(1, 2, 0)
        self.sim.notifySend(2, 1, 0)
        self.assertTrue(self.sim.V == [{1: 3, 2: 3}, {}, {}, {}])
        self.assertTrue(self.sim.Tmin == float('inf'))

        self.sim.notifySend(1, 9, 1)
        self.assertTrue(self.sim.V == [{1: 3, 2: 3}, {1: 1}, {}, {}])
        self.assertTrue(self.sim.Tmin == 9)

        self.sim.notifySend(1, 6, 1)
        self.assertTrue(self.sim.V == [{1: 3, 2: 3}, {1: 2}, {}, {}])
        self.assertTrue(self.sim.Tmin == 6)

        self.sim.notifySend(2, 5, 1)
        self.assertTrue(self.sim.V == [{1: 3, 2: 3}, {1: 2, 2: 1}, {}, {}])
        self.assertTrue(self.sim.Tmin == 5)

        self.sim.notifySend(1, 8, 1)
        self.assertTrue(self.sim.V == [{1: 3, 2: 3}, {1: 3, 2: 1}, {}, {}])
        self.assertTrue(self.sim.Tmin == 5)

        self.sim.notifySend(2, 5, 1)
        self.sim.notifySend(2, 1, 0)
        self.sim.notifySend(2, 1, 0)
        self.sim.notifySend(2, 6, 1)
        self.assertTrue(self.sim.V == [{1: 3, 2: 5}, {1: 3, 2: 3}, {}, {}])
        self.assertTrue(self.sim.Tmin == 5)

    def test_setGVT(self):
        self.sim.gvt = 0
        models = [Generator()]
        from pypdevs.statesavers import CopyState
        models[0].old_states = [CopyState((0, 1), (2, 1), None, 0, {}, 0), CopyState((2, 1), (6, 1), None, 0, {}, 0)]
        self.sim.model = StubRootDEVS(models, 0)
        # Prevent a loop
        self.sim.next_LP = self.sim
        self.assertTrue(self.sim.gvt == 0)
        self.sim.setGVT(5, [], False)
        self.assertTrue(self.sim.gvt == 5)
        # Try to set to a time before the current GVT
        try:
            self.sim.setGVT(1, [], False)
            self.fail()
        except DEVSException:
            pass
        # GVT shouldn't have changed
        self.assertTrue(self.sim.gvt == 5)
