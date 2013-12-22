import unittest
import subprocess
import os

from tests.testMessageScheduler import TestMessageScheduler
from tests.testScheduler import TestScheduler
from tests.testActions import TestActions
from tests.testHelpers import TestHelpers
from tests.testGVT import TestGVT
from tests.testWait import TestWait
from tests.testExceptions import TestExceptions
from tests.testMPI import TestMPI
from tests.testLocal import TestLocal
from tests.testRealtime import TestRealtime
from tests.testTermination import TestTermination
from tests.testTestUtils import TestTestUtils
from tests.testLogger import TestLogger

if __name__ == '__main__':
    import stacktracer
    stacktracer.trace_start("trace.html",interval=5,auto=True) # Set auto flag to always update file!

    # Do general setup of all servers
    runMPI = True
    try:
        import mpi4py
    except ImportError:
        runMPI = False

    # Run the tests
    if runMPI:
        mpi = unittest.TestLoader().loadTestsFromTestCase(TestMPI)
    local = unittest.TestLoader().loadTestsFromTestCase(TestLocal)
    actions = unittest.TestLoader().loadTestsFromTestCase(TestActions)
    termination = unittest.TestLoader().loadTestsFromTestCase(TestTermination)
    gvt = unittest.TestLoader().loadTestsFromTestCase(TestGVT)
    exceptions = unittest.TestLoader().loadTestsFromTestCase(TestExceptions)
    wait = unittest.TestLoader().loadTestsFromTestCase(TestWait)
    helpers = unittest.TestLoader().loadTestsFromTestCase(TestHelpers)
    scheduler = unittest.TestLoader().loadTestsFromTestCase(TestScheduler)
    mscheduler = unittest.TestLoader().loadTestsFromTestCase(TestMessageScheduler)
    testutils = unittest.TestLoader().loadTestsFromTestCase(TestTestUtils)
    logger = unittest.TestLoader().loadTestsFromTestCase(TestLogger)
    realtime = unittest.TestLoader().loadTestsFromTestCase(TestRealtime)

    allTests = unittest.TestSuite()
    allTests.addTest(testutils)
    allTests.addTest(actions)
    allTests.addTest(helpers)
    allTests.addTest(gvt)
    allTests.addTest(termination)
    allTests.addTest(exceptions)
    allTests.addTest(wait)
    allTests.addTest(scheduler)
    allTests.addTest(logger)
    allTests.addTest(local)
    #allTests.addTest(realtime)
    if runMPI:
        allTests.addTest(mpi)
        pass
    unittest.TextTestRunner(verbosity=2).run(allTests)

    if not runMPI:
        print("mpi4py could not be found and these tests were skipped")
