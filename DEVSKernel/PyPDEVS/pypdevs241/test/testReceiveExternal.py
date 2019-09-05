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

class TestReceiveExternal(unittest.TestCase):
    def setUp(self):
        self.sim = basicSim()

    def tearDown(self):
        self.sim.run_gvt = False

    def test_receiveExternal(self):
        self.assertTrue(self.sim.inqueue == [])

        # Basic situation, inqueue empty
        msg = NetworkMessage((2, 1), {}, 1234, False, 0)
        self.sim.receiveExternal(msg)
        self.assertTrue(self.sim.inqueue == [msg])

        # Add another message, appended at the end
        msg2 = NetworkMessage((3, 2), {}, 5234, False, 0)
        self.sim.receiveExternal(msg2)
        self.assertTrue(self.sim.inqueue == [msg, msg2])

        # Append another message, not in sorted order
        msg3 = NetworkMessage((1, 1), {}, 5264, False, 0)
        self.sim.receiveExternal(msg3)
        self.assertTrue(self.sim.inqueue == [msg, msg2, msg3])
