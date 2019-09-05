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

import os
import sys
sys.path.append('testmodels')
import pypdevs.middleware as middleware
import unittest
import logging
from pypdevs.logger import setLogger
setLogger('None', ('localhost', 514), logging.WARN)
from pypdevs.controller import Controller
import threading
from pypdevs.basesimulator import BaseSimulator
from pypdevs.message import NetworkMessage
from models import *
from collections import defaultdict

class StubController(Controller):
    def __init__(self, name):
        Controller.__init__(self, name, None, None)
        self.reverted = False
        # Just don't create an int, as this indicates remote locations
        self.destinations = defaultdict(lambda : None)
        from pypdevs.relocators.manualRelocator import ManualRelocator
        self.relocator = ManualRelocator()
        self.initialAllocator = None

    def revert(self, a):
        self.reverted = True

    def receiveControl(self, msg):
        thrd = threading.Thread(target=BaseSimulator.receiveControl, args=[self, msg])
        thrd.start()

def equalStateVectors(v1, v2):
    if len(v1) != len(v2):
        return False

    for i in range(len(v1)):
        if v1[i][0] != v2[i][0]:
            return False
        if v1[i][1] != v2[i][1]:
            return False
        # Don't check the state, as this contains addresses
    return True

def vcdEqual(f1, f2):
    f1 = open(f1, 'r')
    f2 = open(f2, 'r')
    line = 0
    for l1, l2 in zip(f1, f2):
        if l1 != l2 and line != 1:
            return False
        line += 1
    return True

def removeFile(f1):
    try:
        os.remove(f1)
    except OSError:
        # File was not there, so result is the same
        pass

def basicSim():
    class StubModel(object):
        def __init__(self):
            self.local_model_ids = set([0, 1])

    class StubServer(object):
        def getProxy(self, name):
            return None

    setLogger('None', ('localhost', 514), logging.WARN)
    sim = StubController(0)
    # Kernels doesn't really matter in the tests, though use a value > 1 to prevent localised optimisations
    sim.server = StubServer()
    sim.setGlobals(
                   tracers=[],
                   address=('localhost', 514),
                   loglevel=logging.WARN,
                   checkpoint_name="(none)",
                   memoization=False,
                   statesaver=2,
                   kernels=3,
                   checkpoint_frequency=-1,
                   msg_copy=0)
    # Set it so that it should be initialised to a decent prevtime
    sim.prevtime = (0, 1)
    sim.model = StubModel()
    sim.simlock.release()
    return sim

def basicMsg():
    class StubDEVS(object):
        def __init__(self):
            self.model_id = 0
    
    class StubPort(object):
        def __init__(self):
            self.port_id = 0
            self.hostDEVS = StubDEVS()
    time = 1
    age = 1
    content = {StubPort(): None}
    uuid = 12345
    color = False
    return NetworkMessage((time, age), content, uuid, color, None)
