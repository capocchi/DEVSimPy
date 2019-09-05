# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# tracers.py --- trace output
#                     --------------------------------
#                            Copyright (c) 2012
#                             Hans  Vangheluwe
#                            Yentl Van Tendeloo
#                       McGill University (Montréal)
#                     --------------------------------
# Version 1.1                                        last modified: 09/09/12
#  - Added VCD record for VCD trace file output
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import sys
import time
from .util import execute, easyCommand, toStr, DEVSException, getProxy, EPSILON
from math import floor

### VCD helper class (actually more of a struct)

class VCDRecord(object):
    """
    A data class to keep information about VCD variables
    """

    def __init__(self, identifierNr, modelName, portName):
        """
        Constructor
        """
        self.modelName = modelName
        self.portName = portName
        self.identifier = identifierNr
        # BitSize cannot be given since there is no event created on this wire
        # Set to None to make sure that it will be changed
        self.bitSize = None

##### MAIN output functions, these will be called and are used
#                            to delegate all tracing

class Tracers(object):
    """
    The main tracer object that does all tracing
    """
    def __init__(self):
        """
        Constructor, sets all tracing options to False
        """
        self.verbose = False
        self.verb_file = None
        self.verb_prevtime = 0
        self.immediate = False

        self.xml = False
        self.xml_file = None

        self.vcd = False
        self.vcd_file = None
        self.vcd_prevtime = 0

    def tracesInternal(self, aDEVS):
        """
        Perform all necessary tracing for an internal transition of the specified model
        Args:
            aDEVS - the model that transitioned
        """
        if self.verbose:
            self.verboseInternal(aDEVS)
        if self.xml:
            self.xmlInternal(aDEVS)
        if self.vcd:
            self.vcdInternal(aDEVS)

    def tracesInit(self, aDEVS):
        """
        Perform all necessary tracing for an initialisation transition of the specified model
        Args:
            aDEVS - the model that was initialized
        """
        if self.verbose:
            self.verboseInit(aDEVS)
        if self.xml:
            self.xmlInit(aDEVS)
        if self.vcd:
            self.vcdInit(aDEVS)

    def tracesExternal(self, aDEVS):
        """
        Perform all necessary tracing for an external transition of the specified model
        Args:
            aDEVS - the model that transitioned
        """
        if self.verbose:
            self.verboseExternal(aDEVS)
        if self.xml:
            self.xmlExternal(aDEVS)
        if self.vcd:
            self.vcdExternal(aDEVS)

    def tracesConfluent(self, aDEVS):
        """
        Perform all necessary tracing for a confluent transition of the specified model
        Args:
            aDEVS - the model that transitioned
        """
        if self.verbose:
            self.verboseConfluent(aDEVS)
        if self.xml:
            self.xmlConfluent(aDEVS)
        if self.vcd:
            self.vcdConfluent(aDEVS)

    def startTracers(self):
        """
        Start up all specified tracers by e.g. creating the files that will contain the logs
        """
        if self.verbose:
            pass
        if self.xml:
            self.initXML()
        if self.vcd:
            self.initVCD()

    def stopTracers(self):
        """
        Stop all specified tracers by e.g. flushing the files that contain the logs
        """
        if self.verbose:
            self.verb_file.flush()
        if self.xml:
            self.xml_file.write("</trace>")
            self.xml_file.flush()
        if self.vcd:
            self.vcd_file.flush()

    def setImmediate(self, immediate):
        """
        Configure whether or not all tracing should happen immediately or only after GVT has passed
        Args:
            immediate - boolean whether tracing should be shown immediately
        """
        self.immediate = immediate

