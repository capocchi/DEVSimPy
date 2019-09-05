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

from pypdevs.util import runTraceAtController, toStr
from pypdevs.activityVisualisation import visualizeMatrix
import sys

class TracerCell(object):
    """
    A tracer for Cell-DEVS style tracing output
    """
    def __init__(self, uid, server, filename, x_size, y_size, multifile):
        """
        Constructor

        :param uid: the UID of this tracer
        :param server: the server to make remote calls on
        :param filename: filename to save to
        :param x_size: the x size of the grid
        :param y_size: the y size of the grid
        :param multifile: whether or not multiple files should be generated for each timestep
        """
        if server.getName() == 0:
            self.filename = filename
        else:
            self.filename = None
        self.server = server
        self.uid = uid
        self.x_size = x_size
        self.y_size = y_size
        self.multifile = multifile
        self.prevtime = 0.0

    def startTracer(self, recover):
        """
        Starts up the tracer

        :param recover: whether or not this is a recovery call (so whether or not the file should be appended to)
        """
        if self.filename is None:
            return
        elif recover:
            if not self.multifile:
                self.cell_realfile = open(self.filename, 'a+')
        else:
            if not self.multifile:
                self.cell_realfile = open(self.filename, 'w')
        self.cell_count = 0
        self.cells = [[None] * self.y_size for _ in range(self.x_size)]

    def stopTracer(self):   
        """
        Stop the tracer
        """
        if not self.multifile:
            self.cell_realfile.flush()

    def traceInit(self, aDEVS, t):
        """
        The trace functionality for Cell DEVS output at initialisation

        :param aDEVS: the model that was initialised
        :param t: time at which it should be traced
        """
        try:
            runTraceAtController(self.server, 
                                 self.uid, 
                                 aDEVS, 
                                 [aDEVS.x, 
                                    aDEVS.y, 
                                    t, 
                                    toStr(aDEVS.state.toCellState())])
        except AttributeError:
            pass

    def traceInternal(self, aDEVS):
        """
        The trace functionality for Cell DEVS output at an internal transition

        :param aDEVS: the model that transitioned
        """
        try:
            runTraceAtController(self.server, 
                                 self.uid, 
                                 aDEVS, 
                                 [aDEVS.x, 
                                    aDEVS.y, 
                                    aDEVS.time_last, 
                                    toStr(aDEVS.state.toCellState())])
        except AttributeError:
            pass

    def traceExternal(self, aDEVS):
        """
        The trace functionality for Cell DEVS output at an external transition

        :param aDEVS: the model that transitioned
        """
        try:
            runTraceAtController(self.server, 
                                 self.uid, 
                                 aDEVS, 
                                 [aDEVS.x, 
                                    aDEVS.y, 
                                    aDEVS.time_last, 
                                    toStr(aDEVS.state.toCellState())])
        except AttributeError:
            pass

    def traceConfluent(self, aDEVS):
        """
        The trace functionality for Cell DEVS output at a confluent transition

        :param aDEVS: the model that transitioned
        """
        try:
            runTraceAtController(self.server, 
                                 self.uid, 
                                 aDEVS, 
                                 [aDEVS.x, 
                                    aDEVS.y, 
                                    aDEVS.time_last, 
                                    toStr(aDEVS.state.toCellState())])
        except AttributeError as e:
            print(e)
            pass

    def trace(self, x, y, time, state):
        """
        Save the state of the cell

        :param x: the x coordinate of the model, to be used when plotting
        :param y: the y coordinate of the model, to be used when plotting
        :param time: the time when the model assumed this state
        :param state: the actual state to print
        """
        # Strip of the age for Cell DEVS
        time = time[0]
        if time != self.prevtime:
            # Frist flush the grid
            self.cell_count += 1
            if self.multifile:
                self.cell_realfile = open(self.filename % self.cell_count, 'w')
            else:
                self.cell_realfile.write("== At time %s ===\n" % (self.prevtime))
            visualizeMatrix(self.cells, "%s", self.cell_realfile)
            self.prevtime = time
            if self.multifile:
                self.cell_realfile.close()
        self.cells[x][y] = state
