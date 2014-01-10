# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        <Barrage2E.py>

 Model:       <Barrage>
 Authors:      <AMORETTI>

 Date:     <2011-08-31>
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message
from initParametres import initParametres
import os.path

### Model class ----------------------------------------------------------------
class Barrage_Ospedale(DomainBehavior):


    def __init__(self,fileName=os.path.join(os.getcwd(), "parametreGeneraux.dat"),\
                 fileName1=os.path.join(os.getcwd(), "productions.dat"),\
                 fileName2=os.path.join(os.getcwd(), "sortieBarrages.dat"),indice=0):
      
        DomainBehavior.__init__(self)

	self.flag = []
	self.gainTurbinage= 0.0
	self.turbinage = [] #liste des turbinages sur 52 semaines
	self.debordement = 0.0
	self.secheresse = 0.0
	self.coutPompage = 0.0
	self.production =[]


        self.flag = []
        self.gainTurbinage= 0.0
        self.turbinage = [] #liste des turbinages sur 52 semaines
        self.debordement = 0.0
        self.secheresse = 0.0
        self.coutPompage = 0.0
        self.production =[]

        self.inflows = []
        self.localTime = 0
        self.mode = 0
	self.nbSamples=None
	self.volumeBarrage=None
	self.initVolumes=None
	self.volumeMini=None
	self.volumeMaxi=None
	self.nbSem=None
	self.hasPowerGenerationB=None
	self.hasPumpB=None
	self.prixUnitEDF=None
	self.coutUnitPompage=None
	self.indB=None
	self.f_sortie = None

	# lecture des parametres généraux

	if os.path.exists(fileName) :
		f_lecture=open(fileName,'r')
		param=initParametres(f_lecture)
		self.nbSamples=param.nbSamples

        self.nbSamples=None
        self.volumeBarrage=None
        self.initVolumes=None
        self.volumeMini=None
        self.volumeMaxi=None
        self.nbSem=None
        self.hasPowerGenerationB=None
        self.hasPumpB=None
        self.prixUnitEDF=None
        self.coutUnitPompage=None
        self.indB=None
        self.f_sortie = None

        # lecture des parametres generaux

        if os.path.exists(fileName) :
            f_lecture=open(fileName,'r')
            param=initParametres(f_lecture)
            self.nbSamples=param.nbSamples

            self.volumeBarrage=param.initVolumes[indice]
            self.initVolumes=param.initVolumes
            self.volumeMini=param.minVolumes[indice]
            self.volumeMaxi=param.maxVolumes[indice]
            self.nbSem=self.nbSamples
            self.hasPowerGenerationB=param.hasPowerGeneration[indice]
            self.hasPumpB=param.hasPump[indice]
            self.prixUnitEDF=param.coutUTurbinage[indice]
            self.coutUnitPompage=param.coutUPompage[indice]
            self.indB=indice # indice du barrage 0 1

            #init liste turbinage
            self.turbinage = [0.0]*self.nbSem

        #else:
            #print '!!!!!!!!!! barrage',indice,'Parametres generaux  file not found'

                if os.path.exists(fileName2):
                        #print 'Tableau Sortie barrage',indice,' file found'
                        self.f_sortie=open(fileName2,'w')

                        l1='N.sem'+';'\
                           +'Volume'+';'\
                           +'Sechss'+';'\
                           +'Debord'+';'\
                           +'Prod'+';'\
                           +'Conso'+';'\
                           +'Q.Turb'+';'\
                           +'GainT'+';'\
                           +'Pompge'+';'\
                           +'CoutPomp'+';'\
                           +'\n'+'\n'
                        self.f_sortie.write(l1)
                #else:
                       #print '!!!!!!!!!!!!! Tableau Sortie barrage',indice,'  file not found'

        #print 'barrage  ',indice
        #print 'volumes',self.volumeBarrage,self.volumeMini,self.volumeMaxi,self.volumeFinH
        #print 'pump ',self.hasPumpB, self.hasPowerGenerationB
        #print 'prix edf ',self.prixUnitEDF
        #print 'cout pompage', self.coutUnitPompage

                self.flag = [False]*2

                if os.path.exists(fileName1):
                        #print 'Production barrage',indice, ' file found'
                        with open(fileName1,'r') as f:
                                for i in range(self.nbSem):
                                        l = f.readline()
                                        t=l.split(" ")
                                        #print t[indice]
                                        self.production.append(float(t[indice+1])) # indice 0 = N°semaine
                        #f.close()
                        #print 'barrage',indice,self.production
                #else:
                        #print '!!!!!!!!! Production barrage',indice, ' file not found'

        if os.path.exists(fileName2):
            #print 'Tableau Sortie barrage',indice,' file found'
            self.f_sortie=open(fileName2,'w')

                self.state = {  'status': 'ACTIVE', 'sigma':INFINITY, 'indice': indice }

        def extTransition(self):


            l1='N.sem'+';'\
               +'Volume'+';'\
               +'Sechss'+';'\
               +'Debord'+';'\
               +'Prod'+';'\
               +'Conso'+';'\
               +'Q.Turb'+';'\
               +'GainT'+';'\
               +'Pompge'+';'\
               +'CoutPomp'+';'\
               +'\n'+'\n'
            self.f_sortie.write(l1)
        #else:
           #print '!!!!!!!!!!!!! Tableau Sortie barrage',indice,'  file not found'


        self.flag = [False]*2

        if os.path.exists(fileName1):
            #print 'Production barrage',indice, ' file found'
            with open(fileName1,'r') as f:
                for i in range(self.nbSem):
                    l = f.readline()
                    t=l.split(" ")
                    #print t[indice]
                    self.production.append(float(t[indice+1])) # indice 0 = Num semaine
            #f.close()
            #print 'barrage',indice,self.production
        #else:
            #print '!!!!!!!!! Production barrage',indice, ' file not found'
                #Recuperation de la trace
                # trace=1 ==> on ecrit le fichier une fois en fin de simu pour chaque semaine
                # trace =0 on ecrit dans un message le cout et la secheresse à la semaine 51
                        self.trace = int(msg.value[0])
                        self.kMmP=float(msg.value[1])
                        self.volumeFinH=float(msg.value[2])
                        self.flag[1]=True
                        if self.hasPowerGenerationB:
                                for i in range(self.nbSem):
                                        self.turbinage[i]=float(msg.value[i+3])
                                        #print 'b',self.turbinage[i]
                #del msg
                for i in range(2):
                        if self.flag[i]!=True:
                                total=False

                if total==True:
                        self.state['sigma'] = 0


        def outputFnc(self):

                j=int(self.localTime)
                turbinageE=0.0

        self.state = {  'status': 'ACTIVE', 'sigma':INFINITY, 'indice': indice }

                if self.hasPowerGenerationB: #cas du turbinage
                        self.gainTurbinage += self.turbinage[j]*self.prixUnitEDF
                        #print self.gainTurbinage
                        debitQS= self.turbinage[j]-self.debitRemplissage
                        turbinageE=self.turbinage[j]
                else:
                        debitQS=-self.debitRemplissage
                Qpompe=0.0

    def extTransition(self):

                if self.hasPumpB: #cas du pompage
                        if self.debitVidange>0:
                                self.coutPompage += self.debitVidange*self.coutUnitPompage
                                Qpompe=self.debitVidange

        total = True
        msg = self.peek(self.IPorts[1])
        if (msg != None):


                self.volumeBarrage+= - debitQS - self.debitVidange #evolution du barrage
                #print self.name,j,' Qrempl',debitQS, 'turb',turbinageE, 'vidang_rempli',self.debitVidange, 'vol', self.volumeBarrage

        #Recuperation debitVidange si >0 (<0=remplissage)
            self.debitVidange = float(msg.value[0])
            self.flag[0]=True
            #print self.name,self.debitVidange
        #del msg


                # Si volumeBarrage > Vmax:
                if self.volumeBarrage > self.volumeMaxi:
                        self.debordement+= self.volumeBarrage - self.volumeMaxi
                        #print 'debord',self.debordement

                # Si volumeBarrage < Vmin:
                if j==self.nbSem-1 :
                        if self.volumeBarrage < self.volumeFinH:
                                self.secheresse += self.volumeFinH- self.volumeBarrage
                else:
                        if self.volumeBarrage < self.volumeMini:
                                self.secheresse += self.volumeMini- self.volumeBarrage
                        #print 'secheresse ',self.secheresse

        msg = self.peek(self.IPorts[0])
        if (msg != None):

                # Si volumeBarrage > Vmax alors saturation:
                if self.volumeBarrage > self.volumeMaxi:
                        self.volumeBarrage = self.volumeMaxi

        #Recuperation de la trace
        # trace=1 ==> on ecrit le fichier une fois en fin de simu pour chaque semaine
        # trace =0 on ecrit dans un message le cout et la secheresse a la semaine 51
            self.trace = int(msg.value[0])
            self.kMmP=float(msg.value[1])
            self.volumeFinH=float(msg.value[2])
            self.flag[1]=True
            if self.hasPowerGenerationB:
                for i in range(self.nbSem):
                    self.turbinage[i]=float(msg.value[i+3])
                    #print 'b',self.turbinage[i]
        #del msg
        for i in range(2):
            if self.flag[i]!=True:
                total=False

        if total==True:
            self.state['sigma'] = 0

	msg1=Message() #
	msg2=Message() #
	msg3=Message() #


    def outputFnc(self):

        j=int(self.localTime)
        turbinageE=0.0

        self.debitRemplissage = self.kMmP * self.production[j]
        #print self.name,self.debitRemplissage,self.debitVidange

        if self.hasPowerGenerationB: #cas du turbinage
            self.gainTurbinage += self.turbinage[j]*self.prixUnitEDF
            #print self.gainTurbinage
            debitQS= self.turbinage[j]-self.debitRemplissage
            turbinageE=self.turbinage[j]
        else:
            debitQS=-self.debitRemplissage
        Qpompe=0.0


        if self.hasPumpB: #cas du pompage
            if self.debitVidange>0:
                self.coutPompage += self.debitVidange*self.coutUnitPompage
                Qpompe=self.debitVidange


        self.volumeBarrage+= - debitQS - self.debitVidange #evolution du barrage
        #print self.name,j,' Qrempl',debitQS, 'turb',turbinageE, 'vidang_rempli',self.debitVidange, 'vol', self.volumeBarrage



        # Si volumeBarrage > Vmax:
        if self.volumeBarrage > self.volumeMaxi:
            self.debordement+= self.volumeBarrage - self.volumeMaxi
            #print 'debord',self.debordement

        # Si volumeBarrage < Vmin:
        if j==self.nbSem-1 :
            if self.volumeBarrage < self.volumeFinH:
                self.secheresse += self.volumeFinH- self.volumeBarrage
        else:
            if self.volumeBarrage < self.volumeMini:
                self.secheresse += self.volumeMini- self.volumeBarrage
            #print 'secheresse ',self.secheresse


        # Si volumeBarrage > Vmax alors saturation:
        if self.volumeBarrage > self.volumeMaxi:
            self.volumeBarrage = self.volumeMaxi

        if self.trace==1:
            l1=str(self.localTime)+';'\
                +str(self.volumeBarrage)+';'\
                +str(self.secheresse)+';'\
                +str(self.debordement)+';'\
                +str(debitQS)+';'\
                +str(self.debitVidange)+';'\
                +str(turbinageE)+';'\
                +str(self.gainTurbinage)+';'\
                +str(Qpompe)+';'\
                +str(self.coutPompage)+';'\
                +'\n'
            self.f_sortie.write(l1)

            msg1=Message() #
            msg2=Message() #
            msg3=Message() #

            self.vol = self.OPorts[1]
            msg1.value=[int(self.volumeBarrage)]
            #print 'envoi ',msg.value[0]
            #print self.gainTurbinage
            msg1.time = self.localTime
            self.poke(self.vol,msg1)

            self.turb = self.OPorts[2]
            msg2.value=[int(turbinageE)]
            #print 'envoi ',msg.value[0]
            #print self.gainTurbinage
            msg2.time = self.localTime
            self.poke(self.turb,msg2)

            self.pomp = self.OPorts[3]
            msg3.value=[int(Qpompe)]
            #print 'envoi ',msg.value[0]
            #print self.gainTurbinage
            msg3.time = self.localTime
            self.poke(self.pomp,msg3)

        self.flag[0]=False

	self.turb = self.OPorts[2]
	msg2.value=[int(turbinageE)]
	#print 'envoi ',msg.value[0]
	#print self.gainTurbinage
	msg2.time = self.localTime
	self.poke(self.turb,msg2)

	self.pomp = self.OPorts[3]
	msg3.value=[int(Qpompe)]
	#print 'envoi ',msg.value[0]
	#print self.gainTurbinage
	msg3.time = self.localTime
	self.poke(self.pomp,msg3)

                self.flag[0]=False

#                print self.name,self.localTime
        if self.localTime>=self.nbSem-1 :
            if self.trace==1:
                self.f_sortie.close()


            self.localTime = -1 # car iniTransition est executee apres

	    self.localTime = -1 # car iniTransition est executée après


            msg=Message() # ==> cout pompe, gain turbine, secheresse
            self.CD = self.OPorts[0]

            msg.value=[self.coutPompage]
#                        print self.gainTurbinage
            msg.value.append(self.gainTurbinage)
            msg.value.append(self.secheresse)
            msg.time = self.localTime
            self.poke(self.CD,msg)

            self.volumeBarrage=self.initVolumes[self.indB]
            self.debordement=0.0
            self.secheresse=0.0
            self.coutPompage=0.0
            self.gainTurbinage= 0.0
            self.flag[1]=False

            #print 'barrage fin 52 sem '


    def intTransition(self):
        #print "intTransition"
        self.localTime = self.localTime + 1
        self.state['sigma'] = INFINITY

        def intTransition(self):
                #print "intTransition"
                self.localTime = self.localTime + 1
                self.state['sigma'] = INFINITY

        def timeAdvance(self):
                return self.state['sigma']

    def timeAdvance(self):
        return self.state['sigma']
