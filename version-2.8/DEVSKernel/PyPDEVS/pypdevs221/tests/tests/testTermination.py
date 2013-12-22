from testutils import *

class TestTermination(unittest.TestCase):
    # Tests the externalInput function, which takes messages of the form:
    #   [[time, age], content, anti-message, UUID, color]
    def setUp(self):
        self.sim = basicSim()
        self.msg = basicMsg()

    def tearDown(self):
        self.sim.runGVT = False

    def test_check_global(self):
        # If check returns True, it means that we should stop
        # This is for basic situations without inputScheduler
        self.sim.termination_time = (5, float('inf'))
        self.sim.model = Generator()
        self.assertFalse(self.sim.check())
        self.sim.model.timeNext = (5, 1)
        self.assertFalse(self.sim.check())
        self.sim.model.timeNext = (5, 2)
        self.assertFalse(self.sim.check())
        self.sim.model.timeNext = (6, 1)
        self.assertTrue(self.sim.check())
        self.sim.model.timeNext = (float('inf'), 1)
        self.assertTrue(self.sim.check())

        # Now there is an inputScheduler
        msg = NetworkMessage(self.msg.timestamp, self.msg.content, self.msg.uuid, self.msg.color, self.msg.destination)
        msg2 = NetworkMessage(self.msg.timestamp, self.msg.content, self.msg.uuid, self.msg.color, self.msg.destination)

        self.sim.inputScheduler.heap = [msg]
        self.sim.model.timeNext = (float('inf'), 1)

        # Message in inputScheduler must still be sent
        msg.timestamp = (3, 1)
        self.assertFalse(self.sim.check())

        # Message in inputScheduler is after the termination time
        msg.timestamp = (6, 1)
        self.assertTrue(self.sim.check())

        # Messages in inputScheduler, only last one must still be sent
        msg.timestamp = (2, 1)
        msg2.timestamp = (4, 1)
        self.sim.prevtime = (3, 1)
        self.sim.inputScheduler.heap.append(msg2)
        self.assertFalse(self.sim.check())

        msg.timestamp = (6, 1)
        msg2.timestamp = (7, 1)
        self.sim.prevtime = (3, 1)
        self.sim.inputScheduler.heap.append(msg2)
        self.assertTrue(self.sim.check())

        self.sim.model.timeNext = (3, 1)
        msg.timestamp = (2, 1)
        msg2.timestamp = (7, 1)
        self.sim.prevtime = (2, 4)
        self.sim.inputScheduler.heap.append(msg2)
        self.assertFalse(self.sim.check())
