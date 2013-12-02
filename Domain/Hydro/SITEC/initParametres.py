# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        <initParametres.py>

 Model:       <describe model>
 Authors:      <your name>

 Date:     <yyyy-mm-dd>
-------------------------------------------------------------------------------
"""
	
### Specific import ------------------------------------------------------------
#from DomainInterface.DomainBehavior import DomainBehavior
#"from Object import Message
#"import os.path
		
### Model class ----------------------------------------------------------------
class initParametres:
        def __init__(self,f):
                """Constructor.
                @param fileName : file path of model parameters
                @fileName : file path of model parameters                """
                #DomainBehavior.__init__(self)                
                #  Model Parameters
                # DomainBehavior.__init__(self)
                self.models = []
                

# lecture des parametres généraux

                l = f.readline()
                t=l.split(" ")
                self.nbSamples = int(t[0]) #nb semaines
                l = f.readline()
                t=l.split(" ")
                #print l
                self.nbModes = int(t[0]) #modes ete, hiver
                l = f.readline()
                t=l.split(" ")
                self.nbFeeds=int(t[0]) #nb barrages
                #print self.nbFeeds
                l = f.readline()
                t=l.split(" ")
                self.nbConsumptions=int(t[0]) #nb points consommation
                #print self.nbConsumptions
                for m in range(self.nbModes):
                        self.models.append([[],[],[],[]])
                        l = f.readline()
                        #print l
                        t = l.split(" ")
                        for i in range(self.nbFeeds):
                                self.models[m][0].append(float(t[i])) #coeff constants
                                #print self.models[m][0]
                        for c in range(self.nbConsumptions): #coeff variables
                                l = f.readline()
                                #print l
                                t = l.split(" ")
                                #print t
                                s = []
                                for i in range(self.nbFeeds):
                                        s.append(float(t[i]))
                                self.models[m][1].append(s)
                        l = f.readline()
                        #print l
                        t = l.split(" ")
                        for i in range(self.nbFeeds):
                                self.models[m][2].append(float(t[i])) #débits vidange mini
                        l = f.readline()
                        #print l
                        t = l.split(" ")
                        for i in range(self.nbFeeds):
                                self.models[m][3].append(float(t[i])) #débit vidange maxi
                l = f.readline()
                #print self.models
                t = l.split(" ")
                self.hasPump = []
                for i in range(self.nbFeeds): # définition des pompages
                        if int(t[i]) == 1 :
                                self.hasPump.append(bool(t[i]))
                        else :
                                self.hasPump.append(bool())
                #print self.hasPump
                #les pompages maxi sont liés aux débits vidanges maxi
                l = f.readline()
                #print l
                t = l.split(" ")
                self.hasPowerGeneration = []
                self.nbPowerGeneration = 0
                self.powerGeneration = []
                for i in range(self.nbFeeds): #définition des turbines
                        if int(t[i]) == 1 :
                                self.hasPowerGeneration.append(bool(t[i]))
                                self.powerGeneration.append([])
                                for j in range(self.nbSamples):
                                        self.powerGeneration[self.nbPowerGeneration].append(0.0)
                                self.nbPowerGeneration = self.nbPowerGeneration + 1
                        else :
                                self.hasPowerGeneration.append(bool())
                #print 'npg',self.nbPowerGeneration
                l = f.readline()
                #print l
                t = l.split(" ")
                self.powerGenerationIndex = []
                for i in range(self.nbFeeds):
                        self.powerGenerationIndex.append(int(t[i]))
                #print self.hasPump
                l = f.readline()
                #print l
                t = l.split(" ")
                self.maxPower = []
                for i in range(self.nbFeeds):# turbinage maxi
                        self.maxPower.append(float(t[i]))
                #print 'maxP',self.maxPower
                l = f.readline()
                #print l
                t = l.split(" ")
                self.initVolumes = []
                for i in range(self.nbFeeds):# volume initiaux
                        self.initVolumes.append(float(t[i]))
                #print 'vol ini ',self.initVolumes
                l = f.readline()
                t = l.split(" ")
                self.maxVolumes = []
                for i in range(self.nbFeeds): #volumes maximaux
                        self.maxVolumes.append(float(t[i]))
                #print 'max vol ',self.maxVolumes
                l = f.readline()
                t = l.split(" ")
                self.minVolumes = []
                for i in range(self.nbFeeds): #volume minimum
                        self.minVolumes.append(float(t[i]))
                #print 'vol mini',self.minVolumes
                l = f.readline()
                t = l.split(" ")
                self.coutUTurbinage = []
                for i in range(self.nbFeeds): #coutUnitaire_turbinage
                        self.coutUTurbinage.append(float(t[i]))
                #print 'cout turbinage ',self.coutTurbinage
                l = f.readline()
                t = l.split(" ")
                self.coutUPompage = []
                for i in range(self.nbFeeds): #coutUnitaire_pompage
                        self.coutUPompage.append(float(t[i]))
                #print 'cout pompage',self.coutPompage
                f.close()
