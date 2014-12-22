import logging
import logging.handlers

def setLogger(loc, address, loglevel):
    global logger
    logger = logging.getLogger('PyDEVS-logging')
    logger.setLevel(loglevel)
    global location
    location = loc
    handler = logging.handlers.SysLogHandler(address, facility=19)
    logger.addHandler(handler)

def debug(msg):
    logger.debug(str(location) + " " + msg)
    return True

def info(msg):
    logger.info(str(location) + " " + msg)
    return True

def warn(msg):
    logger.warn(str(location) + " " + msg)
    return True

def error(msg):
    logger.error(str(location) + " " + msg)
    return True
