# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------------------
 Name:        <Generator.py>

 Authors:      <Timothee Ville>

 Date:     <2012-28-02>
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

### Constants ------------------------------------------------------------------
TAB = '\t'
SIGN = '\n\t'
BODY_FUNC = '\n\t\t'


### Action class ---------------------------------------------------------------
class Generator(DomainBehavior):

    def __init__(self):
        DomainBehavior.__init__(self)

        # State variable
        self.state = {'status': 'ACTIVE', 'sigma':0}

        self.function = ""
        self.inRun = ""
        #self.sign = ""
        #self.body = [None]*100
        self.sentencesTest = ""

        self.msg = Message()

    def extTransition(self):
        pass

    def intTransition(self):
        self.state = {'status': 'IDLE', 'sigma':INFINITY}

    def outputFnc(self):
        self.msg.value = [[self.function], [self.inRun], 0.0]

        self.msg.time = self.timeNext
        for output in xrange(len(self.OPorts)):
            self.poke(self.OPorts[output], self.msg)

    def timeAdvance(self):
        return self.state['sigma']

    def setFunction(self, function):
        self.function = function

    def setInRun(self, inRun):
        self.inRun = inRun

    def declareFunction(self, function_tab=""):
        function = ""
        inFunc = False
        begin = False

        # Retrieve each lines of function declaration
        func = function_tab.split('\n')

        # Indent correctly
        count = 0
        tmp = 0
        for line in func:
            size = len(line) - 1

            if line.startswith('def'):
                begin = True

            elif line[size] == ':' and inFunc:
                count += 1
            else:
                count -= 1
                if count < 0:
                    count = 0

            if not inFunc and not begin:
                function += SIGN + line
            elif tmp <= 0 and inFunc:
                function += BODY_FUNC + line
            elif inFunc:
                function += BODY_FUNC + tmp * TAB + line
            elif begin and not inFunc:
                function += SIGN + line
                inFunc = True

            tmp = count
        self.function = function
