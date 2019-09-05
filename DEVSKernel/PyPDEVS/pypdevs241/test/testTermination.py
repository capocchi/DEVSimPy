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

class TestTermination(unittest.TestCase):
    # Tests the externalInput function, which takes messages of the form:
    #   [[time, age], content, anti-message, UUID, color]
    def setUp(self):
        self.sim = basicSim()
        self.msg = basicMsg()

    def tearDown(self):
        self.sim.run_gvt = False

    def test_check_global(self):
        # If check returns True, it means that we should stop
        # This is for basic situations without input_scheduler
        self.sim.termination_time = (5, float('inf'))
        self.sim.model = Generator()
        self.assertFalse(self.sim.check())
        self.sim.model.time_next = (5, 1)
        self.assertFalse(self.sim.check())
        self.sim.model.time_next = (5, 2)
        self.assertFalse(self.sim.check())
        self.sim.model.time_next = (6, 1)
        self.assertTrue(self.sim.check())
        self.sim.model.time_next = (float('inf'), 1)
        self.assertTrue(self.sim.check())

        # Now there is an input_scheduler
        msg = NetworkMessage(self.msg.timestamp, self.msg.content, self.msg.uuid, self.msg.color, self.msg.destination)
        msg2 = NetworkMessage(self.msg.timestamp, self.msg.content, self.msg.uuid, self.msg.color, self.msg.destination)

        self.sim.input_scheduler.heap = [msg]
        self.sim.model.time_next = (float('inf'), 1)

        # Message in input_scheduler must still be sent
        msg.timestamp = (3, 1)
        self.assertFalse(self.sim.check())

        # Message in input_scheduler is after the termination time
        msg.timestamp = (6, 1)
        self.assertTrue(self.sim.check())

        # Messages in input_scheduler, only last one must still be sent
        msg.timestamp = (2, 1)
        msg2.timestamp = (4, 1)
        self.sim.prevtime = (3, 1)
        self.sim.input_scheduler.heap.append(msg2)
        self.assertFalse(self.sim.check())

        msg.timestamp = (6, 1)
        msg2.timestamp = (7, 1)
        self.sim.prevtime = (3, 1)
        self.sim.input_scheduler.heap.append(msg2)
        self.assertTrue(self.sim.check())

        self.sim.model.time_next = (3, 1)
        msg.timestamp = (2, 1)
        msg2.timestamp = (7, 1)
        self.sim.prevtime = (2, 4)
        self.sim.input_scheduler.heap.append(msg2)
        self.assertFalse(self.sim.check())
