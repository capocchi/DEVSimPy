# -*- coding: utf-8 -*-

"""
    Authors: T. Ville (tim.ville@me.com)
    Date: 02/07/2014
    Description:
    Depends: simpleparse
"""

# from simpleparse.common import numbers, strings, comments
from simpleparse.parser import Parser
import sys

### ------------------------------------------------------------------------ ###
# =================================CONTANTS=================================== #
### ------------------------------------------------------------------------ ###

MATCH_LIST = ["state_name", "CURRENT_STATE", "NEXT_STATE", "OUTPUT_MSG", "INPUT_MSG", "number"]
INIT_START = "to start"
CODING = "# -*- coding: utf-8 -*-"

### ------------------------------------------------------------------------ ###
# ==================================GRAMMAR=================================== #
### ------------------------------------------------------------------------ ###


class MyParser():

    def __init__(self):
        self.DECLARATION = r'''
string                  := [a-zA-Z_],[a-zA-Z0-9_]*
number                  := [1-9], [0-9]*

states                  := states_fnc / state_name
states_fnc              := initial_states / passive_states / hold_states
initial_states          := c"to start ", (passive_states / hold_states)
passive_states          := c"passivate in ", state_name, " "?, "!"
hold_states             := c"hold in ", state_name, c" for time ", number, " "?, "!"
state_name              := string / CURRENT_STATE / NEXT_STATE
CURRENT_STATE           := string
NEXT_STATE              := string

messages                := OUTPUT_MSG / INPUT_MSG
OUTPUT_MSG              := (number / string)+
INPUT_MSG               := (number / string)+

functions               := (int_transition / output_fnc / ext_transition)
int_transition          := c"from ", CURRENT_STATE, c" go to ", NEXT_STATE, " "?, "!"
output_fnc              := c"after ", CURRENT_STATE, c" output ", OUTPUT_MSG, " "?, "!"
ext_transition          := c"when in ", CURRENT_STATE, c" and receive ", INPUT_MSG, c" go to ", NEXT_STATE, " "?, "!"
'''
        self.cg = CodeGenerator()
        self.TO_MATCHED = dict(
            passive_states=dict(start="passivate", matched=[]),
            hold_states=dict(start="hold in", matched=[]),
            int_transition=dict(start="from", matched=[]),
            output_fnc=dict(start="after", matched=[]),
            ext_transition=dict(start="when in", matched=[])
        )

    def get_parser(self):
        """
        Get the grammar parser
        :return: Parser
        """
        return Parser(self.DECLARATION)

    def get_matched(self, children, data, matched):
        """
        Return a list of matched words
        :param children:
        :param data:
        :param matched:
        :return: matched
        """
        for child in children:
            if child[0] in MATCH_LIST:
                begin = child[1]+1
                end = child[2]+1
                match = data[begin:end]
                matched.append({"Matched": match, "Type": child[0]})

            else:
                self.get_matched(child[3], data, matched)
        return matched

    def dispatch(self, data):
        """
        Dispatch matched word into the right place on dictionary
        :param data: specifications
        """
        myparser = self.get_parser()
        for test_data in data.splitlines():
            test_data = test_data.strip()
            init = False
            if test_data.startswith(INIT_START):
                init = True
                test_data = (test_data[len(INIT_START):]).strip()
            for matched in self.TO_MATCHED.keys():
                if test_data.startswith(self.TO_MATCHED[matched]["start"]):
                    _, children, _ = myparser.parse(test_data, production=matched)
                    self.TO_MATCHED[matched]["matched"].append(self.get_matched(children, repr(test_data), [init]))

    def generate(self, test_paths, test=False):
        """
        Entry method for generating test file
        :param test_paths: specification and destination files paths
        :param test: boolean (optional)
        """
        behavior = "# -*- coding: utf-8 -*-"
        if not test:
            spec_path, behavior_path = test_paths
            with open(spec_path, 'r') as testing_s:
                spec = testing_s.read()
        else:
            spec = test_paths

        self.dispatch(spec)
        behavior = self.cg.dispatch(self.TO_MATCHED)

        if not test:
            with open(behavior_path, 'w+') as testing_b:
                testing_b.write(behavior)
        else:
            print behavior

    @staticmethod
    def print_matched(matched_dict):
        """ DocString """
        for name in matched_dict:
            print name

            for key in matched_dict[name]:
                print "\t", key, " : ", matched_dict[name][key]


### ------------------------------------------------------------------------ ###
# =================================DECORATOR================================== #
### ------------------------------------------------------------------------ ###


class CodeGenerator():

    def __init__(self):
        self.obj_list = list()
        self.generated_code = ""

    @staticmethod
    def reindent(code):
        """
        :param code:
        :return: string
        """
        tab = code.split("\n")
        new_code = ""
        prof = 0
        for line in tab:
            if line.startswith("else") and prof > 0:
                prof -= 1
            line = (prof*"\t")+line
            if line.endswith(":"):
                prof += 1
            # else :
            #     if prof > 0 :
            #         prof -= 1
            new_code += "\n"+line

        return new_code

    def dispatch(self, dic):
        for key in dic.keys():
            if dic[key]['matched'] != []:
                self.obj_list.append(eval(key)(dic[key]['matched']))
        self.propagate()
        return self.generated_code

    def propagate(self):
        for obj in self.obj_list:
            self.generated_code += str(obj.generate())


