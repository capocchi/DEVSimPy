import sys
sys.path.append('../../src/')

from infinity import *
from DEVS import AtomicDEVS, CoupledDEVS
from math import exp

T_AMBIENT = 27.0
T_IGNITE = 300.0
T_GENERATE = 500.0
T_BURNED = 60.0
TIMESTEP = 0.01
PH_INACTIVE = 'inactive'
PH_UNBURNED = 'unburned'
PH_BURNING = 'burning'
PH_BURNED = 'burned'
RADIUS = 3
TMP_DIFF = 1.0

#########################################
## Map layout
#########################################
## x_max = 6, y_max = 6
#########################################
##   0 1 2 3 4 5 6
## 0
## 1
## 2
## 3
## 4
## 5
## 6
#########################################
#########################################

def getPhaseFor(temp, phase):
    if temp > T_IGNITE or (temp > T_BURNED and phase == PH_BURNING):
        return PH_BURNING
    elif temp < T_BURNED and phase == PH_BURNING:
        return PH_BURNED
    else:
        return PH_UNBURNED

class CellState(object):
    # Simply here for future necessity
    def __init__(self, temp):
        self.temperature = temp
        self.igniteTime = float('inf')
        self.currentTime = 0.0
        self.phase = PH_INACTIVE
        self.surroundingTemps = [T_AMBIENT] * 4
        self.oldTemperature = temp

    def __str__(self):
        return "%s (T: %f)" % (self.phase, self.temperature)

    def copy(self):
        a = CellState(self.temperature)
        a.igniteTime = self.igniteTime
        a.currentTime = self.currentTime
        a.phase = self.phase
        a.surroundingTemps = list(self.surroundingTemps)
        a.oldTemperature = self.oldTemperature
        return a

    def __eq__(self, other):
        return self.temperature == other.temperature and self.igniteTime == other.igniteTime and self.currentTime == other.currentTime and self.phase == other.phase and self.surroundingTemps == other.surroundingTemps and self.oldTemperature == other.oldTemperature

    def toCellState(self):
        return self.temperature

class Cell(AtomicDEVS):
    def __init__(self, x, y, x_max, y_max):
        AtomicDEVS.__init__(self, "Cell(%d, %d)" % (x, y))
        
        self.state = CellState(T_AMBIENT)

        # For Cell DEVS tracing
        self.x = x
        self.y = y

        self.inports = [self.addInPort("in_N"), self.addInPort("in_E"), self.addInPort("in_S"), self.addInPort("in_W"), self.addInPort("in_G")]
        self.outport = self.addOutPort("out_T")

        self.taMap = {PH_INACTIVE: INFINITY, PH_UNBURNED: 1.0, PH_BURNING: 1.0, PH_BURNED: INFINITY}

    def preActivityCalculation(self):
        return None

    def postActivityCalculation(self, _):
        return self.state.temperature - T_AMBIENT

    def intTransition(self):
        #for _ in range(4100):
        #    pass
        # First check for the surrounding cells and whether we are on a border or not
        self.state.currentTime += self.timeAdvance()
        # OK, now we have a complete list
        if abs(self.state.temperature - self.state.oldTemperature) > TMP_DIFF:
            self.state.oldTemperature = self.state.temperature

        if self.state.phase == PH_BURNED:
            # Don't do anything as we are already finished
            return self.state
        elif self.state.phase == PH_BURNING:
            newTemp = 0.98689 * self.state.temperature + 0.0031 * (sum(self.state.surroundingTemps)) + 2.74 * exp(-0.19 * (self.state.currentTime * TIMESTEP - self.state.igniteTime)) + 0.213
        elif self.state.phase == PH_UNBURNED:
            newTemp = 0.98689 * self.state.temperature + 0.0031 * (sum(self.state.surroundingTemps)) + 0.213

        newPhase = getPhaseFor(newTemp, self.state.phase)
        if newPhase == PH_BURNED:
            newTemp = T_AMBIENT
        if self.state.phase == PH_UNBURNED and newPhase == PH_BURNING:
            self.state.igniteTime = self.state.currentTime * TIMESTEP

        self.state.phase = newPhase
        self.state.temperature = newTemp
        return self.state

    def extTransition(self, inputs):
        # NOTE we can make the assumption that ALL temperatures are received simultaneously, due to Parallel DEVS being used
        self.state.currentTime += self.elapsed
        if self.inports[-1] in inputs:
            # A temperature from the generator, so simply set our own temperature
            self.state.temperature = inputs[self.inports[-1]][0]
            self.state.phase = getPhaseFor(self.state.temperature, self.state.phase)
            if self.state.phase == PH_BURNING:
                self.state.igniteTime = self.state.currentTime * TIMESTEP
        else:
            for num, inport in enumerate(self.inports[:4]):
                self.state.surroundingTemps[num] = inputs.get(inport, [self.state.surroundingTemps[num]])[0]

        if self.state.phase == PH_INACTIVE:
            self.state.phase = PH_UNBURNED
        return self.state

    def outputFnc(self):
        if abs(self.state.temperature - self.state.oldTemperature) > TMP_DIFF:
            return {self.outport: [self.state.temperature]}
        else:
            return {}
            
    def timeAdvance(self):
        return self.taMap[self.state.phase]

