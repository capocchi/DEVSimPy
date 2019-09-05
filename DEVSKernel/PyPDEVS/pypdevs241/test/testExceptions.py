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

from .testutils import *
from pypdevs.util import DEVSException
from pypdevs.DEVS import BaseDEVS, AtomicDEVS, CoupledDEVS

class TestExceptions(unittest.TestCase):
    # Tests the externalInput function, which takes messages of the form:
    #   [[time, age], content, anti-message, UUID, color]
    def setUp(self):
        self.sim = basicSim()

    def tearDown(self):
        self.sim.run_gvt = False

    def test_DEVS_model_exceptions(self):
        try:
            # Shouldn't allow instantiation of the base model
            junk = BaseDEVS("junk")
            self.fail() #pragma: nocover
        except DEVSException:
            pass
        try:
            # Shouldn't allow instantiation of the base model
            junk = AtomicDEVS("junk")
            self.fail() #pragma: nocover
        except DEVSException:
            pass
        try:
            # Shouldn't allow instantiation of the base model
            junk = CoupledDEVS("junk")
            self.fail() #pragma: nocover
        except DEVSException:
            pass
