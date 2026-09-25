"""Test script for WizardGUI functionality.

Usage:
    python test_wizardgui.py --autoclose
    python test_wizardgui.py --autoclose 10  # Auto-close after 10s delay
"""

import os
import builtins

from config import UpdateBuiltins
from ApplicationController import TestApp
from WizardGUI import ModelGeneratorWizard

UpdateBuiltins()

DEVSIMPY_ICON = getattr(builtins, "DEVSIMPY_ICON", "iconDEVSimPy.ico")
ICON_PATH = getattr(builtins, "ICON_PATH", os.path.join(os.path.dirname(__file__), "..", "devsimpy", "icons"))

app = TestApp(0)
frame = ModelGeneratorWizard(
    parent=None,
    title='Test',
    img_filename=os.path.join(ICON_PATH, DEVSIMPY_ICON)
)
app.RunTest(frame)
