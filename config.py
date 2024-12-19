import os

# Définissez la variable `ABS_HOME_PATH` si elle n'est pas déjà définie.
# Par exemple, si ABS_HOME_PATH est le répertoire actuel, vous pouvez définir :
ABS_HOME_PATH = os.path.abspath(os.path.dirname(__file__))

# specific built-in variables. (don't modify the default value. If you want to change it, go to the PreferencesGUI from devsimpy interface.)
builtin_dict = {
    'SPLASH_PNG': os.path.join(ABS_HOME_PATH, 'splash', 'splash.png'),
    'DEVSIMPY_ICON': 'iconDEVSimPy.ico',
    'HOME_PATH': ABS_HOME_PATH,
    'ICON_PATH': 'icons',
    'SIMULATION_SUCCESS_SOUND_PATH': os.path.join('sounds', 'Simulation-Success.wav'),
    'SIMULATION_ERROR_SOUND_PATH': os.path.join('sounds', 'Simulation-Error.wav'),
    'DOMAIN_PATH': os.path.join(ABS_HOME_PATH, 'Domain'),
    'NB_OPENED_FILE': 5,
    'NB_HISTORY_UNDO': 5,
    'OUT_DIR': 'out',
    'SELECTED_IA' : "",
				'PARAMS_IA' : {
					'CHATGPT_API_KEY' : '',
					'OLLAMA_PORT' : "11434",
					'OLLAMA_MODEL' : "mistral",
				},
    'PLUGINS_PATH': os.path.join(ABS_HOME_PATH, 'plugins'),
    'FONT_SIZE': 12,
    'LOCAL_EDITOR': True,
    'EXTERNAL_EDITOR_NAME': "",
    'LOG_FILE': os.devnull,
    'DEFAULT_SIM_STRATEGY': 'bag-based',
    'PYDEVS_SIM_STRATEGY_DICT' : {'original':'SimStrategy1', 'bag-based':'SimStrategy2', 'direct-coupling':'SimStrategy3'},
    'PYPDEVS_SIM_STRATEGY_DICT' : {'classic':'SimStrategy4', 'parallel':'SimStrategy5'},
    'PYPDEVS_221_SIM_STRATEGY_DICT' : {'classic':'SimStrategy4', 'parallel':'SimStrategy5'},
    'HELP_PATH' : os.path.join('doc', 'html'),
    'NTL' : False,
    'DYNAMIC_STRUCTURE' : False,
    'REAL_TIME': False,
    'VERBOSE': False,
    'TRANSPARENCY' : True,
    'NOTIFICATION': True,
    'DEFAULT_PLOT_DYN_FREQ' : 100,
    'DEFAULT_DEVS_DIRNAME':'PyDEVS',
    'DEVS_DIR_PATH_DICT':{
        'PyDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyDEVS'),
        'PyPDEVS_221':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs221' ,'src'),
        'PyPDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','old')
    },
    'GUI_FLAG':True
}
