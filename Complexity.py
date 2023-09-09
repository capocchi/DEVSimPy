# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Complexity.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 03/15/20
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import os, sys
import Components
import textwrap

import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
from Utilities import getInstance

def GetMacCabeMetric(path):
    """
    """

    complexity = 0.0

    try:
        p = os.path.dirname(path)
        if p not in sys.path:
            sys.path.append(p)
        import maccabe as codepaths
    except ImportError as info:
        msg = 'ERROR: maccabe module not imported: %s\n'%info
        sys.stderr.write(msg)
        return complexity
    else:
        
        cls = Components.GetClass(path)
        if inspect.isclass(cls):
            args = Components.GetArgs(cls)
            devs = getInstance(cls, args)

            ### Get class of model
            if not path.endswith('.pyc'):

                ### mcCabe complexity
                ### beware to use tab for devs code of models

                L = [getattr(cls,fct) for fct in ('extTransition','intTransition','outputFnc') if hasattr(cls, fct)]
                
                ### when model is created, the transition functions are empty...
                try:
                    source_list = list(map(inspect.getsource, L))
                except Exception as info:
                    source_list = []

                L_args = []

                complexity = 0.0
                for text in source_list:
                    ### textwrap for deleting the indentation

                    try:
                        ast = codepaths.ast.parse(textwrap.dedent(text).strip())
                        visitor = codepaths.PathGraphingAstVisitor()
                        visitor.preorder(ast, visitor)
                    except Exception as info:
                        sys.stdout.write("Error in Complexity module")
                    else:
                        for graph in visitor.graphs.values():
                            complexity += graph.complexity()
                            
                return complexity
                ### for .pyc file
            else:
                return 0.0
        else:
            return 0.0

if __name__ == "__main__":
    # execute only if run as a script
    path = sys.argv[1]
    sys.stdout.write(str(GetMacCabeMetric(path)))
