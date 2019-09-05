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
Logger for Syslog
"""

logger = None
location = None
queue = []
import threading
loglock = threading.Lock()

def setLogger(loc, address, loglevel):
    """
    Sets the logger object

    :param loc: location of the server, to prepend to every logged message
    :param address: the address of the syslog server in the form of (ip-address, port)
    :param loglevel: the level of logging to perform, should be one specified in the logging module
    """
    if loglevel is None:
        return
    global logger
    if logger is not None:
        # A logger is already set, so ignore this one
        return
    import logging
    import logging.handlers
    handler = logging.handlers.SysLogHandler(address, facility=19)
    local_logger = logging.getLogger('PyPDEVS-logging')
    local_logger.addHandler(handler)
    local_logger.setLevel(loglevel)
    global location
    location = loc
    # Now make the logger 'public'
    logger = local_logger

def log(level, msg, logger):
    """
    Do the actual logging at the specified level, but save it in case no logger exists yet

    :param level: string representation of the function to call on the logger
    :param msg: the message to log
    :returns: True -- to allow it as an #assert statement
    """
    with loglock:
        global location
        global queue
        if len(msg) > 80:
            msg = msg[:79]
        if logger is not None:
            # Flush the queue first
            for level1, msg1 in queue:
                getattr(logger, level1)("%s -- %s" % (location, msg1))
            queue = []
            getattr(logger, level)("%s -- %s" % (location, msg))
        else:
            queue.append((level, msg))
        return True

def debug(msg):
    """
    Debug logging statement

    :param msg: the message to print
    :returns: True -- to allow it as an #assert statement
    """
    return log("debug", msg, logger)

def info(msg):
    """
    Informational logging statement

    :param msg: the message to print
    :returns: True -- to allow it as an #assert statement
    """
    return log("info", msg, logger)

def warn(msg):
    """
    Warning logging statement

    :param msg: the message to print
    :returns: True -- to allow it as an #assert statement
    """
    return log("warn", msg, logger)

def error(msg):
    """
    Error logging statement

    :param msg: the message to print
    :returns: True -- to allow it as an #assert statement
    """
    return log("error", msg, logger)
