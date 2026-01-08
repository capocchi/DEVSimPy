# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Strategies.py --- Strategies for DEVSimPy simulation
#                     --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 3.0                                      last modified:  23/12/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# This module implements various simulation strategies for DEVSimPy,
# depending on the selected DEVS package (PyDEVS, PyPDEVS, BrokerDEVS,...).
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import builtins
import re
import os

### import the DEVS module depending on the selected DEVS package in DEVSKernel directory
for pydevs_dir, path in getattr(builtins,'DEVS_DIR_PATH_DICT').items():
	if os.path.exists(path):
		### split from DEVSKernel string and replace separator with point
		d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')

		### for py 3.X
		import importlib
		exec("%s = importlib.import_module('DEVSKernel%s.DEVS')"%(pydevs_dir,d))
		
		
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Import simulation strategies from different DEVS backends
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

# ---------------------------------------------------------------------------
# Original PyDEVS strategies
# ---------------------------------------------------------------------------

from DEVSKernel.PyDEVS.SimStrategies import OriginalPyDEVSSimStrategy, BagBasedPyDEVSSimStrategy, DirectCouplingPyDEVSSimStrategy, terminate_never

# ---------------------------------------------------------------------------
# Classic and Parallel PyPDEVS strategies
# ---------------------------------------------------------------------------

from DEVSKernel.PyPDEVS.SimStrategies import ClassicPyPDEVSSimStrategy, ParallelPyPDEVSSimStrategy

# ---------------------------------------------------------------------------
# Broker-based distributed strategies with DEVSStreaming message standardization
# Supports multiple brokers (Kafka, MQTT, RabbitMQ, etc.)
# ---------------------------------------------------------------------------

# Kafka + DEVSStreaming
from DEVSKernel.BrokerDEVS.DEVSStreaming.SimStrategyKafkaMS4Me import SimStrategyKafkaMS4Me

# MQTT + DEVSStreaming
try:
    from DEVSKernel.BrokerDEVS.DEVSStreaming.SimStrategyMqttMS4Me import SimStrategyMqttMS4Me
except ImportError as e:
    logger = __import__('logging').getLogger(__name__)
    logger.debug("MQTT strategy not available: %s", e)
    SimStrategyMqttMS4Me = None

# Generic Broker-based distributed strategies (for other brokers)
# Available for future use - currently under development
try:
    from DEVSKernel.BrokerDEVS.SimStrategyBroker import (
        SimStrategyBroker,
        KafkaSimStrategy,
        BrokerSimStrategyFactory,
    )
except ImportError as e:
    # Generic broker strategies not yet ready
    logger = __import__('logging').getLogger(__name__)
    logger.debug("Generic broker strategies not available: %s", e)
