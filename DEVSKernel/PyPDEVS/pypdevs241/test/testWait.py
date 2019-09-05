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

class TestWait(unittest.TestCase):
    def setUp(self):
        self.sim = basicSim()

    def tearDown(self):
        self.sim.run_gvt = False

    def checkWait(self, finish):
        self.checkWaitStart()
        self.checkWaitStop(finish)

    def checkWaitStart(self):
        # A thread, otherwise the state of the lock cannot be checked
        # Though this is somewhat more difficult to terminate...
        self.proc = threading.Thread(target=BaseSimulator.waitUntilOK, 
                                     args=[self.sim, 0])
        self.proc.start()

    def checkWaitStop(self, finish=True):
        # Give it not too much time to finish
        self.proc.join(0.1)

        # Still running, but shouldn't finish --> OK
        if self.proc.is_alive() and not finish:
            return

        # Still running, but should finish --> NOK
        elif self.proc.is_alive() and finish: #pragma: nocover
            # Force thread shutdown
            self.sim.V[0] = float('inf')
            self.sim.Vchange.set()
            self.fail("Thread should finish, but was not finished")

        # No longer running, and should finish --> OK
        elif not self.proc.is_alive() and finish:
            return

        # No longer running, but should not finish --> NOK
        elif not self.proc.is_alive() and not finish: #pragma: nocover
            self.fail("Thread should keep running, but has finished")

    def test_GVT_wait(self):
        # Run a seperate thread for the waiting, 
        #  after each modification, we just check wheter it is still live
        self.sim.Vlock.acquire()
        self.sim.V = [{0: 0}, {}]
        self.sim.control_msg = [0, 0, {0: 0}]
        self.checkWait(finish=True)

        self.sim.V = [{0: -3}, {}]
        self.sim.control_msg = [0, 0, {0: 0}]
        self.checkWait(finish=True)

        self.sim.V = [{0: -3}, {}]
        self.sim.control_msg = [0, 0, {0: -4}]
        self.checkWait(finish=True)

        self.sim.V = [{0: 0}, {}]
        self.sim.control_msg = [0, 0, {0: -5}]
        self.checkWait(finish=True)

        self.sim.V = [{0: 3}, {}]
        self.sim.control_msg = [0, 0, {0: -3}]
        self.checkWait(finish=True)

        self.sim.V = [{0: -3}, {}]
        self.sim.control_msg = [0, 0, {0: 3}]
        self.checkWait(finish=True)

        self.sim.V = [{0: 1}, {}]
        self.sim.control_msg = [0, 0, {0: 0}]
        self.checkWait(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=True)

        self.sim.V = [{0: 0}, {}]
        self.sim.control_msg = [0, 0, {0: 1}]
        self.checkWait(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=True)

        self.sim.V = [{0: 3}, {}]
        self.sim.control_msg = [0, 0, {0: -2}]
        self.checkWait(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=True)

        # Should stop at exactly the correct time
        self.sim.V = [{0: -3}, {}]
        self.sim.control_msg = [0, 0, {0: 6}]
        self.checkWait(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=True)

        # Do multiple receives at once
        self.sim.V = [{0: -3}, {}]
        self.sim.control_msg = [0, 0, {0: 6}]
        self.checkWait(finish=False)
        self.sim.notifyReceive(False)
        self.sim.notifyReceive(False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=True)
