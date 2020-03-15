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
ABS_HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

import builtins
### specific built-in variables. (don't modify the default value. If you want to change it, go to the PreferencesGUI from devsimpy interface.)
builtin_dict = {'SPLASH_PNG': os.path.join(ABS_HOME_PATH, 'splash', 'splash.png'), # abslolute path
				'DEVSIMPY_PNG': 'iconDEVSimPy.png',	# png file for devsimpy icon
				'HOME_PATH': ABS_HOME_PATH,
				'ICON_PATH': os.path.join(ABS_HOME_PATH, 'icons'),
				'ICON_PATH_16_16': os.path.join(ABS_HOME_PATH, 'icons', '16x16'),
				'SIMULATION_SUCCESS_SOUND_PATH': os.path.join(ABS_HOME_PATH,'sounds', 'Simulation-Success.wav'),
				'SIMULATION_ERROR_SOUND_PATH': os.path.join(ABS_HOME_PATH,'sounds', 'Simulation-Error.wav'),
				'DOMAIN_PATH': os.path.join(ABS_HOME_PATH, 'Domain'), # path of local lib directory
				'NB_OPENED_FILE': 5, # number of recent files
				'NB_HISTORY_UNDO': 5, # number of undo
				'OUT_DIR': 'out', # name of local output directory (composed by all .dat, .txt files)
				'PLUGINS_PATH': os.path.join(ABS_HOME_PATH, 'plugins'), # path of plug-ins directory
				'FONT_SIZE': 12, # Block font size
				'LOCAL_EDITOR': True, # for the use of local editor
				'LOG_FILE': os.devnull, # log file (null by default)
				'DEFAULT_SIM_STRATEGY': 'bag-based', #choose the default simulation strategy for PyDEVS
				'PYDEVS_SIM_STRATEGY_DICT' : {'original':'SimStrategy1', 'bag-based':'SimStrategy2', 'direct-coupling':'SimStrategy3'}, # list of available simulation strategy for PyDEVS package
                'PYPDEVS_SIM_STRATEGY_DICT' : {'classic':'SimStrategy4', 'distributed':'SimStrategy5', 'parallel':'SimStrategy6'}, # list of available simulation strategy for PyPDEVS package
				'HELP_PATH' : os.path.join('doc', 'html'), # path of help directory
				'NTL' : False, # No Time Limit for the simulation
				'DYNAMIC_STRUCTURE' : False, # Dynamic Structure for local PyPDEVS simulation
				'REAL_TIME': False, ### PyPDEVS threaded real time simulation
				'VERBOSE':False,
				'TRANSPARENCY' : True, # Transparancy for DetachedFrame
				'DEFAULT_PLOT_DYN_FREQ' : 100, # frequence of dynamic plot of QuickScope (to avoid overhead),
				'DEFAULT_DEVS_DIRNAME':'PyDEVS', # default DEVS Kernel directory
				'DEVS_DIR_PATH_DICT':{'PyDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyDEVS'),
									'PyPDEVS_221':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs221' ,'src'),
									'PyPDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','old')},
				'GUI_FLAG':False
				}

# Sets the homepath variable to the directory where your application is located (sys.argv[0]).
builtins.__dict__.update(builtin_dict)

import inspect
import Components
import textwrap

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

                source_list = list(map(inspect.getsource, L))

                L_args = []

                for text in source_list:
                    ### textwrap for deleting the indentation

                    ast = codepaths.ast.parse(textwrap.dedent(text).strip())
                    visitor = codepaths.PathGraphingAstVisitor()
                    visitor.preorder(ast, visitor)

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
