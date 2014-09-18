from util import runTraceAtController
import sys

class MyTracer(object):
    """
    A custom tracer
    """
    def __init__(self, uid, server, myOwnArg1, myOwnArg2):
        """
        Constructor

        :param uid: the UID of this tracer
        :param server: the server object, to make remote calls
        :param myOwnArg_: custom arguments for this tracer
        """
        self.server = server
        self.uid = uid
        # Own processing

    def startTracer(self, recover):
        """
        Starts up the tracer

        :param recover: whether or not this is a recovery call (so whether or not the file should be appended to)
        """
        pass

    def stopTracer(self):
        """
        Stop the tracer
        """
        pass

    def trace(self, time, myCustomParam1, myCustomParam2):
        """
        Actual tracing function, will do something that is irreversible. If this function is called, 
        it is guaranteed that the trace operation will *not* be rolled back.

        :param time: time at which this trace happened
        :param myCustomParam_: custom parameters
        """
        pass

    def traceInternal(self, aDEVS):
        """
        Tracing done for the internal transition function

        :param aDEVS: the model that transitioned
        """
        # You should only vary the 'myCustomParam_' part
        runTraceAtController(self.server, self.uid, aDEVS, [myCustomParam1, myCustomParam2])

    def traceConfluent(self, aDEVS):
        """
        Tracing done for the confluent transition function

        :param aDEVS: the model that transitioned
        """
        # You should only vary the 'myCustomParam_' part
        runTraceAtController(self.server, self.uid, aDEVS, [myCustomParam1, myCustomParam2])

    def traceExternal(self, aDEVS):
        """
        Tracing done for the external transition function

        :param aDEVS: the model that transitioned
        """
        # You should only vary the 'myCustomParam_' part
        runTraceAtController(self.server, self.uid, aDEVS, [myCustomParam1, myCustomParam2])

    def traceInit(self, aDEVS):
        """
        Tracing done for the initialisation

        :param aDEVS: the model that was initialised
        """
        # You should only vary the 'myCustomParam_' part
        runTraceAtController(self.server, self.uid, aDEVS, [myCustomParam1, myCustomParam2])
