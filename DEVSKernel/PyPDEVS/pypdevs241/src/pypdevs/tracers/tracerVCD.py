# Copyright 2014 Modelling, Simulation and Design Lab (MSDL) at 
# McGill University and the University of Antwerp (http://msdl.cs.mcgill.ca/)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pypdevs.util import runTraceAtController, toStr, DEVSException
from math import floor

class VCDRecord(object):
    """
    A data class to keep information about VCD variables
    """

    def __init__(self, identifier_nr, model_name, port_name):
        """
        Constructor.

        :param identifier_nr: the actual identifier
        :param model_name: name of the model
        :param port_name: name of the port
        """
        self.model_name = model_name
        self.port_name = port_name
        self.identifier = identifier_nr
        # BitSize cannot be given since there is no event created on this wire
        # Set to None to make sure that it will be changed
        self.bit_size = None

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
        self.vcd_var_list = []
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
            self.vcd_var_list.append(VCDRecord(counter, model, port))
            counter += 1

        modelList = []
        for i in range(len(self.vcd_var_list)):
            if self.vcd_var_list[i].model_name not in modelList:
                modelList.append(self.vcd_var_list[i].model_name)
        for module in modelList:
            self.vcd_file.write(("$scope %s %s $end\n" % (module, module)).encode())
            for var in range(len(self.vcd_var_list)):
                if self.vcd_var_list[var].model_name == module:
                    self.vcd_file.write("$var wire ".encode())
                    if self.vcd_var_list[var].bit_size is None:
                        self.vcd_file.write("1".encode())
                    else:
                        bitsize = str(self.vcd_var_list[var].bit_size)
                        self.vcd_file.write(bitsize.encode())
                    self.vcd_file.write((" %s %s $end\n" 
                            % (self.vcd_var_list[var].identifier, 
                               self.vcd_var_list[var].port_name)).encode())
            self.vcd_file.write(("$upscope $end\n").encode())
        self.vcd_file.write(("$enddefinitions $end\n").encode())
        self.vcd_file.write(("$dumpvars \n").encode())
        for var in range(len(self.vcd_var_list)):
            self.vcd_file.write(("b").encode())
            if self.vcd_var_list[var].bit_size is None:
                # The wire is a constant error signal, so the wire is never used
                # Assume 1 bit long
                self.vcd_file.write(("z").encode())
            else:
                for i in range(self.vcd_var_list[var].bit_size):
                    self.vcd_file.write(("z").encode())
            self.vcd_file.write((" %s\n" % self.vcd_var_list[var].identifier).encode())
        self.vcd_file.write(("$end\n").encode())

    def trace(self, model_name, time, port_name, vcd_state):
        """
        Trace a VCD entry

        :param model_name: name of the model
        :param time: time at which transition happened
        :param port_name: name of the port
        :param vcd_state: state to trace on the specified port
        """
        # Check if the signal is a valid binary signal
        for i in range(len(vcd_state)):
            if (i == 0):
                if vcd_state[i] == 'b':
                    continue
                else:
                    raise DEVSException(("Port %s in model does not carry " +
                                        "a binary signal\n" +
                                        "VCD exports require a binary signal," +
                                        "not: ") % (port_name, model_name, vcd_state))
            char = vcd_state[i]
            if char not in ["0", "1", "E", "x"]:
                raise DEVSException(("Port %s in model does not carry " +
                                     "a binary signal\n" +
                                     "VCD exports require a binary signal," +
                                     "not: ") % (port_name, model_name, vcd_state))
        # Find the identifier of this wire
        for i in range(len(self.vcd_var_list)):
            if (self.vcd_var_list[i].model_name == model_name and 
                    self.vcd_var_list[i].port_name == port_name):
                identifier = str(self.vcd_var_list[i].identifier)
                break
            # If the bit_size is not yet defined, define it now
            if self.vcd_var_list[i].bit_size is None:
                self.vcd_var_list[i].bit_size = len(vcd_state)-1
            elif self.vcd_var_list[i].bit_size != len(vcd_state) - 1:
                raise DEVSException("Wire has changing bitsize!\n" +
                                    "You are probably not using bit encoding!")
            # Now we have to convert between logisim and VCD notation
            vcd_state = vcd_state.replace('x', 'z')
            vcd_state = vcd_state.replace('E', 'x')
            # identifier will be defined, otherwise the record was not in the list
            if time > self.vcd_prevtime:
                # Convert float to integer without losing precision
                # ex. 5.0 --> 50, 5.5 --> 55
                t = time[0]
            vcd_time = int(str(int(floor(t))) + 
                          str(int(t - floor(t)) * (len(str(t)) - 2)))

            if (self.vcd_prevtime != vcd_time):
                # The time has passed, so add a new VCD header
                self.vcd_file.write(("#" + str(vcd_time) + "\n").encode())
                self.vcd_prevtime = vcd_time

        self.vcd_file.write((vcd_state + " " + identifier + "\n").encode())

    def traceConfluent(self, aDEVS):
        """
        The trace functionality for VCD output at a confluent transition

        :param aDEVS: the model that transitioned
        """
        name = toStr(aDEVS.getModelFullName())
        for I in range(len(aDEVS.IPorts)):
            port_name = aDEVS.IPorts[I].getPortName()
            signal_bag = aDEVS.my_input.get(aDEVS.IPorts[I], [])
            if signal_bag is not None:
                for port_signal in signal_bag:
                    runTraceAtController(self.server, 
                                         self.uid, 
                                         aDEVS, 
                                         [name, 
                                            aDEVS.time_last, 
                                            toStr(port_name), 
                                            toStr(port_signal)])
        for I in range(len(aDEVS.OPorts) ):
            if aDEVS.OPorts[I] in aDEVS.my_output:
                port_name = aDEVS.OPorts[I].getPortName()
                signal_bag = aDEVS.my_output.get(aDEVS.OPorts[I], [])
                if signal_bag is not None:
                    for port_signal in signal_bag:
                        runTraceAtController(self.server, 
                                             self.uid, 
                                             aDEVS, 
                                             [name, 
                                                aDEVS.time_last, 
                                                toStr(port_name), 
                                                toStr(port_signal)])

    def traceInternal(self, aDEVS):
        """
        The trace functionality for VCD output at an internal transition

        :param aDEVS: the model that transitioned
        """
        name = toStr(aDEVS.getModelFullName())
        for I in range(0, len(aDEVS.OPorts) ):
            if aDEVS.OPorts[I] in aDEVS.my_output:
                port_name = aDEVS.OPorts[I].getPortName()
                signal_bag = aDEVS.my_output.get(aDEVS.OPorts[I], [])
                if signal_bag is not None:
                    for port_signal in signal_bag:
                        runTraceAtController(self.server, 
                                             self.uid, 
                                             aDEVS, 
                                             [name, 
                                                aDEVS.time_last, 
                                                toStr(port_name), 
                                                toStr(port_signal)])

    def traceExternal(self, aDEVS):
        """
        The trace functionality for VCD output at an external transition

        :param aDEVS: the model that transitioned
        """
        name = toStr(aDEVS.getModelFullName())
        for I in range(len(aDEVS.IPorts)):
            port_name = aDEVS.IPorts[I].getPortName()
            signal_bag = aDEVS.my_input.get(aDEVS.IPorts[I], [])
            if signal_bag is not None:
                for port_signal in signal_bag:
                    runTraceAtController(self.server, 
                                         self.uid, 
                                         aDEVS, 
                                         [name, 
                                            aDEVS.time_last, 
                                            toStr(port_name), 
                                            toStr(port_signal)])

    def traceInit(self, aDEVS, t):
        """
        The trace functionality for VCD output at initialisation

        :param aDEVS: the model that was initialized
        :param t: time at which it should be traced
        """
        pass
