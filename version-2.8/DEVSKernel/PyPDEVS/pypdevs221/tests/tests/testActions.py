from testutils import *
from util import DEVSException

class TestActions(unittest.TestCase):
    # Tests the externalInput function, which takes messages of the form:
    #   [[time, age], content, anti-message, UUID, color]
    def setUp(self):
        self.sim = basicSim()

    def tearDown(self):
        self.sim.runGVT = False

    def test_actions_delayed_action_normal(self):
        self.sim.GVT = 0
        plist = []
        plist.append([(1, 1), "model1", "ABC"])
        plist.append([(2, 1), "model3", "ABC"])
        plist.append([(3, 1), "model1", "ABE"])
        plist.append([(2, 6), "model1", "DBC"])
        plist.append([(0, 1), "model2", "ABZ"])
        plist.append([(7, 1), "model1", "A5C"])
        # Messages should not be sorted in the actions list
        for i in plist:
            self.sim.delayedAction(i[0], i[1], i[2])

        self.assertTrue(self.sim.actions == plist)

    def test_actions_text_revertion(self):
        self.sim.GVT = 1
        plist = []
        plist.append([(1, 1), "model1", "ABC"])
        plist.append([(2, 1), "model3", "ABC"])
        plist.append([(3, 1), "model1", "ABE"])
        plist.append([(2, 6), "model1", "DBC"])
        # This one should be filtered out
        plist.append([(0, 1), "model2", "ABZ"])
        plist.append([(7, 1), "model1", "A5C"])
        # Messages should not be sorted in the toPrint list
        rlist = []
        for i in plist:
            if i[0][0] < self.sim.GVT:
                try:
                    self.sim.delayedAction(i[0], i[1], i[2])
                    # Should throw an exception
                    self.fail() #pragma: nocover
                except DEVSException:
                    # OK
                    pass
            else:
                # This one should work fine
                self.sim.delayedAction(i[0], i[1], i[2])
                rlist.append(i)

        self.assertTrue(self.sim.actions == rlist)

    def test_actions_perform(self):
        self.sim.GVT = 0
        plist = []
        # Should not need to be added in correct order!
        # Those that should not be executed contain faulty code 
        #  (a division by zero)
        plist.append([(0, 0), "model1", "pass"])
        plist.append([(3, 1), "model2", "pass"])
        plist.append([(2, 1), "model3", "pass"])
        plist.append([(2, 1), "model1", "pass"])
        plist.append([(6, 4), "model2", "1/0"])
        plist.append([(4, 3), "model1", "pass"])
        plist.append([(8, 2), "model1", "1/0"])
        plist.append([(9, 9), "model3", "1/0"])

        plist2 = []
        # Should be in this exact order, otherwise this part was sorted too
        plist2.append(plist[4])
        plist2.append(plist[6])
        plist2.append(plist[7])

        self.sim.actions = list(plist)
        # Perform all actions up to time 5
        try:
            self.sim.performActions(5)
        except ZeroDivisionError: #pragma: nocover
            # executed a bad piece of code!
            self.fail("Executed too much code") 

        self.assertTrue(self.sim.actions == plist2)

        # Now execute a command that should crash, to make sure that 
        #  this code is executed and not just deleted
        try:
            self.sim.performActions(7)
            self.fail("Didn't execute desired code") #pragma: nocover
        except ZeroDivisionError:
            pass

    def test_actions_remove_revert(self):
        self.sim.GVT = 5
        plist = []
        # Should not need to be added in correct order!
        plist.append([(0, 0), "model1", "ABC"])
        plist.append([(3, 1), "model2", "ABC"])
        plist.append([(2, 1), "model3", "ABC"])
        plist.append([(2, 1), "model1", "ABC"])
        plist.append([(8, 4), "model2", "ABC"])
        plist.append([(4, 3), "model1", "ABC"])
        plist.append([(8, 2), "model1", "ABC"])
        plist.append([(9, 9), "model3", "ABC"])
        # Make a copy...
        self.sim.actions = list(plist)

        self.sim.removeActions("model1", (9, 1))
        # No messages from this time on
        self.assertTrue(self.sim.actions == plist)

        try:
            self.sim.removeActions("model1", (4, 3))
            # Revertion from before the GVT, should be denied!
            self.fail() #pragma: nocover
        except DEVSException:
            pass
        # Nothing should have happend to the print list
        self.assertTrue(self.sim.actions == plist)

        self.sim.removeActions("model2", (5,1))
        # One message from model2 should be removed, as it is just at the GVT
        clist = []
        clist.append([(0, 0), "model1", "ABC"])
        clist.append([(3, 1), "model2", "ABC"])
        clist.append([(2, 1), "model3", "ABC"])
        clist.append([(2, 1), "model1", "ABC"])
        clist.append([(4, 3), "model1", "ABC"])
        clist.append([(8, 2), "model1", "ABC"])
        clist.append([(9, 9), "model3", "ABC"])

        try:
            self.sim.removeActions("QDFQF", (0,0))
            # Should still cause an error, even if there is nothing < GVT
            self.fail() #pragma: nocover
        except DEVSException:
            pass
        self.assertTrue(self.sim.actions == clist)
    def test_actions_remove_normal(self):
        self.sim.GVT = 0
        plist = []
        # Should not need to be added in correct order!
        plist.append([(0, 0), "model1", "ABC"])
        plist.append([(3, 1), "model2", "ABC"])
        plist.append([(2, 1), "model3", "ABC"])
        plist.append([(2, 1), "model1", "ABC"])
        plist.append([(8, 4), "model2", "ABC"])
        plist.append([(4, 3), "model1", "ABC"])
        plist.append([(8, 2), "model1", "ABC"])
        plist.append([(9, 9), "model3", "ABC"])
        # Make a copy...
        self.sim.actions = list(plist)

        self.sim.removeActions("model1", (9, 1))
        # No messages from this time on
        self.assertTrue(self.sim.actions == plist)

        self.sim.removeActions("model1", (4, 3))
        # The message at [4,3] itself should also be removed
        clist = []
        clist.append([(0, 0), "model1", "ABC"])
        clist.append([(3, 1), "model2", "ABC"])
        clist.append([(2, 1), "model3", "ABC"])
        clist.append([(2, 1), "model1", "ABC"])
        clist.append([(8, 4), "model2", "ABC"])
        clist.append([(9, 9), "model3", "ABC"])
        self.assertTrue(self.sim.actions == clist)

        self.sim.removeActions("model2", (0,0))
        # All messages from model2 should be removed
        clist = []
        clist.append([(0, 0), "model1", "ABC"])
        clist.append([(2, 1), "model3", "ABC"])
        clist.append([(2, 1), "model1", "ABC"])
        clist.append([(9, 9), "model3", "ABC"])
        self.assertTrue(self.sim.actions == clist)

        self.sim.removeActions("QDFQF", (0,0))
        # Shouldn't make a difference as the model does not exist
        self.assertTrue(self.sim.actions == clist)
