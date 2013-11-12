# -*- coding: utf-8 -*-

"""
Name : ViewerGen.py 
Brief descritpion : Sinus generator atomic model 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 21/03/09
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS:
"""

### at the beginning to prevent with statement for python vetrsion <=2.5
from __future__ import with_statement

import os
from Domain.Myths.MythDomainBehavior import MythDomainBehavior
from Domain.Myths.Object import Myth, Message
#from Domain.Basic.Object import Message
        
#    ======================================================================    #
class ViewerGen(MythDomainBehavior):
        def __init__(self, fileName = os.path.join(os.getcwd(), "fichier.dat"), fileName2 = os.path.join(os.getcwd(), "fichier.dat")):
               
                MythDomainBehavior.__init__(self)

                self.fileName = fileName
                self.FileName2 = fileName2
                
                self.NBTOT = 0
                self.LAT = []
                self.LONG = []
                self.SIG = [0]  #le sigma
                self.mythemList = []
                
                if os.path.exists(self.fileName):
                    f = open(self.fileName,'r')
                    self.mythemList = map(lambda line: line.split(' '), map(lambda l: l.strip('\n'), f.readlines()))
                    f.close()
					
                    self.NBTOT = len(self.mythemList)
					
                if os.path.exists(self.FileName2):
                        i = 0
                        with open(self.FileName2,"rb") as f:
                                for l in filter(lambda b: b != '' , map(lambda a: a.replace('\n', ''), f.readlines())):
                                        self.LAT.append(float(l.split(' ')[0]))
                                        #self.debugger("ici")
                                        #self.debugger(self.LAT)
                                        self.LONG.append(float(l.split(' ')[1]))
                                        #self.debugger("la")
                                        #self.debugger(self.LONG)
                                        self.SIG.append(i)
                                        i += 1

                self.state = {	'status':	'ACTIVE', 'sigma':self.SIG[0], 'NbMythems':self.NBTOT}

        ###
        def intTransition(self):
                """
                """
                # (idle during dt)
                #self.debugger("entrer inttrans viewerFGen")
                
                self.state['NbMythems'] -= 1 
                
                if self.state['NbMythems'] > 0:
                    self.state['sigma'] = 0
                    
                else:
                    self.state['sigma'] = INFINITY
                    
                                  
        ###
        def outputFnc(self):
                """
                """
                assert(len(self.mythemList) == len(self.LAT) and len(self.LAT) == len(self.LONG))
				
                N = len(self.mythemList)
               
                data = [self.mythemList[N-self.state['NbMythems']], self.LAT[N-self.state['NbMythems']], self.LONG[N-self.state['NbMythems']]]
               
                self.poke(self.OPorts[0], Message(data,self.timeNext))
               
        ###
        def timeAdvance(self): return self.state['sigma']

        ###
        def __str__(self): return "ViewerGen"
