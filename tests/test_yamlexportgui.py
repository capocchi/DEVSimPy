
"""Test script for YAMLExportGUI.

Usage:
    python test_yamlexportgui.py --autoclose
    python test_yamlexportgui.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# Import after ApplicationController that inits sys.path to avoid import issues
from YAMLExportGUI import YAMLExportGUI

# Run the test
app = TestApp(0)
frame = YAMLExportGUI(None, -1, 'Test', path=r'test.yaml')
app.RunTest(frame)
