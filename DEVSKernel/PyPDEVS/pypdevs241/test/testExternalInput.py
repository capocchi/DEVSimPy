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
from pypdevs.util import DEVSException

class TestExternalInput(unittest.TestCase):
    def setUp(self):
        self.sim = basicSim()
        self.msg = basicMsg()

    def tearDown(self):
        self.sim.run_gvt = False

    def test_externalInput_antimsg_unpresent(self):
        # Send a non-present anti message
        self.sim.externalInput(self.msg)
        self.assertTrue(self.sim.outputQueue == [])
        self.assertTrue(self.sim.prevtime == (0,1))

    def test_externalInput_antimsg_unpresent_other(self):
        # Send a non-present anti message
        self.sim.filtered = [self.msg.uuid]
        msg2 = NetworkMessage(self.msg.timestamp, self.msg.content, self.msg.uuid, self.msg.color, self.msg.destination)
        msg2.uuid = 11111
        self.sim.externalInput(msg2)
        self.assertTrue(self.sim.outputQueue == [])
        self.assertTrue(self.sim.prevtime == (0,1))

    def test_externalInput_antimsg_unpresent_multi(self):
        # Send a non-present anti message
        self.sim.filtered = [self.msg.uuid, self.msg.uuid]
        self.sim.externalInput(self.msg)
        # This message should now get filtered
        self.assertTrue(self.sim.outputQueue == [])
        self.assertTrue(self.sim.prevtime == (0,1))

    def test_externalInput_normal(self):
        self.msg.timestamp = (1, 2)
        self.sim.prevtime = (1, 1)

        self.sim.externalInput(self.msg)

        self.assertTrue(self.sim.outputQueue == [])
        self.assertTrue(self.sim.prevtime == (1, 1))

    def test_externalInput_revert(self):
        self.msg.timestamp = (1, 1)
        self.sim.prevtime = (10, 1)
        self.sim.model = Generator()
        self.sim.model.local_model_ids = set([0, 1])
        self.sim.model.rootsim = self.sim

        self.sim.externalInput(self.msg)

        self.assertTrue(self.sim.reverted)
