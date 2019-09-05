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

"""
Scheduler for external input messages
"""
from heapq import heappop, heappush, heapify
from pypdevs.logger import *

class MessageScheduler(object):
    """
    An efficient implementation of a message scheduler for the inputQueue,
    it supports very fast invalidations (O(1)) and fast retrievals of first
    element (O(log(n) in average case)
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
        self.invalids = set()

    def __getstate__(self):
        """
        For pickling
        """
        retdict = {}
        unpicklable = frozenset(["instancemethod", "lock", "_Event"])
        for i in dir(self):
            if getattr(self, i).__class__.__name__ in unpicklable:
                # unpicklable, so don't copy it
                continue
            elif str(i).startswith("__"):
                continue
            else:
                retdict[str(i)] = getattr(self, i)
        return retdict

    def insert(self, extraction, model_list):
        """
        Insert several messages that were created elsewhere and merge them in.

        :param extraction: the output of the extract method on the other message scheduler
        :param model_list: models that are inserted and for which extraction happened
        """
        msgs, invalids = extraction
        # A simple update suffices, as these messages have a unique ID
        self.invalids |= invalids
        for msg in msgs:
            moddata = {}
            for entry in msg.content:
                inport = model_list[entry[0]].ports[entry[1]]
                moddata[inport] = msg.content[entry]
            # Overwrite the original message
            msg.content = moddata
            self.schedule(msg)

    def extract(self, model_ids):
        """
        Extract messages from the message scheduler for when a model gets removed from this kernel.

        :param model_ids: iterable of model_ids of models that will be removed from this node
        :returns: tuple -- extraction that needs to be passed to the insert method of another scheduler
        """
        new_heap = []
        extracted = []
        for msg in self.heap:
            for port in msg.content:
                if port.host_DEVS.model_id in model_ids:
                    msg.content = {(i.host_DEVS.model_id, i.port_id): 
                                    msg.content[i]
                                    for i in msg.content}
                    extracted.append(msg)
                else:
                    new_heap.append(msg)
                # Break, as this was simply done for a python 2 and python 3 compliant version
                break
        heapify(new_heap)
        self.heap = new_heap
        return (extracted, self.invalids)

    def schedule(self, msg):
        """
        Schedule a message for processing

        :param msg: the message to schedule
        """
        try:
            self.invalids.remove(msg.uuid)
        except KeyError:
            heappush(self.heap, msg)

    def massUnschedule(self, uuids):
        """
        Unschedule several messages, this way it will no longer be processed.

        :param uuids: iterable of UUIDs that need to be removed
        """
        self.invalids = self.invalids.union(uuids)

    def readFirst(self):
        """
        Returns the first (valid) message. Not necessarily O(1), as it could be
        the case that a lot of invalid messages are still to be deleted.
        """
        self.cleanFirst()
        return self.heap[0]

    def removeFirst(self):
        """
        Notify that the first (valid) message is processed.

        :returns: msg -- the next first message that is valid
        """
        self.cleanFirst()
        self.processed.append(heappop(self.heap))

    def purgeFirst(self):
        """
        Notify that the first (valid) message must be removed

        :returns: msg -- the next first message that is valid
        """
        self.cleanFirst()
        heappop(self.heap)

    def cleanFirst(self):
        """
        Clean all invalid messages at the front of the list. Method MUST be called
        before any accesses should happen to the first element, otherwise this
        first element might be a message that was just invalidated
        """
        try:
            while 1:
                self.invalids.remove(self.heap[0].uuid)
                # If it got removed, it means that the message was indeed invalidated, so we can simply pop it
                heappop(self.heap)
        except (KeyError, IndexError):
            # Seems that the UUID was not invalidated, so we are done
            # OR
            # Reached the end of the heap and all were invalid
            pass

    def revert(self, time):
        """
        Revert the inputqueue to the specified time, will also clean up the list of processed elements

        :param time: time to which revertion should happen
        """
        try:
            i = 0
            while self.processed[i].timestamp < time:
                i += 1
            for msg in self.processed[i:]:
                # All processed messages were valid, so no need for the more expensive check
                # Should an invalidation for a processed message have just arrived, it will
                # be processed AFTER this revertion, thus using the normal unschedule() function
                heappush(self.heap, msg)
            self.processed = self.processed[:i]
        except IndexError:
            # All elements are smaller
            pass
    
    def cleanup(self, time):
        """
        Clean up the processed list, also removes all invalid elements

        :param time: time up to which cleanups are allowed to happen
        """
        # We can be absolutely certain that ONLY elements from the processed list should be deleted
        self.processed = [i for i in self.processed if i.timestamp >= time]
        # Clean up the dictionary too, as otherwise it will start to contain a massive amount of entries, consuming both memory and increasing the amortized worst case
