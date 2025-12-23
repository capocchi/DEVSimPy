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
# depending on the selected DEVS package (PyDEVS, PyPDEVS, KafkaDEVS).
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
# Kafka-based distributed strategy with IN-MEMORY workers (threads)
# ---------------------------------------------------------------------------

from DEVSKernel.KafkaDEVS.MS4Me.SimStrategyKafkaMS4Me import SimStrategyKafkaMS4Me
