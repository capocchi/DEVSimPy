#MODULES DEVS
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.Basic.Object import Message
import pickle
#VOIR PLUGIN ACTIVITY

class SimpleAtomicModel(DomainBehavior):
    
    def __init__(self):
        DomainBehavior.__init__(self)
        self.state = {'sigma' : INFINITY}
        self.inputDic = {}
        self.historyState = []
        self.mode = "LOG"

#TRANSMISSION DE MESSAGE
    def sendMessage(self,NumPort, message):
        msg = Message()
        msg.value = [message]
        msg.time = self.timeNext
        self.poke(self.OPorts[NumPort], msg)

#LECTURE MESSAGE (INDIVIDUEL AVEC RETOUR)  
    def readMessage(self):
        for port in self.IPorts :
            msg = self.peek(port)
            if msg:
                return msg.value[0]
        return None
        
#LECTURE MESSAGE (LISTE AVEC ATTRIBUT DE CLASSE)
    def updateInputMessagesDic(self):
        for i in range(len(self.IPorts)):
            if self.peek(self.IPorts[i]):
                message = self.peek(self.IPorts[i])
                self.inputDic[str(i)] = message.value[0]

#HISTORIQUE
    def saveState(self):
        #SAV DE LOBJET DANS UNE LISTE DE CHAINE
        self.historyState.append(pickle.dumps(self))
        
    def getStates(self,nameVariable):
        states = []
        for rec in self.historyState:
            theObject = pickle.loads(rec)
            states.append(getattr(theObject,nameVariable))
        return states
    
    def becomeActivate(self):
        self.state['sigma'] = 0
        
    def becomeDesactivate(self):
        self.state['sigma'] = INFINITY
        
#DEBUGAGE
    def showScreen(self, information):
        if self.mode == "LOG":
            print str(self), " : ",  information
        

#DEVS 
    def timeAdvance(self):
        return self.state['sigma']


