# -*- coding: utf-8 -*-

"""
    Authors: T. Ville (tim.ville@me.com)
    Date: 08/12/2014
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
    """
    Return FDDEVS parser object
    """

    def __init__(self):
        self.DECLARATION = r'''
name                    := [a-zA-Z_],[a-zA-Z0-9_]*
string                  := ("'", name, "'") / ('"', name, '"')
number                  := [1-9], [0-9]*
list                    := "(", string / number, (c" and " / (" "?, ",", " "?), string / number)*, ")"

states                  := states_fnc / state_name
states_fnc              := passive_states / hold_states
passive_states          := c"passivate in ", CURRENT_STATE, " "?, "!"
hold_states             := c"hold in ", CURRENT_STATE, c" for time ", number, " "?, "!"
transition_states       := c"from ", CURRENT_STATE, c" go to ", NEXT_STATE, " "?, "!"
state_name              := string / CURRENT_STATE / NEXT_STATE
CURRENT_STATE           := string
NEXT_STATE              := string

messages                := OUTPUT_MSG / INPUT_MSG
OUTPUT_MSG              := (number / string)+ / list
INPUT_MSG               := (number / string)+ / list

functions               := (int_transition / output_fnc / ext_transition / initial_states)
initial_states          := c"to start ", states_fnc
int_transition          := states_fnc / transition_states
output_fnc              := c"after ", CURRENT_STATE, c" output ", OUTPUT_MSG, " "?, "!"
ext_transition          := c"when in ", CURRENT_STATE, c" and receive ", INPUT_MSG, c" go to ", NEXT_STATE, " "?, "!"
'''
        self.init()

    def init(self):
        self.cg = CodeGenerator()
        self.TO_MATCHED = dict(
            int_transition=[],
            output_fnc=[],
            ext_transition=[]
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
                begin = child[1] + 1
                end = child[2] + 1
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
                success, children, nextchar = myparser.parse(test_data, production=matched)
                if success:
                    self.TO_MATCHED[matched].append(self.get_matched(children, repr(test_data), [init]))

    def generate(self, test_paths, test=False):
        """
        Entry method for generating test file
        :param test_paths: specification and destination files paths
        :param test: boolean (optional)
        """
        self.init()
        behavior = "# -*- coding: utf-8 -*-"
        behavior_path = None
        if not test:
            spec_path, behavior_path = test_paths
            with open(spec_path, 'r') as testing_s:
                spec = testing_s.read()
        else:
            spec = test_paths

        self.dispatch(spec)
        behavior += self.cg.dispatch(self.TO_MATCHED)

        if not test:
            with open(behavior_path, 'w+') as testing_b:
                testing_b.write(behavior)
        else:
            # pass
            print behavior
            return behavior

    @staticmethod
    def print_matched(matched_dict):
        """
        :param matched_dict: dict
        """
        for name in matched_dict:
            print name

            for key in matched_dict[name]:
                print "\t", key, " : ", matched_dict[name][key]


### ------------------------------------------------------------------------ ###
# =================================DECORATOR================================== #
### ------------------------------------------------------------------------ ###


class CodeGenerator():
    """
    Master object for generating code
    """

    def __init__(self):
        self.obj_list = list()
        self.generated_code = "\nfrom mock import MagicMock\n" \
                              "# from tempfile import gettempdir\n" \
                              "import sys\n" \
                              "import os\n"

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
            line = (prof * "\t") + line
            if line.endswith(":"):
                prof += 1
            # else :
            #     if prof > 0 :
            #         prof -= 1
            new_code += "\n" + line

        return new_code

    def dispatch(self, dic):
        """

        :param dic: dict
        :return: string
        """
        for key in dic.keys():
            if dic[key]:
                self.obj_list.append(eval(key)(dic[key]))
        self.propagate()
        return self.generated_code

    def propagate(self):
        """
        Execute 'generate' function for each transition type
        """
        for obj in self.obj_list:
            self.generated_code += str(obj.generate())


class GeneratorInterface(object):
    """

    :param matched: matched name for the current transition object
    """

    def __init__(self, matched=list()):
        self._fnc = ""
        self.matched = matched

    @property
    def fnc(self):
        """ Get the current fnc """
        return self._fnc

    @fnc.setter
    def fnc(self, value):
        """

        :param value: string
        """
        self._fnc = value

    def write_on_log(self, value):
        """

        :param value: string
        :return: string
        """
        #log = "with open(logFile, 'a') as log: log.write({})".format(value)
        log = "print %s" % value
        return log

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
        return """
