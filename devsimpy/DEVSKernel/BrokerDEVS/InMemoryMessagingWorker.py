# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# InMemoryMessagingWorker.py --- COMPATIBILITY SHIM
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/26/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# This is a compatibility shim that re-exports from the new location.
# Old code imports: from DEVSKernel.BrokerDEVS.InMemoryMessagingWorker import X
# New location: DEVSKernel.BrokerDEVS.Workers.InMemoryMessagingWorker
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

# Re-export from new location for backward compatibility
from DEVSKernel.BrokerDEVS.Workers.InMemoryMessagingWorker import (
    InMemoryMessagingWorker,
    MessageAdapter,
    MessageConsumer,
    MessageProducer,
)

__all__ = [
    'InMemoryMessagingWorker',
    'MessageAdapter',
    'MessageConsumer',
    'MessageProducer',
]
