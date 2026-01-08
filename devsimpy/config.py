import os
import sys
import builtins
import logging
import ast
logging.getLogger("pydot").setLevel(logging.WARNING)


from Utilities import GetUserConfigDir

""" PATHS defined from the current dir used to execute devsimpy 
"""
ABS_HOME_PATH = os.path.abspath(os.path.dirname(__file__))
DEVS_SIM_KERNEL_PATH = os.path.join(ABS_HOME_PATH, 'DEVSKernel')

builtins.ABS_HOME_PATH = ABS_HOME_PATH
builtins.DEVS_SIM_KERNEL_PATH = DEVS_SIM_KERNEL_PATH

""" GLOBAL_SETTINGS for handle the paths of the DEVSimPy package
"""

GLOBAL_SETTINGS = {
    'SPLASH_PNG': os.path.join(ABS_HOME_PATH, 'splash', 'splash.png'),
    'DEVSIMPY_PACKAGE_PATH': os.path.join(ABS_HOME_PATH),
    'ICON_PATH': os.path.join(ABS_HOME_PATH, 'icons'),
    'DEVS_DIR_PATH_DICT': {
        'PyDEVS': os.path.join(DEVS_SIM_KERNEL_PATH, 'PyDEVS'),
        'PyPDEVS_221': os.path.join(DEVS_SIM_KERNEL_PATH, 'PyPDEVS', 'pypdevs221' , 'src'),
        'PyPDEVS': os.path.join(DEVS_SIM_KERNEL_PATH, 'PyPDEVS', 'old'),
        'BrokerDEVS': os.path.join(DEVS_SIM_KERNEL_PATH, 'BrokerDEVS')
    },
    'HELP_PATH': os.path.join('doc', 'html'),
    'DEVSIMPY_ICON': 'iconDEVSimPy.ico',
    'PYDEVS_SIM_STRATEGY_DICT': {'original': 'OriginalPyDEVSSimStrategy', 'bag-based': 'BagBasedPyDEVSSimStrategy', 'direct-coupling': 'DirectCouplingPyDEVSSimStrategy'},
    'PYPDEVS_SIM_STRATEGY_DICT': {'classic': 'ClassicPyPDEVSSimStrategy', 'parallel': 'ParallelPyPDEVSSimStrategy'},
    # BrokerDEVS: Nested structure separating Message Standardization from Broker Choice
    # Allows flexible combinations like: Kafka+DEVSStreaming, MQTT+DEVSStreaming, etc.
    'BROKERDEVS_SIM_STRATEGY_DICT': {
        'DEVSStreaming': {  # Message Standardization
            'Kafka': 'SimStrategyKafkaMS4Me',
            'MQTT': 'SimStrategyMqttMS4Me',
            'RabbitMQ': 'SimStrategyRabbitMQMS4Me',
        }
        # Future: Add more message standardizations here
        # 'CustomFormat': {
        #     'Kafka': 'SimStrategyKafkaCustom',
        #     'MQTT': 'SimStrategyMqttCustom',
        # }
    },
    'PYPDEVS_221_SIM_STRATEGY_DICT': {'classic': 'ClassicPyPDEVSSimStrategy', 'parallel': 'ParallelPyPDEVSSimStrategy'},
    'GUI_FLAG': True
}

""" USER_SETTINGS for handle the user preferences
"""
# Specific built-in variables. 
# (don't modify the default value. 
# If you want to change it, 
# go to the PreferencesGUI from devsimpy interface.)
USER_SETTINGS = {
    'DEFAULT_DEVS_DIRNAME': 'PyDEVS',
    'DEFAULT_SIM_STRATEGY': 'bag-based',
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
    'SELECTED_MESSAGE_FORMAT': 'DEVSStreaming',  # For BrokerDEVS
    'SELECTED_BROKER': 'Kafka',  # For BrokerDEVS
    
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

# Check if the pypdevs241 directory is empty 
# (not --recursive option when the devsimpy git has been cloned)
path = os.path.join(DEVS_SIM_KERNEL_PATH, 'PyPDEVS', 'pypdevs241')
if os.path.exists(path) and not len(os.listdir(path)) == 0:
	GLOBAL_SETTINGS['PYPDEVS_241_SIM_STRATEGY_DICT'] = {'classic': 'ClassicPyPDEVSSimStrategy', 'parallel': 'ParallelPyPDEVSSimStrategy'}
	GLOBAL_SETTINGS['DEVS_DIR_PATH_DICT'].update({'PyPDEVS_241': os.path.join(path, 'src', 'pypdevs')})
else:
	sys.stdout.write("PyPDEVS Kernel in version 2.4.1 is not loaded.\nPlease install it in the directory %s using git (https://github.com/kdheepak/pypdevs.git)\n"%path)

# All SETTINGS
ALL_SETTINGS = GLOBAL_SETTINGS | USER_SETTINGS

""" Define functions
"""

def read_dev_sim_py_config_file_without_wx(path):
    config = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            try:
                # essayer d'interpréter la valeur comme expression Python
                config[key] = ast.literal_eval(value)
            except Exception:
                # si ce n'est pas une expression Python (ex: version=5.1.1)
                config[key] = value
    return config

def UpdateBuiltins(new_settings=ALL_SETTINGS):
    """Update builtins with new settings.
	"""
    # Check if the new settings are valid
    if not isinstance(new_settings, dict):
        raise ValueError("new_settings must be a dictionary")

    for key, value in new_settings.items():
            setattr(builtins, key, value)

    ### update user settings from .devsimpy config file if existe
    # ### here because some imports (DomainBehavior, DomainStrucutre, etc) are needed early in the devsimpy.py file. 
    cfg_path = os.path.join(GetUserConfigDir(), ".devsimpy")
    
    if os.path.exists(cfg_path):
        try:
            import wx
            App = wx.App()
        except Exception as e:
            sys.stdout.write(f"wx package not installed {e}.\nUser Settings ignored.")
        else:
             cfg = wx.FileConfig(localFilename = cfg_path)
             builtins.__dict__.update(eval(cfg.Read("settings")))
    else:
         sys.stdout.write(f"Error trying to read the builtin dictionary from config file ({cfg_path}). So, we load the default builtin")
    