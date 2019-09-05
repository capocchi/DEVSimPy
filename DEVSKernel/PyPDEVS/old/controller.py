from .basesimulator import BaseSimulator
from .logger import *

class Controller(BaseSimulator):
    def initGVT(self):
        """
        Initialise the GVT algorithm. Should ONLY be called at the controller,
        though things 'should' work elsewhere...
        """
        assert debug("initGVT called")
        self.simlock.acquire()
        self.nestedlock.acquire()
        self.Tmin = float('inf')
        self.color = True
        msg = [self.model.timeLast[0], float('inf'), self.V]
        self.V = {}
        assert debug("Cleared V")
        self.nextLP.receiveControl(msg)
        self.nestedlock.release()
        self.simlock.release()
        # Wait until the lock is released elsewhere
        self.waitForGVT.wait()
        self.waitForGVT.clear()
        return self.GVT

    def GVTdone(self):
        """
        Notify this simulation kernel that the GVT calculation is finished
        """
        self.waitForGVT.set()

    #TODO never used yet...
    def printRootOutput(self):
        """
        Prints the Root Output of a simulation
        """
        if len(self.model.OPorts) > 0:
            # don't print if root model is autonomous
            # (no output ports)
            print(("\n\tROOT DEVS <%s> Output Port Configuration:" % self.model.getModelFullName()))
            for I in range(0, len(self.model.OPorts) ):
                if self.model.OPorts[I] in self.model.myOutput:
                    print(("\t    port <%s>: %s" % (\
                        self.model.OPorts[I].getPortName(), \
                        self.model.myOutput[self.model.OPorts[I]])))
                else:
                    print(("\t    port <%s>: NoEvent" % self.model.OPorts[I].getPortName()))

    def notifyWait(self):
        """
        Notify the controller that a simulation kernel is waiting.
        """
        self.waitingLock.acquire()
        self.waiting += 1
        self.finishCheck.set()
        self.waitingLock.release()

    def notifyRun(self):
        """
        Notify the controller that a simulation kernel has started running again.
        """
        self.waitingLock.acquire()
        self.waiting -= 1
        self.waitingLock.release()

    def isFinished(self, running):
        """
        Checks if all kernels have indicated that they have finished simulation.
        If each kernel has indicated this, a final (expensive) check happens to 
        prevent premature termination.
        """
        # NOTE make sure that GVT algorithm is not running at the moment, otherwise we deadlock!
        # it might be possible that the GVT algorithm starts immediately after the wait(), causing deadlock again
        # Now we are sure that the GVT algorithm is not running when we start this
        self.waitingLock.acquire()
        if self.waiting == running:
            # It seems that we should be finished, so just ACK this with every simulation kernel before proceeding
            #   it might be possible that the kernel's 'notifyRun' command is still on the way, making the simulation
            #   stop too soon.
            done = self.nextLP.finishRing(self.totalCounter)
        else:
            done = False
        self.waitingLock.release()
        return done

    def waitFinish(self, running):
        """
        Wait until the specified number of kernels have all told that simulation
        finished.
        """
        while True:
            # Force a check after each second
            self.finishCheck.wait(1)
            self.finishCheck.clear()
            if self.isFinished(running):
                # All simulation kernels have told us that they are idle at the moment
                break
        self.runGVT = False
        self.eventGVT.set()
        self.gvtthread.join()
