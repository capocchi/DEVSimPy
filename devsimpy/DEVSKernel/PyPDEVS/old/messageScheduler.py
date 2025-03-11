# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# message_scheduler.py --- Scheduler for external input messages
#                     --------------------------------
#                          Copyright (c) 2013
#                          Hans    Vangheluwe
#                          Yentl Van Tendeloo
#                       McGill University (Montréal)
#                     --------------------------------
# Version 2.0                                       last modified: 21/02/2013
#    - Make a high-performance implementation for the inputQueue
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
from heapq import *
from .logger import *
import threading

class MessageScheduler(object):
    """
    An efficient implementation of a message scheduler for the inputQueue,
    it supports very fast invalidations (O(1)) and fast retrievals of first
    element (O(n*log(n))
    """
    def __init__(self):
        """
        Constructor.
        """
        # List of processed messages
        self.processed = []
        # Heap of the to be processed messages
        self.heap = []
        # All invalidated messages, simply adding a message's UUID will invalidate
        # the message. The counter that it keeps is for multiple invalidations
        self.invalids = {}
        # A lock for the heap
        # It should be shielded by the global simlock, though this module doesn't
        # depend on it for safety
        #self.lock = threading.Lock()

    def __getstate__(self):
        retdict = {}
        for i in dir(self):
            if getattr(self, i).__class__.__name__ not in ["instancemethod", "lock", "_Event"]:
                # unpicklable, so don't copy it
                pass
            else:
                retdict[str(i)] = getattr(self, i)
        return retdict
                                
    def schedule(self, msg):
        """
        Schedule a message for processing
        Args:
                msg - the message to schedule
        """
        if self.invalids.get(msg.uuid, 0) <= 0:
            # It is a good message, so just schedule it in the 'to process' list
            heappush(self.heap, [msg.timestamp, msg])
        else:
            # We filtered one out, so put it in the list, but decrement the number of invalidations
            self.invalids[msg.uuid] -= 1

    def unschedule(self, msg):
        """
        Unschedule a message, this way it will no longer be processed. To make an
        easier interface for time warp implementation, a message can be unscheduled
        more frequently than it is scheduled, this will nullify the next schedule
        of this message.
        """
        time = msg.timestamp
        # Don't remove from processed immediately, as this would slow down anti-message processing
        self.invalids[msg.uuid] = self.invalids.get(msg.uuid, 0) + 1

    def readFirst(self):
        """
        Returns the first (valid) message. Not necessarily O(1), as it could be
        the case that a lot of invalid messages are still to be deleted.
        """
        self.cleanFirst()
        msg = self.heap[0][1]
        return msg

    def removeFirst(self):
        """
        Notify that the first (valid) message is processed.
        """
        self.cleanFirst()
        self.processed.append(heappop(self.heap)[1])

    def cleanFirst(self):
        """
        Clean all invalid messages at the front of the list. Method MUST be called
        before any accesses should happen to the first element, otherwise this
        first element might be a message that was just invalidated
        """
        try:
            while self.invalids.get(self.heap[0][1].uuid, 0) > 0:
                self.invalids[self.heap[0][1].uuid] -= 1
                heappop(self.heap)
        except IndexError:
            pass

    def revert(self, time):
        """
        Revert the inputqueue to the specified time, will also clean up the list of processed elements
        Args:
                time - the time to which revertion should happen
        """
        nprocessed = []
        for i in self.processed:
            if i.timestamp >= time:
                if self.invalids.get(i.uuid, 0) <= 0:
                    self.schedule(i)
                else:
                    self.invalids[i.uuid] -= 1
            else:
                nprocessed.append(i)
        self.processed = nprocessed
    
    def cleanup(self, time):
        """
        Clean up the processed list, also removes all invalid elements
        Args:
                time - the time up to which cleanups are allowed to happen
        """
        # We can be absolutely certain that ONLY elements from the processed list should be deleted
        nprocessed = []
        for i in self.processed:
            if i.timestamp >= time:
                if self.invalids.get(i.uuid, 0) <= 0:
                    nprocessed.append(i)
                else:
                    self.invalids[i.uuid] -= 1
        self.processed = nprocessed
