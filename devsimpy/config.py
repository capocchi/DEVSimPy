import os, sys
import builtins

##########################################################
### PATHS defined from the current dir used to execute devsimpy 
##########################################################
ABS_HOME_PATH = os.path.abspath(os.path.dirname(__file__))
DEVS_SIM_KERNEL_PATH = os.path.join(ABS_HOME_PATH, 'DEVSKernel')

builtins.ABS_HOME_PATH = ABS_HOME_PATH
builtins.DEVS_SIM_KERNEL_PATH = DEVS_SIM_KERNEL_PATH

##########################################################
### GLOBAL_SETTINGS for handle the paths of the DEVSimPy package
##########################################################

GLOBAL_SETTINGS = {
    'SPLASH_PNG': os.path.join(ABS_HOME_PATH, 'splash', 'splash.png'),
    'DEVSIMPY_PACKAGE_PATH': os.path.join(ABS_HOME_PATH),
    'ICON_PATH': os.path.join(ABS_HOME_PATH, 'icons'),
    'DEVS_DIR_PATH_DICT': {
        'PyDEVS': os.path.join(DEVS_SIM_KERNEL_PATH, 'PyDEVS'),
        'PyPDEVS_221': os.path.join(DEVS_SIM_KERNEL_PATH, 'PyPDEVS', 'pypdevs221' , 'src'),
        'PyPDEVS': os.path.join(DEVS_SIM_KERNEL_PATH, 'PyPDEVS', 'old')
    },
    'HELP_PATH': os.path.join('doc', 'html'),
    'DEVSIMPY_ICON': 'iconDEVSimPy.ico',
    'DEFAULT_SIM_STRATEGY': 'bag-based',
    'PYDEVS_SIM_STRATEGY_DICT': {'original': 'SimStrategy1', 'bag-based': 'SimStrategy2', 'direct-coupling': 'SimStrategy3'},
    'PYPDEVS_SIM_STRATEGY_DICT': {'classic': 'SimStrategy4', 'parallel': 'SimStrategy5'},
    'PYPDEVS_221_SIM_STRATEGY_DICT': {'classic': 'SimStrategy4', 'parallel': 'SimStrategy5'},
    'DEFAULT_DEVS_DIRNAME': 'PyDEVS',
    'GUI_FLAG': True
}

##########################################################
### USER_SETTINGS for handle the user preferences
##########################################################

# specific built-in variables. (don't modify the default value. If you want to change it, go to the PreferencesGUI from devsimpy interface.)
USER_SETTINGS = {
    'SIMULATION_SUCCESS_SOUND_PATH': os.path.join('sounds', 'Simulation-Success.wav'),
    'SIMULATION_ERROR_SOUND_PATH': os.path.join('sounds', 'Simulation-Error.wav'),
    'DOMAIN_PATH': os.path.join(GLOBAL_SETTINGS['DEVSIMPY_PACKAGE_PATH'], 'Domain'),
    'PLUGINS_PATH': os.path.join(GLOBAL_SETTINGS['DEVSIMPY_PACKAGE_PATH'], 'plugins'),
    'NB_OPENED_FILE': 5,
    'NB_HISTORY_UNDO': 5,
    'OUT_DIR': 'out',
    'SELECTED_IA': "",
				'PARAMS_IA': {
					'CHATGPT_API_KEY': '',
					'OLLAMA_PORT': "11434",
					'OLLAMA_MODEL': "mistral"
				},
    
    'FONT_SIZE': 12,
    'LOCAL_EDITOR': True,
    'EXTERNAL_EDITOR_NAME': "",
    'LOG_FILE': os.devnull,
    'NTL': False,
    'DYNAMIC_STRUCTURE': False,
    'REAL_TIME': False,
    'VERBOSE': False,
    'TRANSPARENCY': True,
    'NOTIFICATION': True,
    'DEFAULT_PLOT_DYN_FREQ': 100
}

### Check if the pypdevs241 directory is empty (not --recursive option when the devsimpy git has been cloned)
path = os.path.join(DEVS_SIM_KERNEL_PATH, 'PyPDEVS', 'pypdevs241')
if os.path.exists(path) and not len(os.listdir(path)) == 0:
	GLOBAL_SETTINGS['PYPDEVS_241_SIM_STRATEGY_DICT'] = {'classic': 'SimStrategy4', 'parallel': 'SimStrategy5'}
	GLOBAL_SETTINGS['DEVS_DIR_PATH_DICT'].update({'PyPDEVS_241': os.path.join(path, 'src', 'pypdevs')})
else:
	sys.stdout.write("PyPDEVS Kernel in version 2.4.1 is not loaded.\nPlease install it in the directory %s using git (https://github.com/kdheepak/pypdevs.git)\n"%path)

### All SETTINGS
ALL_SETTINGS = GLOBAL_SETTINGS | USER_SETTINGS

###########################################
### Define functions
###########################################

def UpdateBuiltins(new_settings=ALL_SETTINGS):
    # Met à jour les variables globales de `builtins`
    for key, value in new_settings.items():
        setattr(builtins, key, value)
