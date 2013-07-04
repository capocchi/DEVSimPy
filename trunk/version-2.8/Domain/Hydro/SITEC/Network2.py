# -*- coding: utf-8 -*-

"""
Name : Network.py
Brief description : Network of water distribution
Authors : Rene Amoretti and Jean Loup Farges
Version : 1.0
Last modified : 19/09/11
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS
"""

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message
import initParametres
import os.path

class Network(DomainBehavior):
        """     Network of water distribution.

        """
        
        ###
        def __init__(self, fileName=os.path.join(os.getcwd(), "parametresGeneraux.dat"),\
                     fileName1=os.path.join(os.getcwd(), "consommations.dat"),\
                     fileName3=os.path.join(os.getcwd(), "sortiesNetwork.dat")):
                """Constructor.
                @param fileName : file path of model parameters
                @fileName : file path of model parameters
                """
                #  Model Parameters
                DomainBehavior.__init__(self)
                
                self.models = []
#                self.modeChangingTimes = []

                self.flag = []
                self.consos = []
                self.localTime = 0
                self.ecart = 0.0
                self.consumptions = []
                self.fin52Sem = False
                self.nbSamples = None
                self.nbModes = None
                self.nbFeeds = None
                self.nbConsumptions = 0
                self.powerGeneration = None
                self.hasPowerGeneration = None
                self.nbPowerGeneration = None
                self.powerGenerationIndex = None
                self.maxPower = None
                self.initVolumes = None
                self.maxVolumes = None
                self.minVolumes = None
                self.coutUTurbinage = None
                self.coutUPompage = None
               
                if os.path.exists(fileName) :
                        f_lecture = open(fileName,'r')
                        param = initParametres(f_lecture)
                        self.models = param.models
                        self.nbSamples = param.nbSamples
                        self.nbModes = param.nbModes
                        self.nbFeeds = param.nbFeeds
                        self.nbConsumptions = param.nbConsumptions
                        self.powerGeneration = param.powerGeneration
                        self.hasPowerGeneration = param.hasPowerGeneration
                        self.nbPowerGeneration = param.nbPowerGeneration
                        self.powerGenerationIndex = param.powerGenerationIndex
                        self.maxPower = param.maxPower
                        self.initVolumes = param.initVolumes
                        self.maxVolumes = param.maxVolumes
                        self.minVolumes = param.minVolumes
                        self.coutUTurbinage = param.coutUTurbinage
                        self.coutUPompage = param.coutUPompage

                #else:
                        #print '!!!!!!!!!!!!! Network Parametres generaux file not found'
                
                self.nbSem = self.nbSamples

                self.consumptions = [0.0]*self.nbConsumptions
                
                if os.path.exists(fileName1):
                        #print 'NetWork fichiers consos file found'
                        self.f_conso = open(fileName1,'r')
                        for np in range(self.nbSem):
                                l = self.f_conso.readline()
                                t = l.split(" ")
                                self.consos.append([])
                                for i in range(self.nbConsumptions):
                                        self.consos[np].append(float(t[i+1]))# i=0--> N° semaine
                        

                        #self.f_conso.close()
                #else:
                        #print '!!!!!!!!!!!!! NetWork fichiers consos file not found'
                   
                
                #State variable
                self.state = {  'status': 'ACTIVE', 'sigma':INFINITY}
        
        ###
        def intTransition(self):
                self.localTime += 1
                self.state['sigma'] = 1 if self.fin52Sem == False else INFINITY
                        
        ###
        def outputFnc(self):
                #print 'outputFnc'
                msg1 = Message()
                msg2 = Message()
                msg3 = Message()
                self.QR = self.OPorts[0]
                self.QF = self.OPorts[2]
                self.DNW = self.OPorts[1]

                j=int(self.localTime)
                if self.localTime<self.nbSem:
                        for i in range (self.nbConsumptions):
                                self.consumptions[i] = self.kMmC *  self.consos[j][i]
                        if (self.localTime >= self.tf) and (self.localTime <= self.to):
                                # mode été
                                flowQR = self.models[1][0][0]
                                for i in range(self.nbConsumptions):
                                        flowQR = flowQR + self.models[1][1][i][0] * self.consumptions[i]
                                if flowQR < self.models[1][2][0] :
                                        self.ecart += (self.models[1][2][0] - flowQR)
                                if flowQR > self.models[1][3][0] :
                                        self.ecart += (flowQR - self.models[1][3][0])
                                flowQF = self.models[1][0][1]
                       
                                for i in range(self.nbConsumptions):
                                        flowQF = flowQF + self.models[1][1][i][1]  * self.consumptions[i]
                                #print self.models[1][1][i][1],self.consumptions[i]
                                if flowQF < self.models[1][2][1] :
                                        self.ecart += (self.models[1][2][1] - flowQF)
                                if flowQF > self.models[1][3][1] :
                                        self.ecart += (flowQF - self.models[1][3][1])
                                flowQFPos = flowQF
                    
                
                        else:
                        # mode hiver 

                                flowQR = self.models[0][0][0]
                                for i in range(self.nbConsumptions):
                                        flowQR = flowQR + self.models[0][1][i][0]  * self.consumptions[i]
                                #print self.consumptions[i]
                                if flowQR < self.models[0][2][0] :
                                        self.ecart += (self.models[0][2][0] - flowQR)
                                if flowQR > self.models[0][3][0] :
                                        self.ecart += (flowQR - self.models[0][3][0])
                                flowQF = self.models[0][0][1]
                                for i in range(self.nbConsumptions):
                                        flowQF = flowQF + self.models[0][1][i][1]  * self.consumptions[i]
                                if flowQF < self.models[0][2][1] :
                                        self.ecart += (self.models[0][2][1] - flowQF)
                                if flowQF > self.models[0][3][1] :
                                        self.ecart += (flowQF - self.models[0][3][1])
                                flowQFPos = 0.0
                
                        msg1.value = [flowQR,0.0,0.0]
                        msg1.time = self.localTime
                        self.poke(self.QR,msg1)
                
                        msg3.value = [flowQF,0.0,0.0]
                        msg3.time = self.localTime
                        self.poke(self.QF,msg3)
                                
#                        print 'network',self.localTime
                else:
#                        self.localTime = -1 # car intTrans est executée après
                        msg3.value = [self.ecart]
                        msg3.time = self.localTime
                        self.poke(self.DNW,msg3)
                        self.fin52Sem=True
#                        print 'NetWork fin 52 sem'

                
        ###
                        
        def extTransition(self):
                #print "extTransition"
                #Input Port
                msg = self.peek(self.IPorts[0])

#                print 'recu demarre'
                self.localTime = 0
                self.state['sigma'] = 0
                self.trace=int(msg.value[0])
                self.tf=int(msg.value[1])#semaine fermeture vanne
                self.to=int(msg.value[2])#semaine ouverture vannes
                self.kMmC=float(msg.value[3]) # coeff major/Minor conso
                #print self.trace,self.tf,self.to
                #del msg
                self.fin52Sem=False
                self.ecart=0.0
                
        ###
        def timeAdvance(self):return self.state['sigma']
                
        def __str__(self):
                return "Network"
