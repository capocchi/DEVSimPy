#! /usr/bin/env python
# -*- coding: utf8 -*-

# Specific import ---------------------------------------------------------------------------------
import os

# Important PATH ----------------------------------------------------------------------------------
CONTAINER_PATH = os.path.join(DOMAIN_PATH, 'TestAutom', 'Container')
SRC_PATH = os.path.join(CONTAINER_PATH, 'src')
BIN_PATH = os.path.join(SRC_PATH, 'bin')


# Plugin source code ------------------------------------------------------------------------------
def OnLeftDClick(self, event):

    model = self.getDEVSModel()

    os.system('java -jar ' + os.path.join(BIN_PATH, "sikuli-script.jar ") + model.sikuli)
