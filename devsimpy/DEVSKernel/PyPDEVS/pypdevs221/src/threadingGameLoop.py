import threading
import time

class ThreadingGameLoop(object):
    """
    Game loop subsystem for realtime simulation. Time will only progress when a *step* call is made.
    """
    def __init__(self):
        """
        Constructor
        """
        self.event = threading.Event()
        self.ctime = 0.0
        self.nextEvent = float('inf')

    def step(self):
        """
        Perform a step in the simulation. Actual processing is done in a seperate thread.
        """
        self.ctime = time.time()
        if self.ctime >= self.nextEvent:
            self.interrupt()
        
    def wait(self, delay):
        """
        Wait for the specified time, or faster if interrupted

        :param time: time to wait
        """
        self.nextEvent = time.time() + delay
        if self.nextEvent > self.ctime:
            self.event.wait()
    
    def interrupt(self):
        """
        Interrupt the waiting thread
        """
        self.event.set()
        self.event.clear()