##### VERBOSE output function

    def setVerbose(self, verb, file = None, restore = False):
        """
        Configure the verbose tracing subcomponent
        Args:
            verb - whether or not to perform this kind of tracing, if set to False, other parameters are unimportant
            file - the file to write verbose traces to, can be None to direct tracing to stdout
            restore - whether or not an append to a previously existing file should happen
        """
        self.verbose = verb

        if file is None:
            self.verb_file = sys.stdout
        elif restore == False:
            self.verb_file = open(file, 'w')
        elif restore == True:
            self.verb_file = open(file, 'a+')

        self.verb_prevtime = [-1, -1]

    def traceVerbose(self, time, text):
        """
        Perform the actual outputting of the trace
        Args:
            time - time at which the transition happened
            text - the text to show
        """
        string = ""
        #if (abs(time[0] - self.verb_prevtime[0]) > EPSILON) or (self.verb_prevtime[1] != time[1]):
        if time > self.verb_prevtime:
            string = ("\n__  Current Time: %10.2f " + "_"*42 + " \n\n") % (time[0])
            self.verb_prevtime = time
        string += "%s\n" % text
        try:
            self.verb_file.write(string)
        except TypeError:
            self.verb_file.write(string.encode())

    def verboseInit(self, aDEVS):
        """
        The trace functionality for verbose output at the initialisation step
        Args:
            aDEVS - the model that transitioned
        """
        text = ""
        text += "\n\tINITIAL CONDITIONS in model <%s>\n" % aDEVS.getModelFullName()
        text += "\t  Initial State: %s\n" % str(aDEVS.state)
        # Don't show the age
        text += "\t  Next scheduled internal transition at time %5f\n" % (aDEVS.timeNext[0])
        execute(aDEVS, easyCommand("self.tracers.traceVerbose", [aDEVS.timeLast, '"' + text + '"']), self.immediate)

    def verboseInternal(self, aDEVS):
        """
        The trace functionality for verbose output at an internal transition
        Args:
            aDEVS - the model that transitioned
        """
        text = ""
        text += "\n\tINTERNAL TRANSITION in model <%s>\n" % aDEVS.getModelFullName()
        text += "\t  New State: %s\n" % str(aDEVS.state)
        text += "\t  Output Port Configuration:\n"
        for I in range(len(aDEVS.OPorts)):
            if aDEVS.OPorts[I] in aDEVS.myOutput:
                text += "\t    port <" + str(aDEVS.OPorts[I].getPortName()) + ">: \n"
                for msg in aDEVS.myOutput[aDEVS.OPorts[I]]:
                    text += "\t       " + str(msg) + "\n"
            else:
                text += "\t    port%d: NoEvent\n" % (I)
        # Don't show the age
        text += "\t  Next scheduled internal transition at time %5f\n" % (aDEVS.timeNext[0])
        execute(aDEVS, easyCommand("self.tracers.traceVerbose", [aDEVS.timeLast, '"' + text + '"']), self.immediate)

    def verboseConfluent(self, aDEVS):
        """
        The trace functionality for verbose output at a confluent transition
        Args:
            aDEVS - the model that transitioned
        """
        text = ""
        text += "\n\tCONFLUENT TRANSITION in model <%s>\n" % aDEVS.getModelFullName()
        text += "\t  Input Port Configuration:\n"
        for I in range(len(aDEVS.IPorts)):
            text += "\t    port <" + str(aDEVS.IPorts[I].getPortName()) + ">: \n"
            for msg in aDEVS.myInput.get(aDEVS.IPorts[I], []):
                text += "\t       " + str(msg) + "\n"
        text += "\t  New State: %s\n" % str(aDEVS.state)
        text += "\t  Output Port Configuration:\n"
        for I in range(len(aDEVS.OPorts)):
            text += "\t    port <" + str(aDEVS.OPorts[I].getPortName()) + ">:\n"
            for msg in aDEVS.myOutput.get(aDEVS.OPorts[I], []):
                text += "\t       " + str(msg) + "\n"
        # Don't show the age
        text += "\t  Next scheduled internal transition at time %5f\n" % (aDEVS.timeNext[0])
        execute(aDEVS, easyCommand("self.tracers.traceVerbose", [aDEVS.timeLast, '"' + text + '"']), self.immediate)

    def verboseExternal(self, aDEVS):
        """
        The trace functionality for verbose output at an external transition
        Args:
            aDEVS - the model that transitioned
        """
        text = ""
        text += "\n\tEXTERNAL TRANSITION in model <%s>\n" % aDEVS.getModelFullName()
        text += "\t  Input Port Configuration:\n"
        for I in range(len(aDEVS.IPorts)):
            text += "\t    port <" + str(aDEVS.IPorts[I].getPortName()) + ">:\n"
            for msg in aDEVS.myInput.get(aDEVS.IPorts[I], []):
                text += "\t       " + str(msg) + "\n"
        text += "\t  New State: %s\n" % str(aDEVS.state)
        # Don't show the age
        text += "\t  Next scheduled internal transition at time %5f\n" % (aDEVS.timeNext[0])
        execute(aDEVS, easyCommand("self.tracers.traceVerbose", [aDEVS.timeLast, '"' + text + '"']), self.immediate)

