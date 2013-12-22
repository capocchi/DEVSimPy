from testutils import *
import subprocess
import filecmp
import datetime

class TestLocal(unittest.TestCase):
    def setUp(self):
        setLogger('None', ('localhost', 514), logging.WARN)

    def tearDown(self):
        pass

    def test_local_normal(self):
        self.assertTrue(runLocal("normal"))

    def test_local_Z(self):
        self.assertTrue(runLocal("z"))

    def test_local_dual(self):
        self.assertTrue(runLocal("dual"))

    def test_local_dualdepth(self):
        self.assertTrue(runLocal("dualdepth"))

    def test_local_dual_mp(self):
        self.assertTrue(runLocal("dual_mp"))

    def test_local_longtime(self):
        self.assertTrue(runLocal("longtime"))

    def test_local_confluent(self):
        self.assertTrue(runLocal("confluent"))

    def test_local_classic(self):
        self.assertTrue(runLocal("classicDEVS"))

    def test_local_classicConnect(self):
        self.assertTrue(runLocal("classicDEVSconnect"))

    def test_local_zeroLookahead(self):
        self.assertTrue(runLocal("zeroLookahead"))

    def test_local_multi(self):
        self.assertTrue(runLocal("multi"))

    def test_local_trace(self):
        removeFile("devstrace.vcd")
        removeFile("devstrace.xml")
        self.assertTrue(runLocal("trace"))
        # Compare XML and VCD trace files too
        if not vcdEqual("devstrace.vcd", "expected/trace.vcd"):
            print("VCD trace comparison did not match")
            self.fail()
        if not filecmp.cmp("devstrace.xml", "expected/trace.xml"):
            print("XML trace comparison did not match")
            self.fail()

    def test_local_stateStop(self):
        self.assertTrue(runLocal("stateStop"))

    def test_local_atomic(self):
        self.assertTrue(runLocal("atomic"))

    def test_local_local(self):
        self.assertTrue(runLocal("local"))

    def test_local_nested(self):
        self.assertTrue(runLocal("nested"))

    def test_local_multiinputs(self):
        self.assertTrue(runLocal("multiinputs"))

    def test_local_doublelayer(self):
        self.assertTrue(runLocal("doublelayer"))

    def test_local_dynamicstructure(self):
        self.assertTrue(runLocal("dynamicstructure"))

    def test_local_random(self):
        self.assertTrue(runLocal("random"))

    def test_local_draw(self):
        removeFile("model.dot")
        self.assertTrue(runLocal("draw"))
        if not filecmp.cmp("model.dot", "expected/local_model.dot"):
            print("Graphviz file did not match")
            self.fail()
        removeFile("model.dot")

    def test_local_reinit(self):
        removeFile("output/reinit1")
        removeFile("output/reinit2")
        removeFile("output/reinit3")
        try:
            runLocal("reinit")
        except OSError:
            # Problem with the comparison of the file that doesn't exist...
            pass
        # Compare the files
        if not filecmp.cmp("output/reinit1", "expected/reinit1") or \
           not filecmp.cmp("output/reinit2", "expected/reinit2") or \
           not filecmp.cmp("output/reinit3", "expected/reinit3"):
            return False
        else:
            return True
    
    def test_local_multisim(self):
        removeFile("output/normal")
        removeFile("output/dualdepth")

        try:
            runLocal("multisim")
        except OSError:
            pass

        if not filecmp.cmp("output/normal", "expected/normal") or \
           not filecmp.cmp("output/dualdepth", "expected/dualdepth"):
            self.fail()

    def test_local_continue(self):
        removeFile("output/run1")
        removeFile("output/run2")

        try:
            runLocal("continue")
        except OSError:
            pass

        if not filecmp.cmp("output/run1", "expected/run1") or \
           not filecmp.cmp("output/run2", "expected/run2"):
            self.fail()

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
