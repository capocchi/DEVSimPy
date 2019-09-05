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
from pypdevs.schedulers.schedulerAH import SchedulerAH

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.models = []
        for i in range(10):
            ne = Generator()
            ne.model_id = i
            ne.time_next = (1, 1)
            self.models.append(ne)
        for i in range(10):
            ne = Processor()
            ne.model_id = i + 10
            ne.time_next = (float('inf'), 1)
            self.models.append(ne)
        self.scheduler = SchedulerAH(self.models, 1e-9, len(self.models))

    def tearDown(self):
        pass

    def test_scheduler_schedule(self):
        # Only 10, since the Processors should not get scheduled 
        #  due to their time_next
        self.assertTrue(len(self.scheduler.heap) == 10)

    def test_scheduler_unschedule(self):
        self.assertTrue(len(self.scheduler.heap) == 10)

        for i in self.models:
            self.scheduler.unschedule(i)
        # Heap should have the same length, as they became invalid
        self.assertTrue(len(self.scheduler.heap) == 10)
        # Clean up
        self.scheduler.cleanFirst()
        self.assertTrue(len(self.scheduler.heap) == 0)

        for i in self.models:
            self.scheduler.schedule(i)

        self.scheduler.unschedule(self.models[5])
        self.assertTrue(len(self.scheduler.heap) == 10)

    def test_scheduler_get_imminent(self):
        self.assertTrue(len(self.scheduler.heap) == 10)

        self.scheduler.unschedule(self.models[2])
        self.scheduler.unschedule(self.models[4])
        self.scheduler.unschedule(self.models[0])
        self.scheduler.unschedule(self.models[7])
        verifylist = list(self.models[:10])
        verifylist.remove(self.models[0])
        verifylist.remove(self.models[2])
        verifylist.remove(self.models[4])
        verifylist.remove(self.models[7])

        # Heap should have the same length, as they became invalid
        self.assertTrue(len(self.scheduler.heap) == 10)

        res = self.scheduler.getImminent((1, 1))
        self.assertTrue(res == verifylist)

        for i in self.models:
            try:
                self.scheduler.unschedule(i)
            except TypeError:
                # Some are possibly already None
                pass

        # List should be completely empty now
        res = self.scheduler.getImminent((1, 1))
        self.assertTrue(res == [])
