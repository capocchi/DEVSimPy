import sys
import os
import builtins
import DEVS.AtomicDEVS
import DEVS.CoupledDEVS

p = os.path.join('..','DEVSKernel','PyDEVS')
if p not in sys.path:
    sys.path.append(p)

p = os.path.join('..')
if p not in sys.path:
    sys.path.append(p)
    
builtins.__dict__['DEFAULT_DEVS_DIRNAME'] = 'PyDEVS'
builtins.__dict__['DEVS_DIR_PATH_DICT'] = {'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}


class Diagram0(CoupledDEVS):
    def __init__ (self, name):
        CoupledDEVS.__init__(self, name)



################### Model Hierarchy #####################
# Model_Diagram0
#########################################################