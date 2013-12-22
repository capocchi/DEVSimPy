from testutils import *
import subprocess
import filecmp
import datetime

class TestRealtime(unittest.TestCase):
    def setUp(self):
        setLogger('None', ('localhost', 514), logging.WARN)

    def tearDown(self):
        pass

    def test_local_realtime_thread(self):
        self.assertTrue(runRealtime("realtime_thread", 35))

    def test_local_realtime_tk(self):
        self.assertTrue(runRealtime("realtime_tk", 35))

    def test_local_realtime_loop(self):
        self.assertTrue(runRealtime("realtime_loop", 35))

    def test_local_realtime_thread_upscale(self):
        self.assertTrue(runRealtime("realtime_thread_2.0", 70))

    def test_local_realtime_tk_upscale(self):
        self.assertTrue(runRealtime("realtime_tk_2.0", 70))

    def test_local_realtime_loop_upscale(self):
        self.assertTrue(runRealtime("realtime_loop_2.0", 70))

    def test_local_realtime_thread_downscale(self):
        self.assertTrue(runRealtime("realtime_thread_0.5", 17))

    def test_local_realtime_tk_downscale(self):
        self.assertTrue(runRealtime("realtime_tk_0.5", 17))

    def test_local_realtime_loop_downscale(self):
        self.assertTrue(runRealtime("realtime_loop_0.5", 17))

def runRealtime(name, reqtime):
    before = datetime.datetime.now()
    try:
        runLocal(name)
    except OSError:
        pass
    after = datetime.datetime.now()
    # Possibly only a slight timing difference, which is allowable
    f1 = open("output/realtime", 'r')
    f2 = open("expected/realtime", 'r')
    for l1, l2 in zip(f1, f2):
        if l1 != l2:
            # Check that at most 1 character is different
            diffs = 0
            for c1, c2 in zip(l1, l2):
                if c1 != c2:
                    diffs += 1
            if diffs > 1:
                return False
            # It seems that the difference wasn't that big after all, just continue
    # Seems to be done, check for time passed
    diff = after - before
    return reqtime - 1 <= diff.seconds <= reqtime + 1

def runLocal(name):
    outfile = "output/" + str(name)
    removeFile(outfile)
    import subprocess
    try:
        proc = subprocess.Popen("python regression/experiment.py " + str(name) + "_local >> /dev/null", shell=True)
        proc.wait()
    except:
        import sys
        print(sys.exc_info()[0])
        import traceback
        traceback.print_tb(sys.exc_info()[2])
        proc.terminate()
        # Prevent zombie
        del proc
        print("Exception received :(")
        return False

    if not filecmp.cmp(outfile, "expected/" + str(name)):
        return False
    return True
