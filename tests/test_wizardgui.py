"""Test script for WizardGUI functionality.

Usage:
    python test_wizardgui.py --autoclose
    python test_wizardgui.py --autoclose 10  # Auto-close after 10s delay
"""

import os

from ApplicationController import TestApp

# Import after ApplicationController that inits sys.path ot avoid this import
from WizardGUI import ModelGeneratorWizard

# Run the test
app = TestApp(0)
frame = ModelGeneratorWizard(parent=None, title='Test', img_filename = os.path.join('bitmaps', DEVSIMPY_ICON))
# frame.run()
app.RunTest(frame)
