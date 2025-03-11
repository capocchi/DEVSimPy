from .util import runTraceAtController, toStr
import sys

class TracerXML(object):
    """
    A tracer for XML tracing output
    """
    def __init__(self, uid, server, filename):
        """
        Constructor

        :param uid: the UID of this tracer
        :param server: the server to make remote calls on
        :param filename: file to save the trace to
        """
        if server.getName() == 0:
            self.filename = filename
        else:
            self.filename = None
        self.server = server
        self.uid = uid

    def startTracer(self, recover):
        """
        Starts up the tracer

        :param recover: whether or not this is a recovery call (so whether or not the file should be appended to)
        """
        if self.filename is None:
            # Nothing to do here as we aren't the controller
            return
        elif recover:
            self.xml_file = open(self.filename, 'a+')
        else:
            self.xml_file = open(self.filename, 'w')
        self.xml_file.write(("<?xml version=\"1.0\"?>\n" + "<trace>\n").encode())

    def stopTracer(self):
        """
        Stop the tracer
        """
        self.xml_file.write("</trace>")
        self.xml_file.flush()

    def trace(self, modelName, timeStamp, eventKind, portInfo, xmlState, strState):
        """
        Save an XML entry for the provided parameters, basically wraps it in the necessary tags

        :param modelName: name of the model
        :param timeStamp: timestamp of the transition
        :param eventKind: kind of event that happened, e.g. internal, external, ...
        :param portInfo: actual information about the port
        :param xmlState: XML representation of the state
        :param strState: normal string representation of the state
        """
        self.xml_file.write(("<event>\n"
                          + "<model>" + modelName + "</model>\n"
                          + "<time>" + str(timeStamp[0]) + "</time>\n"
                          + "<kind>" + eventKind + "</kind>\n"
                          + portInfo
                          + "<state>\n"+ xmlState + "<![CDATA[" + strState + "]]>\n</state>\n"
                          + "</event>\n").encode())

    def traceInternal(self, aDEVS):
        """
        The trace functionality for XML output at an internal transition

        :param aDEVS: the model that transitioned
        """
        portInfo = ""
        for I in range(len(aDEVS.OPorts)):
            if aDEVS.OPorts[I] in aDEVS.myOutput and aDEVS.myOutput[aDEVS.OPorts[I]] is not None:
                portInfo += "<port name=\""+ aDEVS.OPorts[I].getPortName()+"\" category=\"O\">\n"
                for j in aDEVS.myOutput[aDEVS.OPorts[I]]:
                    portInfo += "<message>" + str(j) + "</message>\n</port>\n"
        runTraceAtController(self.server, self.uid, aDEVS, [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, "'IN'", toStr(portInfo), toStr(aDEVS.state.toXML()), toStr(aDEVS.state)])

    def traceExternal(self, aDEVS):
        """
        The trace functionality for XML output at an external transition

        :param aDEVS: the model that transitioned
        """
        portInfo = ""
        for I in range(len(aDEVS.IPorts)):
            portInfo += "<port name=\""+ aDEVS.IPorts[I].getPortName()+"\" category=\"I\">\n"
            for j in aDEVS.myInput[aDEVS.IPorts[I]]:
                portInfo += "<message>" + str(j) + "</message>\n</port>\n"
        runTraceAtController(self.server, self.uid, aDEVS, [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, "'EX'", toStr(portInfo), toStr(aDEVS.state.toXML()), toStr(aDEVS.state)])

    def traceConfluent(self, aDEVS):
        """
        The trace functionality for XML output at a confluent transition

        :param aDEVS: the model that transitioned
        """
        portInfo = ""
        for I in range(len(aDEVS.IPorts)):
            portInfo += "<port name=\""+ aDEVS.IPorts[I].getPortName()+"\" category=\"I\">\n"
            for j in aDEVS.myInput[aDEVS.IPorts[I]]:
                portInfo += "<message>" + str(j) + "</message>\n</port>\n"
        runTraceAtController(self.server, self.uid, aDEVS, [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, "'EX'", toStr(portInfo), toStr(aDEVS.state.toXML()), toStr(aDEVS.state)])
        portInfo = ""
        for I in range(len(aDEVS.OPorts)):
            if aDEVS.OPorts[I] in aDEVS.myOutput:
                portInfo += "<port name=\""+ aDEVS.OPorts[I].getPortName()+"\" category=\"O\">\n"
                for j in aDEVS.myOutput[aDEVS.OPorts[I]]:
                    portInfo += "<message>" + str(j) + "</message>\n</port>\n"
        runTraceAtController(self.server, self.uid, aDEVS, [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, "'IN'", toStr(portInfo), toStr(aDEVS.state.toXML()), toStr(aDEVS.state)])

    def traceInit(self, aDEVS):
        """
        The trace functionality for XML output at initialization

        :param aDEVS: the model that transitioned
        """
        runTraceAtController(self.server, self.uid, aDEVS, [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, "'EX'", "''", toStr(aDEVS.state.toXML()), toStr(aDEVS.state)])
