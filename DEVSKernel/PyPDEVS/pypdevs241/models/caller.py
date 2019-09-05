import stacktracer
stacktracer.trace_start("trace.html",interval=5,auto=True) # Set auto flag to always update file!

import regression.normal as experiment
import logging
experiment.sim("exp.log", ('localhost', 514), logging.DEBUG)