def patch_{0}({0}):""".format(self.fnc)

    def get_real_status(self):
        """
        Generate string code for retrieving real status of model
        :return: string
        """
        return "realStatus = " + self.fnc + ".__self__.state['status']"

    def get_real_sigma(self):
        """
        :return:
        """
        return "sigma = " + self.fnc + ".__self__.state['sigma']"

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

    def execute_original_fnc(self):
        """
        :return: string
        """
        original_fnc = """
        {}()
        """.format(self.fnc)
        return original_fnc

    def generate(self):
        """
        Generate decorator and patch code
        :return: decorator and patch code
        """
        self.update_fnc()
        dec = str(self.decorator())
        dec += "\n"
        dec += str(self.patch())
        dec += "\n"
        return dec

    def decorator(self):
        """
        :return: string
        """
        dec = self.generate_decorator_struct()
        states = []
        for i in self.matched:
            states += [i[1:]]
        dec += self.conditional_structure(states)
        dec += self.execute_original_fnc()
        dec += self.specif_checker()
        dec += """ """
        dec += """
    return new_{}""".format(self.fnc)
        return dec

    def patch(self):
        """
        :return: string
        """
        pth = self.generate_patch_struct()
        pth += """
    pass"""
        return pth

    # --------------------------------------------- #
    # *********** Abstract functions ************** #
    # --------------------------------------------- #

    def update_fnc(self):
        """
        Update the function name string
        """
        pass

    def conditional_structure(self, data):
        """
        :param data: dict
        """
        pass

    def specif_checker(self):
        """
        Return a string which contain different equality in order to check specification
        """
        pass


# --------------------------------------------------------------------------------- #
# *************************** Intermediary objects ******************************** #
# --------------------------------------------------------------------------------- #
class hold_states(GeneratorInterface):
    """
    :param fnc: string
    """

    def __init__(self, fnc):
        super(hold_states, self).__init__()
        self.fnc = fnc
        self.current_status = None

    def conditional_structure(self, data, ind):
        """
        :param data: list
        :param ind: integer
        :return: string
        """
        # print "hold : "+str(data)
        self.current_status = self.get_xxx_matched_state('CURRENT_STATE', data)
        number = self.get_xxx_matched_state('number', data)

        if ind == 0:
            cond = 'if'
        else:
            cond = 'elif'

        condit_struct = """
        # hold state
        {0} realStatus.upper() == {1} and sigma == {2}:
            current_status, expected_sigma = {1}, {2}
        """.format(cond, self.current_status, number)
        return condit_struct

    def specif_checker(self):
        """
        :return: string
        """
        log = self.write_on_log(
            "'%s.{0}[%s:%s] ==> OK'%({0}.__self__.blockModel.label, current_status, sigma)".format(self.fnc))
        equality = """
        # hold state
        elif realStatus.upper() == {0} and sigma == expected_sigma:
            {1}
        """.format(self.current_status, log)
        return equality


class passive_states(GeneratorInterface):
    """
    :param fnc: string
    """

    def __init__(self, fnc):
        super(passive_states, self).__init__()
        self.fnc = fnc
        self.current_status = None

    def conditional_structure(self, data, ind):
        """
        :param data: list
        :param ind: integer
        :return: string
        """
        # print "passive : "+str(data)
        self.current_status = self.get_xxx_matched_state('CURRENT_STATE', data)

        if ind == 0:
            cond = 'if'
        else:
            cond = 'elif'

        condit_struct = """
        # passive state
        {0} realStatus.upper() == {1}:
            current_status = {1}
        """.format(cond, self.current_status)
        return condit_struct

    def specif_checker(self):
        """
        :return: string
        """
        log = self.write_on_log(
            "'%s.{0}[%s:%s] ==> OK'%({0}.__self__.blockModel.label, current_status, sigma)".format(self.fnc))
        equality = """
        # passive state
        elif realStatus == {0} and sigma == INFINITY:
            {1}
        """.format(self.current_status, log)
        return equality


class transition_states(GeneratorInterface):
    """
    :param fnc: string
    """

    def __init__(self, fnc):
        super(transition_states, self).__init__()
        self.fnc = fnc

    def conditional_structure(self, data, ind):
        """
        :param data: list
        :param ind: integer
        :return: string
        """
        condit_struct = ""
        current_status = self.get_xxx_matched_state('CURRENT_STATE', data)
        next_status = self.get_xxx_matched_state('NEXT_STATE', data)

        if ind == 0:
            cond = 'if'
        else:
            cond = 'elif'

        condit_struct += """
        # transition state
        {0} realStatus.upper() == {1} and sigma == 0:
            current_status, next_status = {1}, {2}
        """.format(cond, current_status, next_status)
        return condit_struct

    def specif_checker(self):
        """
        Generate string code for testing equality between states
        :return:
        """
        log = self.write_on_log(
            "'%s.{0}[%s-->%s] ==> OK'%({0}.__self__.blockModel.label, current_status, next_status)".format(self.fnc))
        equality = """
        # transition state
        elif realStatus == next_status:
            {0}
        """.format(log)
        return equality


# --------------------------------------------------------------------------------- #
# *************************** Transitional objects ******************************* #
# --------------------------------------------------------------------------------- #
class initial_states(GeneratorInterface):

    """
    initial states code generator object
    """

    def __init__(self, matched):
        super(initial_states, self).__init__(matched)
        self.obj = []

    def update_fnc(self):
        """
        update function name
        """
        self.fnc = "__init__"

    def conditional_structure(self, data):
        """
        :param data: list
        """
        pass

    def specif_checker(self):
        """
        :return string
        """
        pass


class int_transition(GeneratorInterface):

    """
    internal transition code generator object
    """

    def __init__(self, matched):
        super(int_transition, self).__init__(matched)
        self.obj = []

    def update_fnc(self):
        """
        Update function name
        """
        self.fnc = "intTransition"

    def conditional_structure(self, data):
        """
        :param data: list
        :return: string
        """
        obj = None
        condit_struct = """
        {0}
        {1}
        current_status, next_status, expected_sigma = None, None, None
        """.format(self.get_real_status(), self.get_real_sigma())
        for ind, line in enumerate(data):
            if len(line) == 2:
                if line[1]['Type'] == 'NEXT_STATE':
                    obj = transition_states(self.fnc)
                elif line[1]['Type'] == 'number':
                    obj = hold_states(self.fnc)

            else:
                obj = passive_states(self.fnc)
            condit_struct += obj.conditional_structure(line, ind)
            self.obj.append(obj)
        return condit_struct

    def specif_checker(self):
        """
        Generate string code for testing equality between states
        :return:
        """
        log1 = self.write_on_log("'Problem when parsing specification'")
        equality = """
        {0}
        {1}
        if current_status is None:
            {2}
        """.format(self.get_real_status(), self.get_real_sigma(), log1)
        for obj in self.obj:
            equality += obj.specif_checker()
        log2 = self.write_on_log("'Error in {0} function'".format(self.fnc))
        equality += """
        else:
            {0}
        """.format(log2)
        return equality


class ext_transition(GeneratorInterface):

    """
    external transition code generator object
    """

    def __init__(self, matched):
        super(ext_transition, self).__init__(matched)

    def update_fnc(self):
        """
        Update function name
        """
        self.fnc = "extTransition"

    def conditional_structure(self, data):
        """
        :param data: list
        :return: string
        """
        condit_struct = """
        {0}
        current_status, next_status = None, None
        model = {1}.__self__
        msg = None
        expected_msg = None
        """.format(self.get_real_status(), self.fnc)
        for ind, line in enumerate(data):
            current_state = self.get_xxx_matched_state('CURRENT_STATE', line)
            next_state = self.get_xxx_matched_state('NEXT_STATE', line)
            input_msg = self.get_xxx_matched_state('INPUT_MSG', line)

            if ind == 0:
                cond = 'if'
            else:
                cond = 'elif'
            condit_struct += """
        {1} realStatus.upper() == {2}:
            current_status, next_status = {2}, {3}
            expected_msg = {4}
        """.format(self.fnc, cond, current_state, next_state, input_msg)
        condit_struct += """
        for line in xrange(len(model.IPorts)):
            tmsg = model.peek(model.IPorts[line])

            if tmsg is not None:
                msg = tmsg
        """
        return condit_struct

    def specif_checker(self):
        """
        Generate string code for testing equality between states
        :param fnc: function name
        :param data:
        :return:
        """
        log1 = self.write_on_log("'Problem when parsing specification'")
        log2 = self.write_on_log(
            "'%s.{0}[%s --> %s : msg --> %s] ==> OK'%({0}.__self__.blockModel.label, current_status, next_status, msg.value[0])".format(
                self.fnc))
        log3 = self.write_on_log(
            "'Error in {0} function : status should be %s and we have %s'%(next_status, realStatus)".format(self.fnc))
        equality = """
        {0}
        if current_status is None and next_status is None and expected_msg is None:
            {1}
        elif realStatus == next_status:
            if (type(expected_msg) is int or type(expected_msg) is str) and msg.value[0] == expected_msg:
                {2}

            elif (type(expected_msg) is tuple or type(expected_msg) is list) and msg.value == expected_msg:
                {2}

        else:
            {3}""".format(self.get_real_status(), log1, log2, log3)
        return equality


class output_fnc(GeneratorInterface):
    """
    output function code generator object
    """

    def __init__(self, matched):
        super(output_fnc, self).__init__(matched)

    def update_fnc(self):
        """
        Update function name
        """
        self.fnc = "outputFnc"

    def conditional_structure(self, data):
        """
        :param data: list
        :return string
        """
        pass

    def specif_checker(self):
        """
        :return string
        """
        pass


### ------------------------------------------------------------------------ ###
# ===================================MAIN===================================== #
### ------------------------------------------------------------------------ ###

if __name__ == "__main__":
    PARSER = MyParser()
    if len(sys.argv) == 3:
        _, SPEC, TEST = sys.argv

        PARSER.generate((SPEC, TEST))
