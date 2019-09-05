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
import subprocess
import filecmp
import time

class TestMPI(unittest.TestCase):
    def setUp(self):
        setLogger('None', ('localhost', 514), logging.WARN)

    def tearDown(self):
        pass

    def test_MPI_normal(self):
        self.assertTrue(runMPI("normal"))

    def test_MPI_z(self):
        self.assertTrue(runMPI("z"))

    def test_MPI_dual(self):
        self.assertTrue(runMPI("dual"))

    def test_MPI_dualdepth(self):
        self.assertTrue(runMPI("dualdepth"))

    def test_MPI_dual_mp(self):
        self.assertTrue(runMPI("dual_mp"))

    def test_MPI_longtime(self):
        self.assertTrue(runMPI("longtime"))

    def test_MPI_relocation(self):
        self.assertTrue(runMPI("relocation"))

    def test_MPI_confluent(self):
        self.assertTrue(runMPI("confluent"))

    def test_MPI_zeroLookahead(self):
        self.assertTrue(runMPI("zeroLookahead"))

    def test_MPI_autoAllocate(self):
        self.assertTrue(runMPI("auto_allocate"))

    def test_MPI_multi(self):
        self.assertTrue(runMPI("multi"))

    def test_MPI_stateStop(self):
        self.assertTrue(runMPI("stateStop"))

    def test_MPI_remoteDC(self):
        self.assertTrue(runMPI("remotedc"))

    def test_MPI_remoteDC_long(self):
        self.assertTrue(runMPI("remotedc_long"))

    def test_MPI_local(self):
        self.assertTrue(runMPI("local", 1))

    def test_MPI_autodist_recurse_limit(self):
        self.assertTrue(runMPI("autodist"))

    def test_MPI_fetch(self):
        self.assertTrue(runMPI("fetch"))

    def test_MPI_multiinputs(self):
        self.assertTrue(runMPI("multiinputs"))

    def test_MPI_reinit(self):
        self.assertTrue(runMPIReinit())

    def test_MPI_draw(self):
        removeFile("model.dot")
        self.assertTrue(runMPI("draw"))
        if not filecmp.cmp("model.dot", "expected/MPI_model.dot"):
            print("Graphviz file did not match")
            self.fail()
        removeFile("model.dot")

    def test_MPI_random(self):
        self.assertTrue(runMPI("random"))

    #@unittest.skip("Known to run into infinite loops")
    def test_MPI_checkpoint(self):
        # First run the checkpoint and check whether or not the output is identical with or without checkpointing enabled
        proc = subprocess.Popen("mpirun -np 3 python testmodels/experiment.py checkpoint", shell=True)
        # Wait for a few seconds, should be about halfway by then
        time.sleep(5)
        proc.kill()
        # Now try recovering
        proc = subprocess.Popen("mpirun -np 3 python testmodels/experiment.py checkpoint", shell=True)
        proc.wait()
        # NOTE: output traces are NOT guaranteed to be identical, as it might be possible that the output was being flushed
        # to disk while the problem happened. Temporarily, this is simply a smoke test.
        # Now remove all generated checkpoints
        proc = subprocess.Popen("rm testing_*.pdc", shell=True)
        proc.wait()

    def test_MPI_trace(self):
        removeFile("devstrace.vcd")
        removeFile("devstrace.xml")
        self.assertTrue(runMPI("trace"))
        # Compare XML and VCD trace files too
        if not vcdEqual("devstrace.vcd", "expected/trace.vcd"):
            print("VCD trace comparison did not match")
            self.fail()
        if not filecmp.cmp("devstrace.xml", "expected/trace.xml"):
            print("XML trace comparison did not match")
            self.fail()

    def test_MPI_reinit(self):
        removeFile("output/reinit1")
        removeFile("output/reinit2")
        removeFile("output/reinit3")
        try:
            runMPI("reinit")
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

def runMPI(name, processes = 3):
    removeFile("output/" + str(name))
    try:
        proc = subprocess.Popen("mpirun -np " + str(processes) + " python testmodels/experiment.py " + str(name), shell=True)
        proc.wait()
    except:
        import sys
        #print(sys.exc_info()[0])
        proc.terminate()
        # Prevent zombie
        del proc
        return False
    # Deadlocks not handled...
    # Compare to the desired result
    if not filecmp.cmp("output/" + str(name), "expected/" + str(name)):
        return False
    return True
