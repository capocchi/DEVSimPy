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

import pypdevs.accurate_time as time
from threading import Lock

class ThreadingGameLoop(object):
    """
    Game loop subsystem for realtime simulation. Time will only progress when a *step* call is made.
    """
    def __init__(self):
        """
        Constructor
        """
        self.next_event = float('inf')

    def step(self):
        """
        Perform a step in the simulation. Actual processing is done in a seperate thread.
        """
        if time.time() >= self.next_event:
            self.next_event = float('inf')
            getattr(self, "func")()
        
    def wait(self, delay, func):
        """
        Wait for the specified time, or faster if interrupted

        :param time: time to wait
        :param func: the function to call
        """
        self.func = func
        self.next_event = time.time() + delay
    
    def interrupt(self):
        """
        Interrupt the waiting thread
        """
        self.next_event = 0
