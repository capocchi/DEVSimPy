from testutils import *
from basesimulator import BaseSimulator

class TestWait(unittest.TestCase):
    def setUp(self):
        self.sim = basicSim()

    def tearDown(self):
        self.sim.runGVT = False

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
        self.sim.controlmsg = [0, 0, {0: 0}]
        self.checkWait(finish=True)

        self.sim.V = [{0: -3}, {}]
        self.sim.controlmsg = [0, 0, {0: 0}]
        self.checkWait(finish=True)

        self.sim.V = [{0: -3}, {}]
        self.sim.controlmsg = [0, 0, {0: -4}]
        self.checkWait(finish=True)

        self.sim.V = [{0: 0}, {}]
        self.sim.controlmsg = [0, 0, {0: -5}]
        self.checkWait(finish=True)

        self.sim.V = [{0: 3}, {}]
        self.sim.controlmsg = [0, 0, {0: -3}]
        self.checkWait(finish=True)

        self.sim.V = [{0: -3}, {}]
        self.sim.controlmsg = [0, 0, {0: 3}]
        self.checkWait(finish=True)

        self.sim.V = [{0: 1}, {}]
        self.sim.controlmsg = [0, 0, {0: 0}]
        self.checkWait(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=True)

        self.sim.V = [{0: 0}, {}]
        self.sim.controlmsg = [0, 0, {0: 1}]
        self.checkWait(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=True)

        self.sim.V = [{0: 3}, {}]
        self.sim.controlmsg = [0, 0, {0: -2}]
        self.checkWait(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=True)

        # Should stop at exactly the correct time
        self.sim.V = [{0: -3}, {}]
        self.sim.controlmsg = [0, 0, {0: 6}]
        self.checkWait(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=True)

        # Do multiple receives at once
        self.sim.V = [{0: -3}, {}]
        self.sim.controlmsg = [0, 0, {0: 6}]
        self.checkWait(finish=False)
        self.sim.notifyReceive(False)
        self.sim.notifyReceive(False)
        self.sim.notifyReceive(False)
        self.checkWaitStop(finish=True)
