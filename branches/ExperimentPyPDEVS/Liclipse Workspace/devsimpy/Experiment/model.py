import sys
import os
import __builtin__

sys.path.append(os.path.join('..','DEVSKernel','PyDEVS'))
sys.path.append(os.path.join('..'))

__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"
__builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {\
	'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),\
	'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}

from DEVS import *
from Domain import *

#import Policeman
#import TrafficLight

class Coupled_Name3(CoupledDEVS):
    def __init__ (self, name):
        CoupledDEVS.__init__(self, name)
        self.addOutPort("OutPort_24")
        self.addInPort("InPort_23")

        self.Policeman_0=self.addSubModel(Policeman.Policeman("Policeman_0"))
        self.Policeman_0.addOutPort("OutPort_22")
        self.Policeman_0.addInPort("InPort_21")

        self.connectPorts(self.IPorts[0], self.Policeman_0.IPorts[0])
        self.connectPorts(self.Policeman_0.OPorts[0], self.OPorts[0])



class Coupled_Name(CoupledDEVS):
    def __init__ (self, name):
        CoupledDEVS.__init__(self, name)
        self.addOutPort("OutPort_30")
        self.addInPort("InPort_29")

        self.Coupled_Name3=self.addSubModel(Coupled_Name3("Coupled_Name3"))

        self.TrafficLight_1=self.addSubModel(TrafficLight.TrafficLight("TrafficLight_1"))
        self.TrafficLight_1.addOutPort("OutPort_26")
        self.TrafficLight_1.addInPort("InPort_25")

        self.TrafficLight_10=self.addSubModel(TrafficLight.TrafficLight("TrafficLight_10"))
        self.TrafficLight_10.addOutPort("OutPort_28")
        self.TrafficLight_10.addInPort("InPort_27")

        self.connectPorts(self.IPorts[0], self.Coupled_Name3.IPorts[0])
        self.connectPorts(self.IPorts[0], self.TrafficLight_1.IPorts[0])
        self.connectPorts(self.IPorts[0], self.TrafficLight_10.IPorts[0])
        self.connectPorts(self.Coupled_Name3.OPorts[0], self.OPorts[0])
        self.connectPorts(self.TrafficLight_1.OPorts[0], self.OPorts[0])
        self.connectPorts(self.TrafficLight_10.OPorts[0], self.OPorts[0])



class trafficLight(CoupledDEVS):
    def __init__ (self, name):
        CoupledDEVS.__init__(self, name)

        self.QuickScope_4=self.addSubModel(QuickScope.QuickScope("QuickScope_4"))
        self.QuickScope_4.addOutPort("OutPort_18")
        self.QuickScope_4.addInPort("InPort_17")

        self.Coupled_Name2=self.addSubModel(Coupled_Name2("Coupled_Name2"))

        self.Coupled_Name=self.addSubModel(Coupled_Name("Coupled_Name"))

        self.TrafficLight_2=self.addSubModel(TrafficLight.TrafficLight("TrafficLight_2"))
        self.TrafficLight_2.addOutPort("OutPort_32")
        self.TrafficLight_2.addInPort("InPort_31")

        self.Policeman_2=self.addSubModel(Policeman.Policeman("Policeman_2"))
        self.Policeman_2.addOutPort("OutPort_34")
        self.Policeman_2.addInPort("InPort_33")

        self.connectPorts(self.Coupled_Name2.OPorts[0], self.TrafficLight_2.IPorts[0])
        self.connectPorts(self.Policeman_2.OPorts[0], self.Coupled_Name2.IPorts[0])
        self.connectPorts(self.Coupled_Name.OPorts[0], self.TrafficLight_2.IPorts[0])
        self.connectPorts(self.Policeman_2.OPorts[0], self.Coupled_Name.IPorts[0])



class Coupled_Name2(CoupledDEVS):
    def __init__ (self, name):
        CoupledDEVS.__init__(self, name)
        self.addOutPort("OutPort_20")
        self.addInPort("InPort_19")



################### Model Hierarchy #####################
# Model_trafficLight
#        -> QuickScope_4
#        -> Coupled_Name2
#        -> Coupled_Name
#        .       -> Coupled_Name3
#        .       .       -> Policeman_0
#        .       -> TrafficLight_1
#        .       -> TrafficLight_10
#        -> TrafficLight_2
#        -> Policeman_2
#########################################################
