from testutils import *

class TestReceiveExternal(unittest.TestCase):
    def setUp(self):
        self.sim = basicSim()

    def tearDown(self):
        self.sim.runGVT = False

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
