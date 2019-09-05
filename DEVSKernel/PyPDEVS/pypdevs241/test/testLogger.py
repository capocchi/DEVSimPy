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
import pypdevs.logger as logger

class StubLogger(object):
    def __init__(self):
        self.lst_debug = []
        self.lst_info = []
        self.lst_warn = []
        self.lst_error = []

    def debug(self, msg):
        self.lst_debug.append(msg)

    def info(self, msg):
        self.lst_info.append(msg)

    def warn(self, msg):
        self.lst_warn.append(msg)

    def error(self, msg):
        self.lst_error.append(msg)

class TestLogger(unittest.TestCase):
    def setUp(self):
        logger.logger = StubLogger()
        logger.location = 154

    def test_logger_debug(self):
        self.assertTrue(logger.debug("ABC"))
        self.assertTrue(logger.logger.lst_debug == ["154 -- ABC"])
        self.assertTrue(logger.logger.lst_info == [])
        self.assertTrue(logger.logger.lst_warn == [])
        self.assertTrue(logger.logger.lst_error == [])

    def test_logger_info(self):
        self.assertTrue(logger.info("ABC"))
        self.assertTrue(logger.logger.lst_info == ["154 -- ABC"])
        self.assertTrue(logger.logger.lst_debug == [])
        self.assertTrue(logger.logger.lst_warn == [])
        self.assertTrue(logger.logger.lst_error == [])

    def test_logger_warn(self):
        self.assertTrue(logger.warn("ABC"))
        self.assertTrue(logger.logger.lst_warn == ["154 -- ABC"])
        self.assertTrue(logger.logger.lst_debug == [])
        self.assertTrue(logger.logger.lst_info == [])
        self.assertTrue(logger.logger.lst_error == [])

    def test_logger_error(self):
        self.assertTrue(logger.error("ABC"))
        self.assertTrue(logger.logger.lst_error == ["154 -- ABC"])
        self.assertTrue(logger.logger.lst_debug == [])
        self.assertTrue(logger.logger.lst_info == [])
        self.assertTrue(logger.logger.lst_warn == [])
