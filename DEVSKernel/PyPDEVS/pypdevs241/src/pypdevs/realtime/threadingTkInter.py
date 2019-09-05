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

def tkMainThreadPoller(tk, queue):
    """
    The polling function to register with Tk at the start. This will do the actual scheduling in Tk.

    :param tk: the Tk instance to use
    :param queue: the queue to check
    """
    global tkRunningID
    while 1:
        try:
            time, func = queue.popleft()
            tkRunningID = tk.after(time, func)
        except TypeError:
            # Was an invalidation call
            try:
                if tkRunningID is not None:
                    tk.after_cancel(tkRunningID)
            except IndexError:
                # Nothing to cancel
                pass
            tkRunningID = None
        except IndexError:
            break
    tk.after(10, tkMainThreadPoller, tk, queue)

class ThreadingTkInter(object):
    """
    Tk Inter subsystem for realtime simulation
    """
    def __init__(self, tk):
        """
        Constructor

        :param queue: the queue object that is also used by the main thread to put events on the main Tk object
        """
        self.runningID = None
        self.last_infinity = False
        import collections
        queue = collections.deque()
        self.queue = queue
        tk.after(10, tkMainThreadPoller, tk, queue)

    def unlock(self):
        """
        Unlock the waiting thread
        """
        # Don't get it normally, as it would seem like a method call
        getattr(self, "func")()

    def wait(self, t, func):
        """
        Wait for the specified time, or faster if interrupted

        :param t: time to wait
        :param func: the function to call
        """
        if t == float('inf'):
            self.last_infinity = True
        else:
            self.last_infinity = False
            self.func = func
            self.queue.append((int(t*1000), self.unlock))

    def interrupt(self):
        """
        Interrupt the waiting thread
        """
        if not self.last_infinity:
            self.queue.append(None)
        self.unlock()
