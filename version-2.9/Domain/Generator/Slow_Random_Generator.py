# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:          <filename.py>
 Model:         <describe model>
 Authors:       <your name>
 Organization:  <your organization>
 Date:          <yyyy-mm-dd>
 License:       <your license>
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message
import random
import time

### Model class ----------------------------------------------------------------
class Slow_Random_Generator(DomainBehavior):
    ''' DEVS Class for Slow_Random_Generator model
    '''

    def __init__(self, minValue=0, maxValue=10, stepDuration=1):
        """ Constructor.
            @param minValue : minimum value
            @param maxValue : maximum value
            @param stepDuration : delay between 2 outputs in seconds
        """
        DomainBehavior.__init__(self)
        self.state = {'sigma':0}
        self.minValue = minValue
        self.maxValue = maxValue
        self.stepDuration = stepDuration
        self.msg = Message(None, None)

    def extTransition(self):
        ''' DEVS external transition function.
        '''
        pass

    def outputFnc(self):
        ''' DEVS output function.
        '''
        value = random.randint(self.minValue, self.maxValue)
        self.msg.value = [value, 0.0, 0.0]
        self.msg.time = self.timeNext
        print (self.msg)
        return self.poke(self.OPorts[0], self.msg)

    def intTransition(self):
        ''' DEVS internal transition function.
        '''
        time.sleep(self.stepDuration)
        self.state['sigma'] = 1

    def timeAdvance(self):
        ''' DEVS Time Advance function.
        '''
        return self.state['sigma']

    def finish(self, msg):
        ''' Additional function which is lunched just before the end of the simulation.
        '''
        pass
