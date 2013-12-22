from testutils import *

class TestTestUtils(unittest.TestCase):
    def test_testutils_equalStateVectors(self):
        state1 = [1, 2, 3]
        state2 = [1, 4, 3]
        state3 = [1, 2, 4]
        state4 = [1, 4, 3]
        state5 = [2, 2, 4]
        a = []
        b = [state1]
        self.assertFalse(equalStateVectors(a, b))
        a = [state2]
        self.assertFalse(equalStateVectors(a, b))
        a = [state1, state2]
        self.assertFalse(equalStateVectors(a, b))
        b = [state2, state1]
        self.assertFalse(equalStateVectors(a, b))
        # Third field doesn't matter
        a = [state1]
        b = [state3]
        self.assertTrue(equalStateVectors(a, b))
        a = [state3, state1]
        b = [state1, state3]
        self.assertTrue(equalStateVectors(a, b))
        # Even though it doesn't matter, length must be equal
        a = [state1, state3]
        b = [state1, state1, state1]
        self.assertFalse(equalStateVectors(a, b))
        a = [state1]
        b = [state5]
        self.assertFalse(equalStateVectors(a, b))
