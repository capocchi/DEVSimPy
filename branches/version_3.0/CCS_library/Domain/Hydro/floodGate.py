# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message


class floodGate(DomainBehavior):
        """
        This class model a standard floodGate (whith hydrogramme over time)
        @author: Bastien POGGI
        @organization: University Of Corsica
        @contact: bpoggi@univ-corse.fr
        @since: 2010.10.10
        @version: 1.0
        """

	def __init__(self,C=6.0):
            """
            @param C: The necessary time to send all water
            """
            DomainBehavior.__init__(self)

            self.state = {	'status': 'ACTIVE','sigma':INFINITY,'C':C}
            self.mesListes = []

	def extTransition(self):
		self.state['sigma']=0
		entre = self.peek(self.IPorts[0])
		entre = entre.value[0]
		self.mesListes.append(self.GenererTableauDebits(entre))

	def outputFnc(self):
		sortie = self.GenererLeDebitDeSortie()
		self.poke(self.OPorts[0],Message([sortie,0.0,0.0],self.timeNext))

	def intTransition(self):
		if(self.mesListes==[[]]):
			self.state['sigma']=INFINITY
		else:
			self.state['sigma']=1

	def timeAdvance(self):
		return self.state['sigma']

        def __str__(self):
		return "floodGate"

	def GenererTableauDebits(self,debit):
            """
            This function is used when extTransition occured. It create a list Ai (i is the current input) of the Output over the time.
            """
            resultat = []
            C = self.state['C']
            for t in range(1,self.state['C']+1):
		calcul = debit * (((t**3)/(C**3))-(((t-1)**3)/(C**3)))
		resultat.append(calcul)
            return resultat

	def GenererLeDebitDeSortie(self):
            """
            This function is used when outPutFnc occured. It send the sum of all the last Aj elements.
            """
            resultat = 0.0
            for liste in self.mesListes:
		if(liste!=[]):
                    resultat += liste[0]
                    del liste[0]
		else:
                    del liste
            return resultat




