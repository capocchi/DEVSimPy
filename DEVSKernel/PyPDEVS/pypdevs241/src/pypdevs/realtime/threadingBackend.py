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

import threading

class ThreadingBackend(object):
    """
    Wrapper around the actual threading backend. It will also handle interrupts and the passing of them to the calling thread.
    """
    def __init__(self, subsystem, args):
        """
        Constructor

        :param subsystem: string specifying the subsystem to use: python, tkinter or loop
        :param args: all additional arguments that should be passed to the subsystem's constructor (must be a list)
        """
        self.interrupted_value = None
        self.value_lock = threading.Lock()
        if subsystem == "python":
            from pypdevs.realtime.threadingPython import ThreadingPython
            self.subsystem = ThreadingPython(*args)
        elif subsystem == "tkinter":
            from pypdevs.realtime.threadingTkInter import ThreadingTkInter
            self.subsystem = ThreadingTkInter(*args)
        elif subsystem == "loop":
            from pypdevs.realtime.threadingGameLoop import ThreadingGameLoop
            self.subsystem = ThreadingGameLoop(*args)
        else:
            raise Exception("Realtime subsystem not found: " + str(subsystem))

    def wait(self, time, func):
        """
        A non-blocking call, which will call the *func* parameter after *time* seconds. It will use the provided backend to do this.

        :param time: time to wait in seconds, a float is possible
        :param func: the function to call after the time has passed
        """
        self.subsystem.wait(time, func)

    def interrupt(self, value):
        """
        Interrupt a running wait call.

        :param value: the value that interrupts
        """
        self.interrupted_value = value
        self.subsystem.interrupt()

    def setInterrupt(self, value):
        """
        Sets the value of the interrupt. This should not be used manually and is only required to prevent the asynchronous combo generator from making *interrrupt()* calls.
        
        :param value: value with which the interrupt variable should be set
        """
        with self.value_lock:
            if self.interrupted_value is None:
                self.interrupted_value = value
                return True
            else:
                # The interrupt was already set, indicating a collision!
                return False

    def getInterrupt(self):
        """
        Return the value of the interrupt and clear it internally.

        :returns: the interrupt
        """
        with self.value_lock:
            val = self.interrupted_value
            self.interrupted_value = None
        return val

    def step(self):
        """
        Perform a step in the backend; only supported for the game loop backend.
        """
        self.subsystem.step()
