# -*- coding: utf-8 -*-

import os
import wx
import Container
import DetachedFrame

_ = wx.GetTranslation

class ExperimentGenerator:
    """
    """
    def __init__(self, fileDir):
        """ Constructor
        """

        ### local copy
        self.fileDir=fileDir

        self.dec=''
        self.hierarchyDescDec='        '

    def augmentDec(self):
        """
        """
        self.dec+='    '
        return self.dec

    def generateCode(self, model):
        """
        """

        name=model.blockModel.label
        self.dec=''
        self.modelPythonDescription[model]=['', 'class %s(CoupledDEVS):' % name,self.augmentDec()+'def __init__ (self, name):',self.augmentDec()+'CoupledDEVS.__init__(self, name)']

        for op in model.OPorts:
            self.modelPythonDescription[model].append(self.dec+'self.addOutPort("%s")' % op.myID)

        for ip in model.IPorts:
            self.modelPythonDescription[model].append(self.dec+'self.addInPort("%s")' % ip.myID)

        for c in model.getComponentSet():
            cname = c.__class__.__name__
            clabel = c.blockModel.label
            self.modelPythonDescription[model].append("")

            self.modelHierarchyDescription.append('#%s-> %s' % (self.hierarchyDescDec, clabel))
            if not ( hasattr(c, "componentSet") or hasattr(c, "component_set")):
                self.modelPythonDescription[model].append(self.dec+'self.%s=self.addSubModel(%s.%s("%s"))' % (clabel, cname, cname, clabel) )
                self.modulePathFile.append(c.blockModel.python_path)
                if self.listModules.count(cname)==0:
                    self.listModules.append(cname)
                for op in c.OPorts:
                    self.modelPythonDescription[model].append(self.dec+'self.%s.addOutPort("%s")' % (clabel, op.myID))
                for ip in c.IPorts:
                    self.modelPythonDescription[model].append(self.dec+'self.%s.addInPort("%s")' % (clabel, ip.myID))
            else:
                self.modelPythonDescription[model].append(self.dec+'self.%s=self.addSubModel(%s("%s"))' % (clabel, cname, clabel))
                self.hierarchyDescDec+='.       '
                self.generateCode(c) #recursivite
                self.hierarchyDescDec = self.hierarchyDescDec[:-8]


        self.modelPythonDescription[model].append("")

        if hasattr(model, 'IC'):
            for ic in model.IC:
                self.modelPythonDescription[model].append(self.dec+'self.connectPorts(self.%s.OPorts[%s], self.%s.IPorts[%s])' % (ic[0][0].blockModel.label, ic[0][0].OPorts.index(ic[0][1]), ic[1][0].blockModel.label, ic[1][0].IPorts.index(ic[1][1])))
        if hasattr(model, 'EIC'):
            for eic in model.EIC:
                self.modelPythonDescription[model].append(self.dec+'self.connectPorts(self.IPorts[%s], self.%s.IPorts[%s])' % (eic[0][0].IPorts.index(eic[0][1]), eic[1][0].blockModel.label, eic[1][0].IPorts.index(eic[1][1])))
        if hasattr(model, 'EOC'):
            for eoc in model.EOC:
                self.modelPythonDescription[model].append(self.dec+'self.connectPorts(self.%s.OPorts[%s], self.OPorts[%s])' % (eoc[0][0].blockModel.label, eoc[0][0].OPorts.index(eoc[0][1]), eoc[1][0].OPorts.index(eoc[1][1])))


    def writeModelFile(self, master):
        """
        """

        self.listModules = ["sys", "os", "builtins", "DEVS.AtomicDEVS", "DEVS.CoupledDEVS"]
        self.modulePathFile = []
        self.modelPythonDescription = {}
        self.modelHierarchyDescription = []

        ### Create the out directory
        if not os.path.exists(self.fileDir):
            os.makedirs(self.fileDir)

        ### Open file in write mode
        class_name = master.label
        newFile = open(os.path.join(self.fileDir, class_name+'Model.py'), 'w')

        ### Code generation

        if isinstance(master, Container.Diagram):
            master = Container.Diagram.makeDEVSInstance(master)

        self.generateCode(master)

        ### Write import
        for m in self.listModules:
            newFile.write('import %s\n' % m)
            
        txt =''.join(["\n\nsys.path.append(os.path.join('..','DEVSKernel','PyDEVS'))\n",
                    "sys.path.append(os.path.join('..'))\n",
                    "setattr(builtins,'DEFAULT_DEVS_DIRNAME','PyDEVS')\n",
                    "setattr(builtins,'DEVS_DIR_PATH_DICT',{'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')})\n\n"])
        
        newFile.write(txt)

        #### Write models
        for modelDesc in list(self.modelPythonDescription.keys()):
            for line in self.modelPythonDescription[modelDesc]:
                newFile.write(line + "\n")
            newFile.write("\n\n")

        ### Hierarchy Description
        newFile.write('################### Model Hierarchy #####################\n')
        newFile.write('# Model_%s\n' % master.blockModel.label)
        for line in self.modelHierarchyDescription:
            newFile.write('%s\n' % line)
        newFile.write('#########################################################')

        ### Close file
        newFile.close()

        return True

    def writeExperimentFile(self, master):

        newFile = open(os.path.join(self.fileDir, master.label+'Experiment.py'), 'w')

        txt = """# Import code for model simulation:
from simulator import Simulator

# Import the model to be simulate
from %s import %s"""%(master.label+'Model',master.label)

        newFile.write(txt)

        txt = """
#    ======================================================================

# 1. Instantiate the (Coupled or Atomic) DEVS at the root of the 
#  hierarchical model. This effectively instantiates the whole model 
#  thanks to the recursion in the DEVS model constructors (__init__).
#
model = %s(name="%s")
#    ======================================================================"""%(master.label,master.label)

        newFile.write(txt)

        txt = """# 2. Link the model to a DEVS Simulator: 
#  i.e., create an instance of the 'Simulator' class,
#  using the model as a parameter.
sim = Simulator(model)

#    ======================================================================"""

        newFile.write(txt)

        txt = """# 3. Perform all necessary configurations, the most commonly used are:

# A. Termination time (or termination condition)
#    Using a termination condition will execute a provided function at
#    every simulation step, making it possible to check for certain states
#    being reached.
#    It should return True to stop simulation, or Falso to continue.
def terminate_whenStateIsReached(clock, model):
    return model.trafficLight.state.get() == "manual"
    sim.setTerminationCondition(terminate_whenStateIsReached)

#    A termination time is prefered over a termination condition,
#    as it is much simpler to use.
#    e.g. to simulate until simulation time 400.0 is reached
sim.setTerminationTime(400.0)

# B. Set the use of a tracer to show what happened during the simulation run
#    Both writing to stdout or file is possible:
#    pass None for stdout, or a filename for writing to that file
sim.setVerbose(None)

#    ======================================================================"""

        newFile.write(txt)

        txt = """# 4. Simulate the model
sim.simulate()

#    ======================================================================"""

        newFile.write(txt)
        newFile.close()

        return True

    def OnExperiment(self, event):
        """
        """

        popup_menu = event.GetEventObject()
        canvas = popup_menu.parent

        diagram = canvas.GetDiagram()

        ### Set the name of diagram from notebook nb2
        nb2 = canvas.GetParent()

        title  = nb2.GetTitle() if isinstance(nb2, DetachedFrame.DetachedFrame) else nb2.GetPageText(nb2.GetSelection()).rstrip()
        diagram.label = os.path.splitext(os.path.basename(title))[0]

        msg = _("Experiment File Generated in %s dirctory!"%self.fileDir) if self.writeModelFile(diagram) and self.writeExperimentFile(diagram) else _("Experiment File not Generated!")
        dlg = wx.MessageDialog(None, msg, _("PyPDEVS Experiment"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()