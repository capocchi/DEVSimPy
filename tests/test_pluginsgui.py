"""Test script for PluginsGUI functionality.

Usage:
    python test_pluginsgui.py --autoclose
    python test_pluginsgui.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from PluginsGUI import ModelPluginsManager

# Run the test
app = TestApp(0)
frame = ModelPluginsManager(parent=None, title="Test", size=(500,400), model=None)
app.RunTest(frame)
