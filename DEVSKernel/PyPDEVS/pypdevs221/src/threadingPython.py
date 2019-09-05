from threading import Event
import time

class ThreadingPython(object):
    """
    Simple Python threads subsystem
    """
    def __init__(self):
        """
        Constructor
        """
        self.evt = Event()

    def wait(self, delay):
        """
        Wait for the specified time, or faster if interrupted

        :param delay: time to wait
        """
        #NOTE this call has a granularity of 5ms in Python <= 2.7.x in the worst case, so beware!
        #     the granularity seems to be much better in Python >= 3.x
        self.evt.wait(delay)
        self.evt.clear()

    def interrupt(self):
        """
        Interrupt the waiting thread
        """
        self.evt.set()
