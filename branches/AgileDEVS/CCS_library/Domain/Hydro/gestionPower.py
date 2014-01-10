# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

### Model class ----------------------------------------------------------------
class gestionPower(DomainBehavior):

	def __init__(self,flowOK=0.0,levelOK=0.0):
            """
            This model is a controler for the water electric production

                @param flowOK : The minimum flow to use water electricity production
                @param levelOK : The minimum level to use water electricity production

            """

            DomainBehavior.__init__(self)

            ### local copy
            self.levelOK = levelOK
            self.flowOK = flowOK

            self.state = {
				'sigma':INFINITY
                         }
                        
            self.D = {}
            self.msg = None
            self.portOrder = None

	def extTransition(self):

            for i in range(len(self.IPorts)):
                msg = self.peek(self.IPorts[i]) #?Si le peek est vide le message sera none et pas reutilisable en sortie
                if msg:
                    self.D[i] = float(msg.value[0])
                    self.msg = msg


            if len(self.D) == len(self.IPorts):
#                """
#                DEBUG
#                """
#                print "flow:", self.D[0]
#                print "flowOK:",self.flowOK
                print "level:",self.D[1]
#                print "levelOK:",self.levelOK

               
                print self.D[1],self.levelOK

#                if  self.D[0]>self.flowOK and self.D[1]>self.levelOK:
                if  self.D[0]>self.flowOK and self.D[1]>float(self.levelOK):
                    print "TURBINER"
                    self.portOrder = 0
                else:
                    print "STOCKER"
                    self.portOrder = 1
                    
                self.state['sigma'] =0
                

	def outputFnc(self):

            if self.portOrder!=None:
                self.msg.value[0] = self.portOrder  #PB SI MSG.VALUE == NONE
#                self.msg.value = [self.portOrder]
                self.msg.time = self.timeNext

                print "envoie du message"
                print self.msg

                self.poke(self.OPorts[0], self.msg)
                self.D = {} #ne pas mettre dans interne car besoin de stoquer variable

	def intTransition(self):
            self.portOrder = None
            self.state['sigma'] = INFINITY

	def timeAdvance(self):
            return self.state['sigma']

        def __str__(self):
            return "gestionPower"