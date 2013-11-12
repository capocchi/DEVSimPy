# -*- coding: utf-8 -*-

#IMPORT
from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message
from Domain.Strategy.lib.GIScompute import GIScompute
from Domain.GIS.GISobject import GISobject
from Domain.Strategy.evaluated.abstractEvaluated import AbstractEvaluated
from Domain.Strategy.evaluator.abstractEvaluator import AbstractEvaluator
from Domain.Strategy.deploiement.deploiementResult import DeploiementResult

class Deploiement(DomainBehavior):

#INITIALISATION
	def __init__(self):
            DomainBehavior.__init__(self)
            self.initState()
            self.initVariable()

#DEVS
	def extTransition(self):
            self.scanPorts()
            if self.isReadyToDeploy():
#                print "DEPLOIEMENT :: LAUNCH DEPLOIEMENT"
                self.createDeploiement()
#            else:
#                print "DEPLOIEMENT :: NOT ENOUGHT COMPONEMENT TO LAUNCH DEPLOIEMENT"
            self.state['sigma'] = 0


  	def outputFnc(self):
            message = Message()
            message.value = [self.myDeploiement]
            message.time = self.timeNext
            self.poke(self.OPorts[0],message)


        def intTransition(self):
            self.state['sigma'] = INFINITY


  	def timeAdvance(self):
            return self.state['sigma']


#INTERNAL FUNCTIONS
        def initState(self):
            self.state = {'status':'IDLE', 'sigma':INFINITY}

        def initVariable(self):
            self.myEvaluated = None
            self.myEvaluator = None
            self.myGISobject = None
            self.myDeploiement = []


#-------Delta Ext internal functions
        def scanPorts(self):
            for port in self.IPorts:
                theMessage = self.peek(port)
                if theMessage != None:
                    theMessageValue = theMessage.value[0]
                    if isinstance(theMessageValue,AbstractEvaluated):
                        self.myEvaluated = theMessageValue
#                        print "evaluated"
                    elif isinstance(theMessageValue,AbstractEvaluator):
                        self.myEvaluator = theMessageValue
#                        print "evaluator"
                    elif isinstance(theMessageValue,GISobject):
                        self.myGISobject = theMessageValue
#                        print "geographic object"


        def isReadyToDeploy(self):
            if self.myEvaluated != None and self.myEvaluator != None and self.myGISobject != None:
                return True
            else:
                return False


        def createDeploiement(self):
            if str(self.myGISobject) == "Line":
                self.createDeploiementLine()
            elif str(self.myGISobject) == "Polygon":
                self.createDeploiementPolygon()
            elif str(self.myGISobject) == "Point":
                self.createDeploiementPoint()


        def createDeploiementLine(self):
#            print "Calcul d'un deploiement sous forme de Ligne"
            myLine = self.myGISobject.listCoordinates
            for i in range(len(myLine)-1):
                self.myDeploiement += self.createSegment(myLine[i], myLine[i+1])


        def createDeploiementPolygon(self):
            print "Calcul d'un deploiement sous forme de Polygon"
            #TODO


        def createDeploiementPoint(self):
            print "Calcul d'un deploiement sous forme d'étoile"
            #TODO


        def createSegment(self,pointA,pointB):
            #Initialisations
            myGIScompute = GIScompute()
            result = [DeploiementResult(pointA, self.myEvaluator.getRangePlacement(self.myEvaluated, pointA))]
            distanceDo = 0

            #Calculs
            distanceToDo = myGIScompute.computeDistanceBetweenTwoPoint(pointA, pointB)
            angle = myGIScompute.computeHandlingBetweenTwoPoint(pointA, pointB)

            #Iteration
            while distanceDo < distanceToDo:

                newPoint = self.myEvaluator.getNextPlacement(self.myEvaluated, result[len(result)-1].point, angle)
                newArea = self.myEvaluator.getRangePlacement(self.myEvaluated, newPoint)
                theDeploiementResult = DeploiementResult(newPoint, newArea)
                result.append(theDeploiementResult)

                distanceDo = myGIScompute.computeDistanceBetweenTwoPoint(pointA, result[len(result)-1].point)

            return result



#INTERNAL FUNCTIONS
	def __str__(self):
            return "deploiementLine"