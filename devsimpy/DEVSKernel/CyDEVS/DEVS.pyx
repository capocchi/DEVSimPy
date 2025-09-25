# cython: language_level=3
import sys
import copy
cdef double INFINITY = float('inf')

cdef class Port:
    cdef public object inLine, outLine, host, name, myID
    def __init__(self, name=""):
        self.inLine = []
        self.outLine = []
        self.host = None
        self.name = name
        self.myID = None
    def __str__(self):
        return self.name

cdef class IPort(Port):
    def __init__(self, name=""):
        Port.__init__(self, name)
        self.name = "IN" + str(self.myID)
    def type(self):
        return "INPORT"

cdef class OPort(Port):
    def __init__(self, name=""):
        Port.__init__(self, name)
        self.name = "OUT" + str(self.myID)
    def type(self):
        return "OUTPORT"

cdef class BaseDEVS:
    cdef public object parent, myID, name, IPorts, OPorts, myInput, myOutput
    def __init__(self, name=""):
        self.parent = None
        self.myID = None
        self.name = name
        self.IPorts = []
        self.OPorts = []
        self.myInput = {}
        self.myOutput = {}
    def addInPort(self):
        port = IPort()
        port.myID = len(self.IPorts)
        port.name = "IN%d" % port.myID
        port.host = self
        self.IPorts.append(port)
        return port
    def addOutPort(self):
        port = OPort()
        port.myID = len(self.OPorts)
        port.name = "OUT%d" % port.myID
        port.host = self
        self.OPorts.append(port)
        return port
    def __str__(self):
        return self.myID

cdef class AtomicDEVS(BaseDEVS):
    cdef public double elapsed
    cdef public dict state
    AtomicIDCounter = 0
    def __init__(self, name=""):
        BaseDEVS.__init__(self, name)
        AtomicDEVS.AtomicIDCounter += 1
        self.myID = "A%d" % AtomicDEVS.AtomicIDCounter
        self.elapsed = 0.
        self.state = {}
    def poke(self, p, v):
        self.myOutput[p] = v
    def peek(self, p):
        value = self.myInput.get(p, None)
        return copy.deepcopy(value) if value else value
    def peek_all(self):
        return [(p, copy.deepcopy(m)) for p, m in list(self.myInput.items())]
    def extTransition(self):
        pass
    def intTransition(self):
        pass
    def outputFnc(self):
        pass
    def timeAdvance(self):
        pass
    def __str__(self):
        return self.myID

cdef class CoupledDEVS(BaseDEVS):
    CoupledIDCounter = 0
    cdef public object componentSet, IC, EIC, EOC
    def __init__(self, name=""):
        BaseDEVS.__init__(self, name)
        CoupledDEVS.CoupledIDCounter += 1
        self.myID = "C%d" % CoupledDEVS.CoupledIDCounter
        self.componentSet = []
        self.IC = []
        self.EIC = []
        self.EOC = []
    def addSubModel(self, model):
        self.componentSet.append(model)
        model.parent = self
        return model
    def connectPorts(self, p1, p2):
        if ((p1.host.parent == self and p2.host.parent == self) and (isinstance(p1, OPort) and isinstance(p2, IPort))):
            if p1.host == p2.host:
                raise Exception('Direct feedback coupling parent not allowed')
            else:
                self.IC.append(((p1.host, p1), (p2.host, p2)))
                p1.outLine.append(p2)
                p2.inLine.append(p1)
        elif ((p1.host == self and p2.host.parent == self) and (isinstance(p1, IPort) and isinstance(p2, IPort))):
            self.EIC.append(((p1.host, p1), (p2.host, p2)))
            p1.outLine.append(p2)
            p2.inLine.append(p1)
        elif ((p1.host.parent == self and p2.host == self) and (isinstance(p1, OPort) and isinstance(p2, OPort))):
            self.EOC.append(((p1.host, p1), (p2.host, p2)))
            p1.outLine.append(p2)
            p2.inLine.append(p1)
        else:
            raise Exception("Illegal coupling!")
    def select(self, immList):
        for model in self.componentSet:
            if model in immList:
                return model
        return immList[0]
    def __str__(self):
        return self.myID