##### XML output function

    def setXML(self, xml):
        """
        Configure whether or not to use XML tracing
        Args:
            xml - boolean whether or not to enable XML tracing
        """
        self.xml = xml

    def initXML(self):
        """
        Initialize the XML tracer, creates the file 'devstrace.xml'
        """
        self.xml_file = open("devstrace.xml", "w")
        self.xml_file.write(("<?xml version=\"1.0\"?>\n" + "<trace>\n").encode())

    def saveXML(self, modelName, timeStamp, eventKind, portInfo, xmlState, strState):
        """
        Save an XML entry for the provided parameters, basically wraps it in the necessary tags
        Args:
            modelName - name of the model
            timeStamp - timestamp of the transition
            eventKind - kind of event that happened, e.g. internal, external, ...
            portInfo - actual information about the port
            xmlState - XML representation of the state
            strState - normal string representation of the state
        """
        self.xml_file.write(("<event>\n"
                          + "<model>" + modelName + "</model>\n"
                          + "<time>" + str(timeStamp) + "</time>\n"
                          + "<kind>" + eventKind + "</kind>\n"
                          + portInfo
                          + "<state>\n"+ xmlState + "<![CDATA[" + strState + "]]>\n</state>\n"
                          + "</event>\n").encode())

    def xmlInternal(self, aDEVS):
        """
        The trace functionality for XML output at an internal transition
        Args:
            aDEVS - the model that transitioned
        """
        portInfo = ""
        for I in range(len(aDEVS.OPorts)):
            if aDEVS.OPorts[I] in aDEVS.myOutput and aDEVS.myOutput[aDEVS.OPorts[I]] is not None:
                portInfo += "<port name=\""+ aDEVS.OPorts[I].getPortName()+"\" category=\"O\">\n"
                for j in aDEVS.myOutput[aDEVS.OPorts[I]]:
                    portInfo += "<message>" + str(j) + "</message>\n</port>\n"
        execute(aDEVS, easyCommand("self.tracers.saveXML", [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, "'IN'", toStr(portInfo), toStr(aDEVS.state.toXML()), toStr(aDEVS.state)]), self.immediate)

    def xmlExternal(self, aDEVS):
        """
        The trace functionality for XML output at an external transition
        Args:
            aDEVS - the model that transitioned
        """
        portInfo = ""
        for I in range(len(aDEVS.IPorts)):
            portInfo += "<port name=\""+ aDEVS.IPorts[I].getPortName()+"\" category=\"I\">\n"
            for j in aDEVS.peek(aDEVS.IPorts[I]):
                portInfo += "<message>" + str(j) + "</message>\n</port>\n"
        execute(aDEVS, easyCommand("self.tracers.saveXML", [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, "'EX'", toStr(portInfo), toStr(aDEVS.state.toXML()), toStr(aDEVS.state)]), self.immediate)

    def xmlConfluent(self, aDEVS):
        """
        The trace functionality for XML output at a confluent transition
        Args:
            aDEVS - the model that transitioned
        """
        portInfo = ""
        for I in range(len(aDEVS.IPorts)):
            portInfo += "<port name=\""+ aDEVS.IPorts[I].getPortName()+"\" category=\"I\">\n"
            for j in aDEVS.peek(aDEVS.IPorts[I]):
                portInfo += "<message>" + str(j) + "</message>\n</port>\n"
        execute(aDEVS, easyCommand("self.tracers.saveXML", [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, "'EX'", toStr(portInfo), toStr(aDEVS.state.toXML()), toStr(aDEVS.state)]), self.immediate)
        portInfo = ""
        for I in range(len(aDEVS.OPorts)):
            if aDEVS.OPorts[I] in aDEVS.myOutput:
                portInfo += "<port name=\""+ aDEVS.OPorts[I].getPortName()+"\" category=\"O\">\n"
                for j in aDEVS.myOutput[aDEVS.OPorts[I]]:
                    portInfo += "<message>" + str(j) + "</message>\n</port>\n"
        execute(aDEVS, easyCommand("self.tracers.saveXML", [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, "'IN'", toStr(portInfo), toStr(aDEVS.state.toXML()), toStr(aDEVS.state)]), self.immediate)

    def xmlInit(self, aDEVS):
        """
        The trace functionality for XML output at initialization
        Args:
            aDEVS - the model that was initialised
        """
        execute(aDEVS, easyCommand("self.tracers.saveXML", [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, "'EX'", "''", toStr(aDEVS.state.toXML()), toStr(aDEVS.state)]), self.immediate)