class GeneratorInterface(object):

    def __init__(self, matched=list()):
        self._fnc = ""
        self.matched = matched

    @property
    def fnc(self):
        """ Get the current fnc """
        return self._fnc

    @fnc.setter
    def fnc(self, value):
        self._fnc = value

    def generate_decorator_struct(self):
        """
        Generate string code for decorator structure
        :return: string code for decorator structure
        """
        struct = """
def dec_{0}({0}):
    def new_{0}():""".format(self.fnc)
        return struct

    def generate_patch_struct(self):
        """
        Generate string code for patch structure
        :return:string code for patch structure
        """
        return ""

    def get_real_status(self):
        """
        Generate string code for retrieving real status of model
        :param fnc: function name
        :return: string
        """
        return "realStatus = "+self.fnc+".__self__.state['status']"

    def get_xxx_matched_state(self, xxx, data):
        """
        Generate string code for retrieving matched word of type xxx
        :param xxx: type name
        :param data: matched list
        :return: List
        """
        matched = None
        for i in data:
            if i['Type'] == xxx:
                matched = i['Matched']
        return matched

    def state_equality(self):
        """
        Generate string code for testing equality between states
        :param fnc: function name
        :param data:
        :return:
        """
        equality = """
        {0}
        if realStatus == next_status:
            print '%s.{1}[%s-->%s] ==> OK'%({1}.__self__.blockModel.label, current_status, next_status)
        else:
            print 'Error in intTransition function : status should be %s and we have %s'%(next_status, realStatus)""".format(self.get_real_status(), self.fnc)
        return equality

    def state_conditional_structure(self, data):
        cond = None
        condit_struct = """
        {0}
        current_status, next_status = None, None""".format(self.get_real_status())
        for ind, line in enumerate(data):
            current_state = self.get_xxx_matched_state('CURRENT_STATE', line)
            next_state = self.get_xxx_matched_state('NEXT_STATE', line)
            if ind == 0:
                cond = 'if'
            else:
                cond = 'elif'
            condit_struct += """
        {0} realStatus.upper() == '{1}':
            current_status, next_status = '{1}', '{2}'""".format(cond, current_state, next_state)
        return condit_struct

    def execute_original_fnc(self):
        original_fnc = """
        {}()""".format(self.fnc)
        return original_fnc

    def update_fnc(self):
        pass

    def generate(self):
        """
        Generate decorator and patch code
        :return: decorator and patch code
        """
        self.update_fnc()
        dec = self.decorator()
        dec += self.patch()
        return dec

    def decorator(self):
        pass

    def patch(self):
        pass

class initial_states(GeneratorInterface):

    def decorator(self):
        pass

    def patch(self):
        pass

    def update_fnc(self):
        self.fnc = "__init__"


class hold_states(GeneratorInterface):

    def update_fnc(self):
        self.fnc = ""

    def decorator(self):
        pass

    def patch(self):
        pass


class passive_states(GeneratorInterface):

    def update_fnc(self):
        self.fnc = ""

    def decorator(self):
        pass

    def patch(self):
        pass


class int_transition(GeneratorInterface):

    def update_fnc(self):
        self.fnc = "intTransition"

    def decorator(self):
        dec = self.generate_decorator_struct()
        states = []
        for i in self.matched:
            states += [i[1:]]
        dec += self.state_conditional_structure(states)
        dec += self.execute_original_fnc()
        dec += self.state_equality()
        dec += """
    return new_{}""".format(self.fnc)
        return dec

    def patch(self):
        patch = self.generate_patch_struct()
        return patch


class ext_transition(GeneratorInterface):

    def update_fnc(self):
        self.fnc = 'extTransition'

    def decorator(self):
        dec = self.generate_decorator_struct()
        states = []
        for i in self.matched:
            states += [i[1:]]
        dec += self.state_conditional_structure(states)
        dec +=self.execute_original_fnc()
        dec += self.state_equality()
        dec += """
    return new_{}""".format(self.fnc)
        return dec

    def patch(self):
        return ""


class output_fnc(GeneratorInterface):

    def update_fnc(self):
        self.fnc = "outputFnc"

    def decorator(self):
        pass

    def patch(self):
        pass


### ------------------------------------------------------------------------ ###
# ===================================MAIN===================================== #
### ------------------------------------------------------------------------ ###

if __name__ == "__main__":
    parser = MyParser()
    if len(sys.argv) == 1:
        SPECIFICATIONS = """
        from ACTIVE go to IDLE !
        """
        parser.generate(SPECIFICATIONS, True)

    elif len(sys.argv) == 3:
        _, SPEC, TEST = sys.argv

        parser.generate((SPEC, TEST))
