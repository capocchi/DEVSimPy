from nose.tools import assert_equals
from Grammar import MyParser

HEAD = """# -*- coding: utf-8 -*-
from mock import MagicMock
# from tempfile import gettempdir
import sys
import os
"""

INT_TRANS = """
def dec_intTransition(intTransition):
    def new_intTransition():
        realStatus = intTransition.__self__.state['status']
        sigma = intTransition.__self__.state['sigma']
        current_status, next_status, expected_sigma = None, None, None
        
        {0}
        
        intTransition()
        
        realStatus = intTransition.__self__.state['status']
        sigma = intTransition.__self__.state['sigma']
        if current_status is None:
            print 'Problem when parsing specification'
        
        {1}
        
        else:
            print 'Error in intTransition function'
         
    return new_intTransition

def patch_intTransition(intTransition):
    pass
"""

EXT_TRANS = """
def dec_extTransition(extTransition):
    def new_extTransition():
        realStatus = extTransition.__self__.state['status']
        current_status, next_status = None, None
        model = extTransition.__self__
        msg = None
        expected_msg = None
        
        {0}

            for line in xrange(len(model.IPorts)):
                tmsg = model.peek(model.IPorts[line])

                if tmsg is not None:
                    msg = tmsg
        
        extTransition()
        
        realStatus = extTransition.__self__.state['status']
        if current_status is None and next_status is None and expected_msg is None:
            print 'Problem when parsing specification'
        elif realStatus == next_status:
            {1}

            elif (type(expected_msg) is tuple or type(expected_msg) is list) and msg.value[0] in expected_msg:
                print '%s.extTransition[%s --> %s : msg --> %s] ==> OK'%(extTransition.__self__.blockModel.label, current_status, next_status, msg.value[0])

        else:
            print 'Error in extTransition function : status should be %s and we have %s'%(next_status, realStatus) 
    return new_extTransition

def patch_extTransition(extTransition):
    pass
"""

class TestGrammar:

    def setup(self):
        self.parser = MyParser()
        expected = ""

    def teardown(self):
        pass

    def test_hold_states(self):
        SPEC = "hold in 'ACTIVE' for time 10 !"

        x1 = """# hold state
        if realStatus.upper() == 'ACTIVE' and sigma == 10:
            current_status, expected_sigma = 'ACTIVE', 10"""

        x2 = """# hold state
        elif realStatus.upper() == 'ACTIVE' and sigma == expected_sigma:
            print '%s.intTransition[%s:%s] ==> OK'%(intTransition.__self__.blockModel.label, current_status, sigma)"""

        expected = HEAD+INT_TRANS.format(x1, x2)
        assert_equals(self.parser.generate(SPEC, True), expected)

    def test_passive_states(self):
        SPEC = "passivate in 'IDLE' !"

        x1 = """# passive state
        if realStatus.upper() == 'IDLE':
            current_status = 'IDLE'"""

        x2 = """# passive state
        elif realStatus == 'IDLE' and sigma == INFINITY:
            print '%s.intTransition[%s:%s] ==> OK'%(intTransition.__self__.blockModel.label, current_status, sigma)"""

        expected = HEAD+INT_TRANS.format(x1, x2)
        assert_equals(self.parser.generate(SPEC, True), expected)

    def test_transition_states(self):
        SPEC = "from 'ACTIVE' go to 'IDLE' !"

        x1 = """# transition state
        if realStatus.upper() == 'ACTIVE' and sigma == 0:
            current_status, next_status = 'ACTIVE', 'IDLE'"""
        
        x2 = """# transition state
        elif realStatus == next_status:
            print '%s.intTransition[%s-->%s] ==> OK'%(intTransition.__self__.blockModel.label, current_status, next_status)"""
        expected = HEAD+INT_TRANS.format(x1, x2)
        assert_equals(self.parser.generate(SPEC, True), expected)

    def test_initial_states(self):
        pass

    def test_int_transition_passive_transition(self):
        SPEC = """from 'ACTIVE' go to 'IDLE' !
passivate in 'IDLE' !
hold in 'ACTIVE' for time 10 !"""
        
        x1 = """# transition state
        if realStatus.upper() == 'ACTIVE' and sigma == 0:
            current_status, next_status = 'ACTIVE', 'IDLE'
        
        # passive state
        elif realStatus.upper() == 'IDLE':
            current_status = 'IDLE'
        
        # hold state
        elif realStatus.upper() == 'ACTIVE' and sigma == 10:
            current_status, expected_sigma = 'ACTIVE', 10"""

        x2 = """# transition state
        elif realStatus == next_status:
            print '%s.intTransition[%s-->%s] ==> OK'%(intTransition.__self__.blockModel.label, current_status, next_status)
        
        # passive state
        elif realStatus == 'IDLE' and sigma == INFINITY:
            print '%s.intTransition[%s:%s] ==> OK'%(intTransition.__self__.blockModel.label, current_status, sigma)
        
        # hold state
        elif realStatus.upper() == 'ACTIVE' and sigma == expected_sigma:
            print '%s.intTransition[%s:%s] ==> OK'%(intTransition.__self__.blockModel.label, current_status, sigma)"""

        expected = HEAD+INT_TRANS.format(x1, x2)
        assert_equals(self.parser.generate(SPEC, True), expected)

    def test_ext_transition(self):
        SPEC = """when in 'IDLE' and receive (1, 2, 3, 'truc') go to 'ACTIVE' !
when in 'ACTIVE' and receive ('stop') go to 'IDLE' !"""

        x1 = """if realStatus.upper() == 'IDLE':
            current_status, next_status = 'IDLE', 'ACTIVE'
            expected_msg = (1, 2, 3, 'truc')"""

        x2 = """if (type(expected_msg) is int or type(expected_msg) is str) and msg.value[0] == expected_msg:
                print '%s.extTransition[%s --> %s : msg --> %s] ==> OK'%(extTransition.__self__.blockModel.label, current_status, next_status, msg.value[0])"""

        expected = HEAD+EXT_TRANS.format(x1, x2)
        assert_equals(self.parser.generate(SPEC, True), expected)

    def test_output_fnc(self):
        pass