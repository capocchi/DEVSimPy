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

import unittest
import subprocess
import os
import sys

from .testRealtime import TestRealtime

if __name__ == '__main__':
    realtime = unittest.TestLoader().loadTestsFromTestCase(TestRealtime)
    allTests = unittest.TestSuite()
    allTests.addTest(realtime)
    unittest.TextTestRunner(verbosity=2, failfast=True).run(allTests)