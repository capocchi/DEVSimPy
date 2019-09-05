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

from threading import Event, Thread, Lock
import pypdevs.accurate_time as time

class ThreadingPython(object):
    """
    Simple Python threads subsystem
    """
    def __init__(self):
        """
        Constructor
        """
        self.evt = Event()
        self.evt_lock = Lock()

    def wait(self, delay, func):
        """
        Wait for the specified time, or faster if interrupted

        :param delay: time to wait
        :param func: the function to call
        """
        #NOTE this call has a granularity of 5ms in Python <= 2.7.x in the worst case, so beware!
        #     the granularity seems to be much better in Python >= 3.x
        p = Thread(target=ThreadingPython.callFunc, args=[self, delay, func])
        p.daemon = True
        p.start()

    def interrupt(self):
        """
        Interrupt the waiting thread
        """
        self.evt.set()

    def callFunc(self, delay, func):
        """
        Function to call on a seperate thread: will block for the specified time and call the function afterwards
        """
        with self.evt_lock:
            self.evt.wait(delay)
            func()
            self.evt.clear()
