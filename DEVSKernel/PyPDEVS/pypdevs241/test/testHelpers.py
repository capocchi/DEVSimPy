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
from pypdevs.util import *

class TestHelpers(unittest.TestCase):
    # Tests the externalInput function, which takes messages of the form:
    #   [[time, age], content, anti-message, UUID, color]
    def setUp(self):
        setLogger('None', ('localhost', 514), logging.WARN)

    def test_helper_add_dict(self):
        a = {"a": 3, "b": 6, "c": 2}
        b = {"a": 4, "b": 1, "c": 7}
        addDict(a, b)
        self.assertTrue(a == {"a": 7, "b": 7, "c": 9})

        b = {"a": 4, "b": 1, "c": 7}
        addDict(a, b)
        self.assertTrue(a == {"a": 11, "b": 8, "c": 16})

        b = {"c": 1}
        addDict(a, b)
        self.assertTrue(a == {"a": 11, "b": 8, "c": 17})

        b = {"a": -21}
        addDict(a, b)
        self.assertTrue(a == {"a": -10, "b": 8, "c": 17})

        b = {"a": 0, "d": 9}
        addDict(a, b)
        self.assertTrue(a == {"a": -10, "b": 8, "c": 17, "d": 9})

        b = {}
        addDict(a, b)
        self.assertTrue(a == {"a": -10, "b": 8, "c": 17, "d": 9})

        b = {"a": 10, "b": -8, "c": -17, "d": -9, "def": 3}
        addDict(a, b)
        self.assertTrue(a == {"a": 0, "b": 0, "c": 0, "d": 0, "def": 3})

        b = {"d": -9, "def": 2}
        addDict(a, b)
        self.assertTrue(a == {"a": 0, "b": 0, "c": 0, "d": -9, "def": 5})

    def test_helper_all_zero_dict(self):

        a = {"a": 0}
        self.assertTrue(allZeroDict(a))

        a = {}
        self.assertTrue(allZeroDict(a))

        a = {"a": 0, "b": 0, "c": 0}
        self.assertTrue(allZeroDict(a))

        a = {"a": 1, "b": 0}
        self.assertFalse(allZeroDict(a))

        a = {"a": 1, "b": -1}
        self.assertFalse(allZeroDict(a))

        a = {"a": 0, "b": 1}
        self.assertFalse(allZeroDict(a))

        a = {"a": -1}
        self.assertFalse(allZeroDict(a))

    def test_toStr(self):
        self.assertTrue(toStr("abc") == "'abc'")
        self.assertTrue(toStr("'abc") == "''abc'")
        self.assertTrue(toStr(5) == "'5'")
        self.assertTrue(toStr([1, 2, 3]) == "'[1, 2, 3]'")

    def test_DEVSException(self):
        self.assertTrue(str(DEVSException("ABC")) == "DEVS Exception: ABC")

    def test_easyCommand(self):
        self.assertTrue(easyCommand("abc", []) == "abc()")
        self.assertTrue(easyCommand("abc", ["1", "def"]) == "abc(1, def)")
        self.assertTrue(easyCommand("abc", ["'def'"]) == "abc('def')")
