from .util import runTraceAtController
import sys

class TracerVerbose(object):
    """
    A tracer for simple verbose output
    """
    def __init__(self, uid, server, filename):
        """
        Constructor

        :param uid: the UID of this tracer
        :param server: the server to make remote calls on
        :param filename: file to save the trace to, can be None for output to stdout
        """
        if server.getName() == 0:
            self.filename = filename
        else:
            self.filename = None
        self.server = server
        self.prevtime = (-1, -1)
        self.uid = uid

    def startTracer(self, recover):
        """
        Starts up the tracer

        :param recover: whether or not this is a recovery call (so whether or not the file should be appended to)
        """
        if self.filename is None:
            self.verb_file = sys.stdout
        elif recover:
            self.verb_file = open(self.filename, 'a+')
        else:
            self.verb_file = open(self.filename, 'w')

    def stopTracer(self):
        """
        Stop the tracer
        """
        self.verb_file.flush()

    def trace(self, time, text):
        """
        Actual tracing function

        :param time: time at which this trace happened
        :param text: the text that was traced
        """
        string = ""
        if time > self.prevtime:
            string = ("\n__  Current Time: %10.2f " + "_"*42 + " \n\n") % (time[0])
            self.prevtime = time
        string += "%s\n" % text
        try:
            self.verb_file.write(string)
        except TypeError:
            self.verb_file.write(string.encode())

    def traceInternal(self, aDEVS):
        """
        Tracing done for the internal transition function

        :param aDEVS: the model that transitioned
        """
        text = "\n"
        text += "\tINTERNAL TRANSITION in model <%s>\n" % aDEVS.getModelFullName()
        text += "\t\tNew State: %s\n" % str(aDEVS.state)
        text += "\t\tOutput Port Configuration:\n"
        for I in range(len(aDEVS.OPorts)):
            text += "\t\t\tport <" + str(aDEVS.OPorts[I].getPortName()) + ">:\n"
            for msg in aDEVS.myOutput.get(aDEVS.OPorts[I], []):
                text += "\t\t\t\t" + str(msg) + "\n"
        # Don't show the age
        text += "\t\tNext scheduled internal transition at time %.2f\n" % (aDEVS.timeNext[0])
        runTraceAtController(self.server, self.uid, aDEVS, [aDEVS.timeLast, '"' + text + '"'])

    def traceConfluent(self, aDEVS):
        """
        Tracing done for the confluent transition function

        :param aDEVS: the model that transitioned
        """
        text = "\n"
        text += "\tCONFLUENT TRANSITION in model <%s>\n" % aDEVS.getModelFullName()
        text += "\t\tInput Port Configuration:\n"
        for I in range(len(aDEVS.IPorts)):
            text += "\t\t\tport <" + str(aDEVS.IPorts[I].getPortName()) + ">: \n"
            for msg in aDEVS.myInput.get(aDEVS.IPorts[I], []):
                text += "\t\t\t\t" + str(msg) + "\n"
        text += "\t\tNew State: %s\n" % str(aDEVS.state)
        text += "\t\tOutput Port Configuration:\n"
        for I in range(len(aDEVS.OPorts)):
            text += "\t\t\tport <" + str(aDEVS.OPorts[I].getPortName()) + ">:\n"
            for msg in aDEVS.myOutput.get(aDEVS.OPorts[I], []):
                text += "\t\t\t\t" + str(msg) + "\n"
        # Don't show the age
        text += "\t\tNext scheduled internal transition at time %.2f\n" % (aDEVS.timeNext[0])
        runTraceAtController(self.server, self.uid, aDEVS, [aDEVS.timeLast, '"' + text + '"'])

    def traceExternal(self, aDEVS):
        """
        Tracing done for the external transition function

        :param aDEVS: the model that transitioned
        """
        text = "\n"
        text += "\tEXTERNAL TRANSITION in model <%s>\n" % aDEVS.getModelFullName()
        text += "\t\tInput Port Configuration:\n"
        for I in range(len(aDEVS.IPorts)):
            text += "\t\t\tport <" + str(aDEVS.IPorts[I].getPortName()) + ">:\n"
            for msg in aDEVS.myInput.get(aDEVS.IPorts[I], []):
                text += "\t\t\t\t" + str(msg) + "\n"
        text += "\t\tNew State: %s\n" % str(aDEVS.state)
        # Don't show the age
        text += "\t\tNext scheduled internal transition at time %.2f\n" % (aDEVS.timeNext[0])
        runTraceAtController(self.server, self.uid, aDEVS, [aDEVS.timeLast, '"' + text + '"'])

    def traceInit(self, aDEVS):
        """
        Tracing done for the initialisation

        :param aDEVS: the model that was initialised
        """
        text = "\n"
        text += "\tINITIAL CONDITIONS in model <%s>\n" % aDEVS.getModelFullName()
        text += "\t\tInitial State: %s\n" % str(aDEVS.state)
        # Don't show the age
        text += "\t\tNext scheduled internal transition at time %.2f\n" % (aDEVS.timeNext[0])
        runTraceAtController(self.server, self.uid, aDEVS, [aDEVS.timeLast, '"' + text + '"'])

    def traceUser(self, time, aDEVS, variable, value):
        text = "\n"
        text += "\tUSER CHANGE in model <%s>\n" % aDEVS.getModelFullName()
        text += "\t\tAltered attribute <%s> to value <%s>\n" % (variable, value)
        # Is only called at the controller, outside of the GVT loop, so commit directly
        self.trace(time, text)
