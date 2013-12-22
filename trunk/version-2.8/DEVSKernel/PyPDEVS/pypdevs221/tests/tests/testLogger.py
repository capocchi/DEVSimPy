from testutils import *
import logger

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
