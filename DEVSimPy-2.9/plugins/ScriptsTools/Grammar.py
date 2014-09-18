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

DECLARATION = r'''
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
output_fnc              := c"after ", state_name, c" output ", OUTPUT_MSG, " "?, "!"
ext_transition          := c"when in ", state_name, c" and receive ", INPUT_MSG, c" go to ", NEXT_STATE, " "?, "!"
'''

### ------------------------------------------------------------------------ ###
# =================================UTILITY==================================== #
### ------------------------------------------------------------------------ ###

def getparser():
    """ DocString """
    return Parser(DECLARATION)

def getmatched(children, data, matched):
    """ DocString """
    for child in children:
        if child[0] in MATCH_LIST:
            begin = child[1]+1
            end = child[2]+1
            match = data[begin:end]
            matched.append({"Matched" : match, "Type" : child[0]})

        else:
            getmatched(child[3], data, matched)
    return matched

def dispatch(data):
    """ DocString """
    parser = getparser()
    for test_data in data.splitlines():
        test_data = test_data.strip()
        init = False
        if test_data.startswith(INIT_START):
            init = True
            test_data = (test_data[len(INIT_START):]).strip()

        for matched in TO_MATCHED.keys():

            if test_data.startswith(TO_MATCHED[matched]["start"]):

                _, children, _ = parser.parse(test_data, production=matched)
                TO_MATCHED[matched]["matched"].append(getmatched(children, repr(test_data), [init]))
    return TO_MATCHED

def generate(test_paths, test=False):
    """ DocString """
    behavior = "# -*- coding: utf-8 -*-"
    if not test:
        spec_path, behavior_path = test_paths
        with open(spec_path, 'r') as testing_s:
            spec = testing_s.read()
    else: 
        spec = test_paths
    matched_dict = dispatch(spec)

    for key in matched_dict:
        if not matched_dict[key]["matched"] == []:

            if matched_dict[key]["matched"][0][0]:
                behavior += initial_states(matched_dict[key]["matched"][0][1])
            else:
                behavior += matched_dict[key]["delegate"](matched_dict[key]["matched"])
    if not test:
        with open(behavior_path, 'w+') as testing_b:
            testing_b.write(behavior)
    else:
        print behavior
    

def print_matched(matched_dict):
    """ DocString """
    for name in matched_dict:
        print name

        for key in matched_dict[name]:
            print "\t", key, " : ", matched_dict[name][key]

def reindent(code):
    """ DocString """
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

### ------------------------------------------------------------------------ ###
# =================================DECORATOR================================== #
### ------------------------------------------------------------------------ ###
# ==================================LIBRARY=================================== #
### ------------------------------------------------------------------------ ###

def get_real_status(fnc):
    """ DocString """
    return "realStatus = "+fnc+".__self__.state['status']"

def get_xxx_matched_state(xxx, data):
    """ DocString """
    matched = None
    for i in data:
        if i['Type'] == xxx:
            matched = i['Matched']
    return matched

def state_equality(fnc, data):
    """ DocString """
    equality = ""
    equality += "\n"+get_real_status(fnc)
    enum = enumerate(data)
    for ind, states in enum:
        state_name = get_xxx_matched_state('CURRENT_STATE', states)
        next_state = get_xxx_matched_state('NEXT_STATE', states)
        if ind == 0:
            equality += "\nif realStatus.upper() == '"+state_name.upper()+"':"
        else:
            equality += "\nelse if realStatus.upper() == '"+state_name.upper()+"':"
        equality += "\nstatus = '"+next_state+"'"
        equality += "\n"+fnc+"()"
        equality += "\n"+get_real_status(fnc)
        equality += "\nif realStatus == status :"
        equality += "\nprint '"+fnc+"["+state_name.upper()+"-->"+next_state+"] ==> OK'"
        equality += "\nelse :"
        equality += "\nprint 'Error in intTransition function : status should be %s and we have %s'%(status, realStatus)"
    return equality

### ----------------------------------------------------------------------- ###
# =================================GENERATOR================================= #
### ----------------------------------------------------------------------- ###

def generate_struct(fnc):
    """ DocString """
    struct = ""
    struct += CODING
    struct = "def dec_"+fnc+"("+fnc+"):"
    struct += "\ndef new_"+fnc+"():"
    return struct

def initial_states(data):
    """ DocString """
    dec = "__init__"
    # print data
    # print generate_struct(dec)
    return reindent(dec)


def hold_states(data):
    """ DocString """
    print "hold "+repr(data)
    # print data
    # return reindent(dec)

def passive_states(data):
    """ DocString """
    print "passive "+repr(data)
    # print data
    # return reindent(dec)

def int_transition(data):
    """ DocString """
    fnc = "intTransition"
    # print generate_struct(dec)
    dec = generate_struct(fnc)
    states = []
    for i in data:
        states += [i[1:]]
    dec += "\n"+state_equality(fnc, states)
    dec = reindent(dec)
    dec += "\n\t\telse :\n\t\t\tintTransition()"
    dec += "\n\treturn new_"+fnc
    return dec


def output_fnc(data):
    """ DocString """
    dec = "outputFnc"
    # print data
    # print generate_struct(dec)
    return reindent(dec)

def ext_transition(data):
    """ DocString """
    dec = "extTransition"
    # print data
    # print generate_struct(dec)
    return reindent(dec)

### ------------------------------------------------------------------------ ###
# ================================MATCH DICT================================== #
### ------------------------------------------------------------------------ ###

TO_MATCHED = {
    "passive_states" : {"start": "passivate", "matched": [], "delegate": passive_states},
    "hold_states"    : {"start": "hold in",   "matched": [], "delegate": hold_states},
    "int_transition" : {"start": "from",      "matched": [], "delegate": int_transition},
    "output_fnc"     : {"start": "after",     "matched": [], "delegate": output_fnc},
    "ext_transition" : {"start": "when in",   "matched": [], "delegate": ext_transition}
}

### ------------------------------------------------------------------------ ###
# ===================================MAIN===================================== #
### ------------------------------------------------------------------------ ###

if __name__ == "__main__":
    if len(sys.argv) == 1:
        SPECIFICATIONS = """
        from ACTIVE go to IDLE !
        """
        generate(SPECIFICATIONS, True)

    elif len(sys.argv) == 3:
        _, SPEC, TEST = sys.argv
        generate((SPEC, TEST))

