# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        <iter3.py>

 Model:       <optim>
 Authors:      <AMORETTI>

 Date:     <2011-09-19>
-------------------------------------------------------------------------------
"""
	
### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message
from initParametres import initParametres
import os.path

### Model class ----------------------------------------------------------------
class Iteration(DomainBehavior,initParametres):


        def __init__(self,fileName=os.path.join(os.path.dirname( __file__ ),"DocSITEC", "parametreGeneraux.dat"),
					fileName1=os.path.join(os.path.dirname( __file__ ),"DocSITEC", "productions.dat"),
					fileName2=os.path.join(os.path.dirname( __file__ ),"DocSITEC", "paramOptim.csv")):
                """Constructor.
                @param fileName : file path of model parameters
                @fileName : file path of model parameters
                """
                
                DomainBehavior.__init__(self)
                initParametres.__init__(self,open(fileName,'r'))
                
                self.localTime = 0 
                self.demandeSimu = 0
                self.flag = []
                #  Model Parameters
                self.inflows = []
                self.localTime = 0
                self.mode = 0
                self.volumes = []
                self.totalCost = 0.0
                self.totalDougth = 0.0
                #  Optimization interfacenbFeeds
                self.modeChangingTimes = [0,6]

                self.solution = []
                self.mincost = 10000000000000.0
                self.mindougth = 10000000000000.0
                self.coutPompage = []
                self.gainTurbinage = []
                self.secheresse = []

                self.models=None
                self.nbSamples=0
                self.nbModes=0
                self.nbFeeds=0
                self.nbConsumptions=0
                self.powerGeneration=None
                self.hasPowerGeneration=None
                self.nbPowerGeneration=0
                self.powerGenerationIndex=None
                self.maxPower=None
                self.initVolumes=None
                self.maxVolumes=None
                self.minVolumes=None
                self.coutUTurbinage=None
                self.coutUPompage=None

                self.etape = 0

# lecture des parametres généraux

                if os.path.exists(fileName) :
                        #print 'OPTIM parametres generaux  file found'
                        f_lecture=open(fileName,'r')
                        param=initParametres(f_lecture)
                        self.models=param.models
                        self.nbSamples=param.nbSamples
                        self.nbModes=param.nbModes
                        self.nbFeeds=param.nbFeeds
                        self.nbConsumptions=param.nbConsumptions
                        self.powerGeneration=param.powerGeneration
                        self.hasPowerGeneration=param.hasPowerGeneration
                        self.nbPowerGeneration=param.nbPowerGeneration
                        self.powerGenerationIndex=param.powerGenerationIndex
                        self.maxPower=param.maxPower
                        self.initVolumes=param.initVolumes
                        self.maxVolumes=param.maxVolumes
                        self.minVolumes=param.minVolumes
                        self.coutUTurbinage=param.coutUTurbinage
                        self.coutUPompage=param.coutUPompage

                        #for i in range(self.nbFeeds): # initialisation des variables d'entrée
                                #self.coutPompage.append(0.0)
                                #self.gainTurbinage.append(0.0)
                                #self.secheresse.append(0.0)

                        self.coutPompage = [0.0]*self.nbFeeds
                        self.gainTurbinage = self.coutPompage
                        self.secheresse = self.coutPompage
                #else :
                        #print '!!!!!!!!!!! OPTIM parametres generaux file not found'

# lecture des parametres d'optimisation
                if os.path.exists(fileName2) :
                        #print '  parametrage optimisation file found'
                        with open(fileName2,'r') as f :
                                self.minFinalVolumes = []
                                for i in range(self.nbFeeds):
                                        #volumes maximaux en fin d'horizon
                                        l = f.readline()
                                        t = l.split(";")
                                        self.minFinalVolumes.append(float(t[0]))
                                l = f.readline()
                                t = l.split(";")
                                self.kMmP=float(t[0])
                                l = f.readline()
                                t = l.split(";")
                                self.kMmC=float(t[0])
                                #print self.minFinalVolumes,self.kMmP,self.kMmC
                                #f.close()
                #else :
                        #print '!!!!!!!!!!! OPTIM fichier parametre optimisation file not found' 
# lecture des productions des barrages
                if os.path.exists(fileName1) :
                        #print '  OPTIM fichier production file found'
                        with open(fileName1,'r') as f :
                                
                                for s in range(self.nbSamples): #productions
                                        self.inflows.append([])
                                        l = f.readline()
                                        #print l
                                        t = l.split(" ")
                                        for i in range(self.nbFeeds):
                                                self.inflows[s].append(float(t[i+1]))# i=0 = N° semaine
                                                #print t[i]
                                #print 'prod iter',self.inflows
                                #f.close()
                #else:
                        #print '!!!!!!!!!!! OPTIM fichier production file not found' 

                for i in range(self.nbPowerGeneration):
                        self.powerGeneration.append([0.0]*self.nbSamples)
                
                self.admissible = []
                self.i_ferme = 0
                self.j_ouvre = 0
                self.finSimu = 0 # fin simu est déterminé à la fin du calcul
                self.flag = [False]*3

                self.state = {	'status': 'ACTIVE', 'sigma':0}


        def extTransition(self):

                total=True
                indiceBarrage=0

                #lecture des données barrage 0 :cout Pompage, Gaint Turb, secheresse
                
                msg = self.peek(self.IPorts[0])
                if (msg!=None):
                        self.coutPompage[indiceBarrage]=float(msg.value[0])
                        self.gainTurbinage[indiceBarrage]=float(msg.value[1])
                        self.secheresse[indiceBarrage]=float(msg.value[2])
                        self.flag[0]=True
                #del msg

                indiceBarrage=1

                #lecture des données barrage 1 :cout Pompage, Gaint Turb, secheresse
                
                msg = self.peek(self.IPorts[2])
                if (msg!=None):
                        self.coutPompage[indiceBarrage]=float(msg.value[0])
                        self.gainTurbinage[indiceBarrage]=float(msg.value[1])
                        self.secheresse[indiceBarrage]=float(msg.value[2])
                        self.flag[1]=True
                #del msg

                #lecture des données secheresse NetWork
                msg = self.peek(self.IPorts[1])
                if (msg!=None):
                       self.secheresseNW=float(msg.value[0])
                       self.flag[2]=True
                #del msg
                
# vérification de la réception des 3 messages

                for i in range(3):
                        if self.flag[i]!=True:
                                total=False
                if total==True and self.finSimu!=1:
                        for i in range(3):
                                self.flag[i]=False
                        self.demandeSimu=0
                        self.cost=0.0
                        self.dougth=0.0
                        for i in range(self.nbFeeds):
                                self.cost+=self.coutPompage[i]-self.gainTurbinage[i]
                                self.dougth+=self.secheresse[i]
                        self.dougth+=self.secheresseNW # dougth de network
                        #print self.cost,self.dougth
                        self.state['sigma'] = 0


                if total==True and self.finSimu==1:
#
# prévoir ici une sortie OPorts pour indiquer le résultat optimal
#
                        print 'fin simulation'
                        self.state['sigma'] = INFINITY

        def emissionMessage(self,trace,changeTimes, powerGeneration):
                                        
                msg=Message([int(trace), int(changeTimes[0]), int(changeTimes[1]), self.kMmC], self.localTime) # ==> trace, i_ferme, j_ouvre kMmC
                self.ifjo = self.OPorts[1]
                self.poke(self.ifjo,msg)

                # à reprendre pour rendre les emissions dynamiques en fonction du nombre et des indices des turbines
                # ici c'est spécifique !!!!!!!!!!!

                msg1=Message() # ==> trace, kMmP,volume final min ,52 turbinages ospedale à reprendre
                self.turbine0 = self.OPorts[0]
                msg1.value=[int(trace), self.kMmP, self.minFinalVolumes[0]]
                for i in range(self.nbSamples):
                        msg1.value.append(powerGeneration[0][i])
                msg1.time = self.localTime
                self.poke(self.turbine0,msg1)

                msg2=Message([int(trace), self.kMmP, self.minFinalVolumes[1]], self.localTime) # ==> trace, kMmP,volume final min, 0 turbinage figari
                self.turbine1 = self.OPorts[2]
                self.poke(self.turbine1,msg2)

        def outputFnc(self):
                while(self.demandeSimu==0 and self.etape!=100):
                        #print 'etape',self.etape
                        if self.etape==0:
                                self.j_ouvre+=1
                                if self.j_ouvre==self.nbSamples:
                                        self.i_ferme+=1
                                        self.j_ouvre=self.i_ferme+1
                                        if self.i_ferme==self.nbSamples-1:
                                                self.etape=2
                                else:
                                        trace=0
                                        self.demandeSimu=1
                                        self.etape=1

                                        self.emissionMessage(0, [self.i_ferme,self.j_ouvre],self.powerGeneration)
                                        
                                        
                                     #attendre fin simu 52 semaines à turbinage nul

                        elif self.etape==1:
                                #print [i,j]
                                #print 'cost = '+cost+' dougth = '+dougth
                                if self.dougth < self.mindougth :
                                        self.solution = [self.i_ferme,self.j_ouvre]
                                        self.mindougth = self.dougth
                                        self.mincost = self.cost
                                else :
                                        if int(self.dougth) == int(self.mindougth) :
                                                if self.cost < self.mincost :
                                                        self.solution = [self.i_ferme,self.j_ouvre]
                                                        self.mincost = self.cost
                                if(int(self.dougth) == 0):#!!!!!!!!
                                        self.admissible.append([self.i_ferme,self.j_ouvre])
                                        #print self.i_ferme,self.j_ouvre
                                self.etape=0
                        elif self.etape==2:
                                #print 'mincost = '+str(self.mincost)+' mindougth = '+str(self.mindougth)+' for : '+str(self.solution)
                                self.optGene = self.powerGeneration
                                #print 'Admissible solution without power generation'
                                #print self.admissible
                                print 'nombre de solutions admissibles sans turbinage',len(self.admissible)
                                self.s=0
                                if len(self.admissible)==0:
                                        print 'pas de solution'
                                        self.etape=100
                                else:
                                        self.nbIterations=len(self.admissible)
                                        self.etape=30
                        elif self.etape==30:
                                self.powerGeneration = []
                                for i in range(self.nbPowerGeneration):
                                        self.powerGeneration.append([])
                                        for j in range(self.nbSamples):
                                                self.powerGeneration[i].append(0.0)
                                self.iturb=0
                                self.etape=31
                        elif self.etape==31:
                                for j in range(self.nbFeeds):
                                        if self.hasPowerGeneration[j]:
                                                if self.powerGenerationIndex[j]==self.iturb:
                                                        self.feedIndex=j
                                self.js=self.nbSamples-1
                                self.etape=32
                        elif self.etape==32:
                                self.maxPower1 = self.kMmP * self.inflows[self.js][self.feedIndex]
                                if self.maxPower1 > self.maxPower[self.feedIndex] :
                                        self.maxPower1 = self.maxPower[self.feedIndex]
                                self.notBack = True
                                self.td=0
                                self.etape=33
                        elif self.etape==33:
                                self.td+=1
                                self.maxPower1 = self.maxPower1 / 2.0
                                #print self.s,self.js
                                #print str(j)+' maxPower = '+str(maxPower)
                                self.powerGeneration[self.iturb][self.js]+= self.maxPower1

                                self.etape=34
                                self.demandeSimu=1
                                trace=0

                                self.emissionMessage(0, \
                                                     [self.admissible[self.s][0],self.admissible[self.s][1]]\
                                                     ,self.powerGeneration)


                               #attendre fin simu 52 semaines

                        elif self.etape==34:
                                if int(self.dougth) != 0.0 :
                                        self.notBack = False
                                        ret = self.dougth
                                        if ret > self.maxPower1 : ret = self.maxPower1
                                        self.powerGeneration[self.iturb][self.js] = self.powerGeneration[self.iturb][self.js] - ret
                                if self.notBack==True and self.td < 10: self.etape=33
                                else: self.etape=35
                        elif self.etape==35:
                                self.js=self.js-1
                                if self.js<0:self.etape=36
                                else:self.etape=32
                        elif self.etape==36:
                                self.iturb+=1
                                if self.iturb==self.nbPowerGeneration:
                                        self.etape=37
                                        self.demandeSimu=1
                                        self.emissionMessage(0,\
                                                             [self.admissible[self.s][0],self.admissible[self.s][1]],\
                                                             self.powerGeneration)

                                else: self.etape=31
                        elif self.etape==37:
                                if self.cost<self.mincost:
                                        self.solution = self.admissible[self.s]
                                        self.optGene = []
                                        for i in range(self.nbPowerGeneration):
                                                self.optGene.append([])
                                                for j in range(self.nbSamples):
                                                        self.optGene[i].append(self.powerGeneration[i][j])
                                        self.optGene = self.powerGeneration
                                        self.mincost = self.cost
                                print self.s,'/',self.nbIterations, self.admissible[self.s]
                                self.s+=1
                                if self.s==len(self.admissible): self.etape=50
                                #if self.s==1: self.etape=50 # pour tester les sorties 
                                else:self.etape=30
                        elif self.etape==50:
                                #print 'mincost = '+str(self.mincost)+' for : '+str(self.solution)+' with '+str(self.optGene)
                                print 'date de fermeture/ouverture des vannes ',self.solution[0],'/',self.solution[1]
                                self.etape=100
                                self.demandeSimu=1
                                self.finSimu=1
                                
                                self.emissionMessage(1,\
                                                     [self.solution[0],self.solution[1]],\
                                                      self.optGene)
                               #attendre fin simu 52 semaines de la solution optimale



                        elif self.etape==100:
                               print 'fin calcul'
			
        def intTransition(self):
               self.state['sigma'] = INFINITY
        def timeAdvance(self):
               return self.state['sigma']
        
