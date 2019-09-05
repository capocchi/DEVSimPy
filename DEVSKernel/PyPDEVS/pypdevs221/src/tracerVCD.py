from .util import runTraceAtController, toStr, DEVSException
from math import floor

class VCDRecord(object):
    """
    A data class to keep information about VCD variables
    """

    def __init__(self, identifierNr, modelName, portName):
        """
        Constructor.

        :param identifierNr: the actual identifier
        :param modelName: name of the model
        :param portName: name of the port
        """
        self.modelName = modelName
        self.portName = portName
        self.identifier = identifierNr
        # BitSize cannot be given since there is no event created on this wire
        # Set to None to make sure that it will be changed
        self.bitSize = None

class TracerVCD(object):
    """
    A tracer for VCD output. Should only be used for binary signals!
    """
    def __init__(self, uid, server, filename):
        """
        Constructor

        :param uid: the UID of the tracer
        :param server: the server to make remote requests on
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
            self.vcd_file = open(self.filename, 'a+')
        else:
            self.vcd_file = open(self.filename, 'w')
        self.vcd_varList = []
        self.vcd_prevtime = 0.0
        self.vcdHeader()

    def stopTracer(self):
        """
        Stop the tracer
        """
        self.vcd_file.flush()

    def vcdHeader(self):
        """
        Create the VCD file header by doing calls to the coordinator
        """
        self.vcd_file.write(("$date\n").encode())
        from datetime import date
        self.vcd_file.write(("\t" + date.today().isoformat() + "\n" +
                            "$end\n" +
                            "$version\n" +
                            "\tPyDEVS VCD export\n" +
                            "$end\n" +
                            "$comment\n" +
                            "\tGenerated from DEVS-code\n" +
                            "$end\n" +
                            "$timescale 1ns $end\n").encode())
        variables = self.server.getProxy(0).getVCDVariables()
        counter = 0
        for i in variables:
            model, port = i
            self.vcd_varList.append(VCDRecord(counter, model, port))
            counter += 1

        modelList = []
        for i in range(len(self.vcd_varList)):
            if self.vcd_varList[i].modelName not in modelList:
                modelList.append(self.vcd_varList[i].modelName)
        for module in modelList:
            self.vcd_file.write(("$scope " + str(module) + " " + str(module) + " $end\n").encode())
            for var in range(len(self.vcd_varList)):
                if self.vcd_varList[var].modelName == module:
                    self.vcd_file.write("$var wire ".encode())
                    if self.vcd_varList[var].bitSize is None:
                        self.vcd_file.write("1".encode())
                    else:
                        self.vcd_file.write(str(self.vcd_varList[var].bitSize).encode())
                    self.vcd_file.write((" " + str(self.vcd_varList[var].identifier) + " " + str(self.vcd_varList[var].portName) + " $end\n").encode())
            self.vcd_file.write(("$upscope $end\n").encode())
        self.vcd_file.write(("$enddefinitions $end\n").encode())
        self.vcd_file.write(("$dumpvars \n").encode())
        for var in range(len(self.vcd_varList)):
            self.vcd_file.write(("b").encode())
            if self.vcd_varList[var].bitSize is None:
                # The wire is a constant error signal, so the wire is never used
                # Assume 1 bit long
                self.vcd_file.write(("z").encode())
            else:
                for i in range(self.vcd_varList[var].bitSize):
                    self.vcd_file.write(("z").encode())
            self.vcd_file.write((" " + str(self.vcd_varList[var].identifier) + "\n").encode())
        self.vcd_file.write(("$end\n").encode())

    def trace(self, modelName, time, portName, vcdState):
        """
        Trace a VCD entry

        :param modelName: name of the model
        :param time: time at which transition happened
        :param portName: name of the port
        :param vcdState: state to trace on the specified port
        """
        # Check if the signal is a valid binary signal
        for i in range(len(vcdState)):
            if (i == 0):
                if vcdState[i] == 'b':
                    continue
                else:
                    raise DEVSException("Port " + portName + " in model " + modelName + " does not carry a binary signal\n" +
                            "VCD exports should carry a binary signal, not: " + str(vcdState))
            char = vcdState[i]
            if char not in ["0", "1", "E", "x"]:
                raise DEVSException("Port " + portName + " in model " + modelName + " does not carry a binary signal\n" +
                          "VCD exports should carry a binary signal, not: " + str(vcdState))
        # Find the identifier of this wire
        for i in range(len(self.vcd_varList)):
            if self.vcd_varList[i].modelName == modelName and self.vcd_varList[i].portName == portName:
                identifier = str(self.vcd_varList[i].identifier)
                break
            # If the bitSize is not yet defined, define it now
            if self.vcd_varList[i].bitSize is None:
                self.vcd_varList[i].bitSize = len(vcdState)-1
            elif self.vcd_varList[i].bitSize != len(vcdState) - 1:
                raise DEVSException("Wire has changing bitsize!\nYou are probably not using bit encoding on the wires!")
            # Now we have to convert between logisim and VCD notation
            vcdState = vcdState.replace('x', 'z')
            vcdState = vcdState.replace('E', 'x')
            # identifier will be defined, otherwise the record was not in the list
            if time > self.vcd_prevtime:
                # Convert float to integer without losing precision
                # ex. 5.0 --> 50, 5.5 --> 55
                t = time[0]
            vcdTime = int(str(int(floor(t))) + str(int(t - floor(t)) * (len(str(t)) - 2)))

            if (self.vcd_prevtime != vcdTime):
                # The time has passed, so add a new VCD header
                self.vcd_file.write(("#" + str(vcdTime) + "\n").encode())
                self.vcd_prevtime = vcdTime

        self.vcd_file.write((vcdState + " " + identifier + "\n").encode())

    def traceConfluent(self, aDEVS):
        """
        The trace functionality for VCD output at a confluent transition

        :param aDEVS: the model that transitioned
        """
        name = toStr(aDEVS.getModelFullName())
        for I in range(len(aDEVS.IPorts)):
            portName = aDEVS.IPorts[I].getPortName()
            signalBag = aDEVS.myInput.get(aDEVS.IPorts[I], [])
            if signalBag is not None:
                for portSignal in signalBag:
                    runTraceAtController(self.server, self.uid, aDEVS, [name, aDEVS.timeLast, toStr(portName), toStr(portSignal)])
        for I in range(len(aDEVS.OPorts) ):
            if aDEVS.OPorts[I] in aDEVS.myOutput:
                portName = aDEVS.OPorts[I].getPortName()
                signalBag = aDEVS.myOutput.get(aDEVS.OPorts[I], [])
                if signalBag is not None:
                    for portSignal in signalBag:
                        runTraceAtController(self.server, self.uid, aDEVS, [name, aDEVS.timeLast, toStr(portName), toStr(portSignal)])

    def traceInternal(self, aDEVS):
        """
        The trace functionality for VCD output at an internal transition

        :param aDEVS: the model that transitioned
        """
        name = toStr(aDEVS.getModelFullName())
        for I in range(0, len(aDEVS.OPorts) ):
            if aDEVS.OPorts[I] in aDEVS.myOutput:
                portName = aDEVS.OPorts[I].getPortName()
                signalBag = aDEVS.myOutput.get(aDEVS.OPorts[I], [])
                if signalBag is not None:
                    for portSignal in signalBag:
                        runTraceAtController(self.server, self.uid, aDEVS, [name, aDEVS.timeLast, toStr(portName), toStr(portSignal)])

    def traceExternal(self, aDEVS):
        """
        The trace functionality for VCD output at an external transition

        :param aDEVS: the model that transitioned
        """
        name = toStr(aDEVS.getModelFullName())
        for I in range(len(aDEVS.IPorts)):
            portName = aDEVS.IPorts[I].getPortName()
            signalBag = aDEVS.myInput.get(aDEVS.IPorts[I], [])
            if signalBag is not None:
                for portSignal in signalBag:
                    runTraceAtController(self.server, self.uid, aDEVS, [name, aDEVS.timeLast, toStr(portName), toStr(portSignal)])

    def traceInit(self, aDEVS):
        """
        The trace functionality for VCD output at initialisation

        :param aDEVS: the model that was initialized
        """
        pass