class Junk(object):
    def __init__(self):
        self.status = True

    def __str__(self):
        return "Generator"

    def copy(self):
        a = Junk()
        a.status = self.status
        return a

class Generator(AtomicDEVS):
    def __init__(self, levels):
        AtomicDEVS.__init__(self, "Generator")
        self.outports = []
        for i in range(levels):
            self.outports.append(self.addOutPort("out_" + str(i)))
        self.state = Junk()

    def intTransition(self):
        self.state.status = False
        return self.state

    def outputFnc(self):
        output = {}
        for i in range(len(self.outports)):
            output[self.outports[i]] = [T_AMBIENT + T_GENERATE/(2**i)]
        return output

    def timeAdvance(self):
        if self.state.status:
            return 1.0
        else:
            return INFINITY

    def preActivityCalculation(self):
        return None

    def postActivityCalculation(self, _):
        return 0.0

class FireSpread(CoupledDEVS):
    def putGenerator(self, x, y):
        CENTER = (x, y)
        for level in range(RADIUS):
            # Left side
            y = level
            for x in range(-level, level + 1, 1):
                self.connectPorts(self.generator.outports[level], self.cells[CENTER[0] + x][CENTER[1] + y].inports[-1])
                self.connectPorts(self.generator.outports[level], self.cells[CENTER[0] + x][CENTER[1] - y].inports[-1])
            x = level
            for y in range(-level + 1, level, 1):
                self.connectPorts(self.generator.outports[level], self.cells[CENTER[0] + x][CENTER[1] + y].inports[-1])
                self.connectPorts(self.generator.outports[level], self.cells[CENTER[0] - x][CENTER[1] + y].inports[-1])
        
    def __init__(self, x_max, y_max):
        CoupledDEVS.__init__(self, "FireSpread")

        self.cells = []
        try:
            from mpi4py import MPI
            nodes = MPI.COMM_WORLD.Get_size()
        except ImportError:
            nodes = 1
        node = 0
        totalCount = x_max * y_max
        counter = 0
        for x in range(x_max):
            row = []
            for y in range(y_max):
                if nodes == 1:
                    node = 0
                elif x <= x_max/2 and y < y_max/2:
                    node = 0
                elif x <= x_max/2 and y > y_max/2:
                    node = 1
                elif x > x_max/2 and y < y_max/2:
                    node = 2
                elif x > x_max/2 and y > y_max/2:
                    node = 3
                row.append(self.addSubModel(Cell(x, y, x_max, y_max), node))
            self.cells.append(row)
            counter += 1

        # Everything is now constructed, so connect the ports now
        self.generator = self.addSubModel(Generator(RADIUS))
        #self.putGenerator(2, 2)
        #self.putGenerator(2, y_max-3)
        #self.putGenerator(x_max-3, 2)
        #self.putGenerator(x_max-3, y_max-3)
        self.putGenerator(5, 5)

        for x in range(x_max):
            for y in range(y_max):
                if x != 0:
                    self.connectPorts(self.cells[x][y].outport, self.cells[x-1][y].inports[2])
                if y != y_max - 1:
                    self.connectPorts(self.cells[x][y].outport, self.cells[x][y+1].inports[1])
                if x != x_max - 1:
                    self.connectPorts(self.cells[x][y].outport, self.cells[x+1][y].inports[3])
                if y != 0:
                    self.connectPorts(self.cells[x][y].outport, self.cells[x][y-1].inports[0])
