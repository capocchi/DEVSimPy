#! /usr/bin/env python
# -*- coding: utf8 -*-
#--------------------------------------------------------------------------------------------------
"""
---------------------------------------------------------------------------------------------------
 Name:        <plugins.py>

 Authors:      <Timothee Ville>

 Date:     <2012-28-02>
---------------------------------------------------------------------------------------------------
"""

# Specific import ---------------------------------------------------------------------------------
import os
import platform

# Important PATH ----------------------------------------------------------------------------------
CONTAINER_PATH = os.path.join(DOMAIN_PATH, 'TestAutom', 'Container')
SRC_PATH = os.path.join(CONTAINER_PATH, 'src')
BIN_PATH = os.path.join(SRC_PATH, 'bin')
LOG_PATH = os.path.join(SRC_PATH, 'logs')

# Plugin source code ------------------------------------------------------------------------------

# Search OS
opsys = str(platform.uname()[:1]).split('\'')[1].strip()
isWindows = None


# Override OnLeftDClick method
def OnLeftDClick(self, event):

    # Get atomic model who launch this plugin
    model = self.getDEVSModel()
    if opsys == 'Windows':
        isWindows = True

    # Test if RobotFramework model is coupled with Sikuli script
    if not model.isSikuli:
        # Launch selenium server
        os.system('java -jar ' + os.path.join(BIN_PATH, 'selenium_server_standalone.jar') + ' -log ' + os.path.join(LOG_PATH, 'selenium_log.log') + ' >/dev/null 2>/dev/null &')
        # Get pid of selenium-server process
        os.system('sel_pid=$!')
        # Launch robotframework process on selenium-server
        os.system('java -jar ' + os.path.join(BIN_PATH, 'robotframework.jar') + ' --outputdir=' + LOG_PATH + ' ' + model.testfile)
        # Kill selenium-server process
        os.system('kill $sel_pid')
    else:
        if isWindows:
            path_sep = ";"
            sikuli_home = "%SIKULI_HOME%"
        else:
            path_sep = ":"
            sikuli_home = "$SIKULI_HOME"
        command = 'java -cp \"' + os.path.join(BIN_PATH, 'robotframework.jar') + path_sep + os.path.join(sikuli_home, 'sikuli-script.jar') + '\" -Dpython.path=\"' + os.path.join(sikuli_home, 'sikuli-script.jar', 'Lib') + '\" org.robotframework.RobotFramework --pythonpath=' + model.sikuliScript + '  --outputdir=' + LOG_PATH + ' --loglevel=TRACE ' + model.testfile
        os.system(command)

    # Ouverture du rapport d'erreurs
    if opsys == 'Darwin':
        os.system('open ' + os.path.join(LOG_PATH, 'log.html'))
    elif opsys == 'Linux':
        os.system('gnome-open ' + os.path.join(LOG_PATH, 'log.html'))
    elif isWindows:
        os.system('start ' + os.path.join(LOG_PATH, 'log.html'))
