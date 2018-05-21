# -*- coding: utf-8 -*-

import os
import shutil
import Container
import DetachedFrame

class ExperimentGenerator:

    def __init__(self, fileDir):
        self.fileDir=fileDir
        self.dec=''
        self.hierarchyDescDec='        '

    def augmentDec(self):
        self.dec+='    '
        return self.dec

    def generateCode(self, model):
        """
        """

        name=model.blockModel.label
        self.dec=''
        self.modelPythonDescription[model]=[]
        self.modelPythonDescription[model].append('')
        self.modelPythonDescription[model].append('class %s(CoupledDEVS):' % name)
        self.modelPythonDescription[model].append(self.augmentDec()+'def __init__ (self, name):')
        self.modelPythonDescription[model].append(self.augmentDec()+'CoupledDEVS.__init__(self, name)')

        for op in model.OPorts:
            self.modelPythonDescription[model].append(self.dec+'self.addOutPort("%s")' % op.myID)

        for ip in model.IPorts:
            self.modelPythonDescription[model].append(self.dec+'self.addInPort("%s")' % ip.myID)

        for c in model.componentSet:
            cname = c.__class__.__name__
            clabel = c.blockModel.label
            self.modelPythonDescription[model].append("")

            self.modelHierarchyDescription.append('#%s-> %s' % (self.hierarchyDescDec, clabel))
            if not hasattr(c, "componentSet"):
                self.modelPythonDescription[model].append(self.dec+'self.%s=self.addSubModel(%s.%s("%s"))' % (clabel, cname, cname, clabel) )
                #self.modulePathFile.append(c.blockModel.python_path)
                #if self.listModules.count(cname)==0:
                    #self.listModules.append(cname)
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

        for ic in model.IC:
            self.modelPythonDescription[model].append(self.dec+'self.connectPorts(self.%s.OPorts[%s], self.%s.IPorts[%s])' % (ic[0][0].blockModel.label, ic[0][0].OPorts.index(ic[0][1]), ic[1][0].blockModel.label, ic[1][0].IPorts.index(ic[1][1])))
        for eic in model.EIC:
            self.modelPythonDescription[model].append(self.dec+'self.connectPorts(self.IPorts[%s], self.%s.IPorts[%s])' % (eic[0][0].IPorts.index(eic[0][1]), eic[1][0].blockModel.label, eic[1][0].IPorts.index(eic[1][1])))
        for eoc in model.EOC:
            self.modelPythonDescription[model].append(self.dec+'self.connectPorts(self.%s.OPorts[%s], self.OPorts[%s])' % (eoc[0][0].blockModel.label, eoc[0][0].OPorts.index(eoc[0][1]), eoc[1][0].OPorts.index(eoc[1][1])))


    def createExperimentFile(self, master):
        """
        """

        self.listModules = []
        self.modulePathFile = []
        self.modelPythonDescription={}
        self.modelHierarchyDescription=[]

        ### List of import 
        self.listModules.append("sys")
        self.listModules.append("os")
        self.listModules.append("__builtin__")
        self.listModules.append("DEVS.AtomicDEVS")
        self.listModules.append("DEVS.CoupledDEVS")

        ### Create or delete the out directory
        if os.path.exists(self.fileDir):
            shutil.rmtree(self.fileDir)
        os.makedirs(self.fileDir)

        ### Open file in write mode
        newFile = open(os.path.join(self.fileDir,'model.py'), 'w')

        ### Code generation

        if isinstance(master, Container.Diagram):
            master = Container.Diagram.makeDEVSInstance(master)

        self.generateCode(master)

        ### write import
        for m in self.listModules:
            newFile.write('import %s\n' % m)
    
        txt =''.join(["\n\nsys.path.append(os.path.join('..','DEVSKernel','PyDEVS'))\n",
                    "sys.path.append(os.path.join('..'))\n",
                    "__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = 'PyDEVS'\n",
                    "__builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}\n\n"])
        
        newFile.write(txt)

        #### write models
        for modelDesc in self.modelPythonDescription.keys():
            for line in self.modelPythonDescription[modelDesc]:
                newFile.write(line + "\n")
            newFile.write("\n\n")

        #Description de la hierarchie du modele
        newFile.write('################### Model Hierarchy #####################\n')
        newFile.write('# Model_%s\n' % master.blockModel.label)
        for line in self.modelHierarchyDescription:
            newFile.write('%s\n' % line)
        newFile.write('#########################################################')

        #Fermeture du fichier
        newFile.close()

    def OnExperiment(self, event):
        """
        """

        popup_menu = event.GetEventObject()
        canvas = popup_menu.parent

        diagram = canvas.GetDiagram()

        ### set the name of diagram from notebook nb2
        nb2 = canvas.GetParent()

        title  = nb2.GetTitle() if isinstance(nb2, DetachedFrame.DetachedFrame) else nb2.GetPageText(nb2.GetSelection()).rstrip()
        diagram.label = os.path.splitext(os.path.basename(title))[0]

        self.createExperimentFile(diagram)