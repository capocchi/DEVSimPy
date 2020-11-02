#!/usr/bin/env python

"""
This file contain the FSM class and the SCXMLToFSM function.
The FSM class allows to model a Finite State Machine and to simulate the transitions.
The FSM class uses the SCXMLToFSM function to translate a SCXML file into a dictionary compatible with the initFromSCXML FSM class method .
A FSM instance can be initialized in two diffrent ways:

FSM = FSM('On', {'start':'On', 'target':'Off', 'event':'1', 'send':'1'})

or

FSM = FSM()
FSM.initFromSCXML('FSM.xml')

The file FSM.xml is exported from the QFSM software only for the free text mode (http://qfsm.sourceforge.net/).
The next state and the output are obtained using the 'next' method:

FSM.next('1') -> ('Off', '1')
"""

from lxml import etree

import copy
import os, sys

__author__ = "Laurent Capocchi"
__copyright__ = "Copyright 2016, The TIC Project"
__credits__ = ["Laurent Capocchi"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Laurent Capocchi"
__email__ = "capocchi@univ-corse.fr"
__status__ = "Production"

class FSM():
        """ Finit State Machine class
        """
        
        def __init__(self, initState=None, transitionDict=None):
                """ Constructor.

                        initstate is the inital state of the FSM
                        transititonDcit is the state transition table that defines for all transition:
                                start: the starting state
                                target: the ending state
                                send: the output associated with the transition
                                event: the event that trigger the transition
                """
                self._initstate = initState
                self._transitiondict = transitionDict

                self._currentstate = self._initstate
                self._currentoutput = None
                self._states = []
                self._events = []
                
        def setTransitionDict(self, val):
                """ set the state transition table
                """
                self._transitiondict = val

        def getTransitionDict(self):
                """ get the state transition table
                """
                return self._transitiondict

        def setInitState(self, val):
                """ set the init state with the val value
                """
                self._initstate = val

        def getInitState(self):
                """ return the init state
                """
                return self._initstate

        def getCurrentState(self):
                """ return the current state
                """
                return self._currentstate

        def setCurrentState(self, s):
                """ set the current state
                """
                self._currentstate = s
        
        def getCurrentOutput(self):
                """ return the current output
                """
                return self._currentoutput

        def setCurrentOutput(self, val):
                """ set the current output
                """
                self._currentoutput = val
        
        def getStates(self):
                """
                """
                return self._states

        def setStates(self, states):
                """
                """
                self._states = states

        def setEvents(self, events):
                """
                """
                self._events = events
        
        def getEvents(self):
                """
                """
                return self._events

        def addStates(self, s):
                """ Add the state s into the state list
                """
                if not s in self._states:
                        self._states.append(s)
                        
        def addEvents(self, evt):
                """ Add event evt to the event list
                """
                if not evt in self._events:
                        self._events.append(s)
                        
        def initFromSCXML(self, scxml):
                """ Init FSM form scxml exported from QFSM (only for free text FSM)
                """
                D = SCXMLtoFSM(scxml)
                if D:
                        self.setInitState(D['initialstate'])
                        self.setCurrentState(self.getInitState())
                        self.setTransitionDict(D['transitions'])
                        self.setStates(D['states'])
                        self.setEvents(D['events'])

        def isCurrentState(self, s):
                """ return True if state s is the current state
                """
                return self.getCurrentState() == s

        def isInstates(self, s):
                """ return True if s is in the state list
                """
                return s in self.getStates()

        def isInEvents(self, e):
                """ return True if e is in the event list
                """
                return e in self.getEvents()
        
        def next(self, event=None):
                """ return the next state if event is received according to the state transition table
                """

                transitionDict = self.getTransitionDict()
                currentState = self.getCurrentState()
                out = []
                
                if transitionDict:
                        self._currentoutput = None 
                        for d in transitionDict:
                                if d['start'] == currentState and d['event'] == event:
                                        self.setCurrentState(d['target'])
                                        #self.setCurrentOutput(d['send'])
                                        out.append(d['send'])
                                        #break
                self.setCurrentOutput(out)
                return  (self.getCurrentState(), self.getCurrentOutput())
                
def SCXMLtoFSM(scxml):
        """
        """

        ### test if the first arg is a file
        if not os.path.isfile(scxml):
                sys.stdout.write("first arg is not a file")
                return None
        elif not (scxml.endswith("xml") or scxml.endswith("scxml")):
                sys.stdout.write("arg is not a xml file")
                return None
        else:
                D = {'states':[], 'events':[]}
                TransitionsList = []
                tree = etree.parse(scxml)
                for node in tree.iter():
                        if 'initialstate' in node.attrib.keys():
                                D['initialstate'] = node.attrib['initialstate']
                        else:
                                if type(node.tag) is str:
                                        if 'state' in node.tag:
                                                s = node.attrib['id']
                                                d = {'start':s}
                                                D['states'].append(s)
                                        elif 'transition' in node.tag:
                                                d.update(node.attrib)
                                                event = node.attrib['event']
                                                if not (event in D['events']):
                                                        D['events'].append(event)
                                                if node.getchildren() == []:
                                                        d['send']= None
                                                        TransitionsList.append(copy.copy(d))
                                        elif 'send' in node.tag:
                                                d['send']=node.attrib['event']
                                                TransitionsList.append(copy.copy(d))
                                                
                D['transitions'] = TransitionsList
                
                return D

if __name__ == '__main__':

        print(SCXMLtoFSM("scxml\FSM.xml"))

        FSM1 = FSM()
        FSM1.initFromSCXML("scxml\FSM.xml")
        print ("initial state ",FSM1.getCurrentState())

        print ("send 1 ", FSM1.next('1'))
        print ("send 0 ", FSM1.next('0'))
        print ("send 0 ", FSM1.next('0'))
        print ("send 1 ", FSM1.next('1'))

        FSM2 = FSM()
        FSM2.initFromSCXML("scxml\FSM_SC_DC.xml")
        print ("initial state ",FSM2.getCurrentState())
        print ("states ", FSM2.getStates())
        print ("events ", FSM2.getEvents())

        print(FSM2.getTransitionDict())
        
        print ("send ON ", FSM2.next('ON'))
        print ("send OFF ", FSM2.next('OFF'))
        print ("send DC ", FSM2.next('DC'))
        print ("send ON ", FSM2.next('ON'))