##### VCD output function

    def setVCD(self, vcd):
        """
        Whether or not VCD tracing should be enabled
        Args:
            vcd - whether or not VCD tracing should be enabled
        """
        self.vcd = vcd

    def vcdTimeAdvance(self, t):
        """
        Advance the time for VCD tracing
        Args:
            t - the new time
        """
        if self.vcd:
            # Convert float to integer without losing precision
            # ex. 5.0 --> 50, 5.5 --> 55
            vcdTime = int(str(int(floor(t))) + str(int(t - floor(t)) * (len(str(t)) - 2)))

            if (self.vcd_prevtime != vcdTime):
                # The time has passed, so add a new VCD header
                self.vcd_file.write(("#" + str(vcdTime) + "\n").encode())
                self.vcd_prevtime = vcdTime

    def initVCD(self):
        """
        Initialise VCD tracing, creates the file 'devstrace.vcd'
        """
        self.vcd_varList = []
        self.vcd_file = open("devstrace.vcd", "w")
        self.vcd_prevtime = 0.0

    def saveVCD(self, modelName, time, portName, vcdState):
        """
        Trace a VCD entry
        Args:
            modelName - the name of the model
            time - time at which transition happened
            portName - name of the port
            vcdState - state to trace on the specified port
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
                recordNr = i
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

    def vcdConfluent(self, aDEVS):
        """
        The trace functionality for VCD output at a confluent transition
        Args:
            aDEVS - the model that transitioned
        """
        name = aDEVS.getModelFullName()
        for I in range(len(aDEVS.IPorts)):
            portName = aDEVS.IPorts[I].getPortName()
            signalBag = aDEVS.peek(aDEVS.IPorts[I])
            if signalBag is not None:
                for portSignal in signalBag:
                    execute(aDEVS, easyCommand("self.tracers.saveVCD", [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, toStr(portName), toStr(portSignal)]), self.immediate)
        for I in range(len(aDEVS.OPorts) ):
            if aDEVS.OPorts[I] in aDEVS.myOutput:
                portName = aDEVS.OPorts[I].getPortName()
                signalBag = aDEVS.myOutput[aDEVS.OPorts[I]]
                if signalBag is not None:
                    for portSignal in signalBag:
                        execute(aDEVS, easyCommand("self.tracers.saveVCD", [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, toStr(portName), toStr(portSignal)]), self.immediate)

    def vcdInternal(self, aDEVS):
        """
        The trace functionality for VCD output at an internal transition
        Args:
            aDEVS - the model that transitioned
        """
        for I in range(0, len(aDEVS.OPorts) ):
            if aDEVS.OPorts[I] in aDEVS.myOutput:
                portName = aDEVS.OPorts[I].getPortName()
                signalBag = aDEVS.myOutput[aDEVS.OPorts[I]]
                if signalBag is not None:
                    for portSignal in signalBag:
                        execute(aDEVS, easyCommand("self.tracers.saveVCD", [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, toStr(portName), toStr(portSignal)]), self.immediate)

    def vcdExternal(self, aDEVS):
        """
        The trace functionality for VCD output at an external transition
        Args:
            aDEVS - the model that transitioned
        """
        for I in range(len(aDEVS.IPorts)):
            portName = aDEVS.IPorts[I].getPortName()
            signalBag = aDEVS.peek(aDEVS.IPorts[I])
            if signalBag is not None:
                for portSignal in signalBag:
                    execute(aDEVS, easyCommand("self.tracers.saveVCD", [toStr(aDEVS.getModelFullName()), aDEVS.timeLast, toStr(portName), toStr(portSignal)]), self.immediate)

    def vcdInit(self, aDEVS):
        """
        The trace functionality for VCD output at initialisation
        Args:
            aDEVS - the model that is initialized
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
        variables = getProxy(aDEVS.rootsim.controller_name).getVCDVariables()
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
