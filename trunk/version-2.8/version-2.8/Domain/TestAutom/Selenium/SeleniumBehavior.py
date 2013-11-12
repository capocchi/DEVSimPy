# -*- coding: utf8 -*-
"""
-------------------------------------------------------------------------------
 Name:        <SeleniumBehavior.py>

 Authors:      <Timothee Ville>

 Date:     <2012-28-02>
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message


### Singleton pattern-----------------------------------------------------------
def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance


### Model class ----------------------------------------------------------------
### Selenium Behaviour class ---------------------------------------------------
@singleton
class SeleniumBehavior(object):

	def __init__(self):
		self.varsArray = {}
		self.textVars = ""
	
	
	def addVarToArray(self, var):
		if not(var in self.varsArray) and (var !=''):
			self.varsArray[var]=self.coordinate(var)
	
	
	def getAllVars(self):
		return self.textVars
	
	
	def coordinate(self, var):
		if var!='':
			self.textVars += "\n"+self.transformVar(var)+"\t"+var
			return self.transformVar(var)
		else:
			return ''
	
	
	def transformVar(self, var):
		# transform var in ${var} for the declaration variable
		if var!='':
				return "${%s}"%(self.is_url(var))
	
	
	def is_url(self, var):
		if var[:4] == "http":
			tmp=var[7:].split('.')
			return tmp[1]
		else:
			return var


### Action class ---------------------------------------------------------------
class Action(DomainBehavior):
	
	def __init__(self):
		DomainBehavior.__init__(self)
		self.singleton = SeleniumBehavior()
		
		# State variable
		self.state = {'status': 'ACTIVE', 'sigma':0}
		
		self.sentencesResource = ""
		self.sentencesTest = ""
		
		self.msg = Message()
	
	
	def extTransition(self):
		pass
	
	
	def intTransition(self):
		self.state = {'status': 'IDLE', 'sigma':INFINITY}
	
	
	def outputFnc(self):
		self.msg.value=[[self.sentencesResource],self.sentencesTest,0.0]
		
		self.msg.time=self.timeNext
		for output in xrange(len(self.OPorts)):
			self.poke(self.OPorts[output],self.msg)
	
	
	def timeAdvance(self):
		return self.state['sigma']
	
	
	def setSentencesResource(self, sentencesResource):
		self.sentencesResource = sentencesResource
	
	
	def setSentencesTest(self, sentencesTest):
		self.sentencesTest = sentencesTest
	

### Should class ---------------------------------------------------------------
class Should(DomainBehavior):
	
	def __init__(self, sentences=""):
		DomainBehavior.__init__(self)
		self.singleton = SeleniumBehavior()
		
		# Instance variables definitions
		self.sentences = sentences
		self.sentenceResource = ""
		self.sentenceTest = ""
		self.msg = Message()
		
		# State variable
		# self.state = {'status': 'ACTIVE', 'sigma':INFINITY} 
		self.state = {'status': 'ACTIVE', 'sigma':0}
	
	
	def extTransition(self):
		for test in xrange(len(self.IPorts)):
			msg = self.peek(self.IPorts[test])
			if msg is not None:
				self.state = {'status': 'ACTIVE', 'sigma':0}
				self.sentenceResource = msg.value[0][0]+self.sentences
				self.sentenceTest = msg.value[1]
			del msg
	
	
	def intTransition(self):
		if len(self.IPorts) == 0:
			self.sentenceTest = self.sentences
			self.outputFnc()
			
		self.state = {'status': 'IDLE', 'sigma':INFINITY}
	
	
	def outputFnc(self):
		if self.sentenceTest != "":
			self.msg.value=[[self.sentenceResource],self.sentenceTest,0.0]
			self.msg.time=self.timeNext
			for output in xrange(len(self.OPorts)):
				self.poke(self.OPorts[output],self.msg)
	
	
	def timeAdvance(self):
		return self.state['sigma']
	
