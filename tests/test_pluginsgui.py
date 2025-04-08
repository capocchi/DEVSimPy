"""Test script for PluginsGUI functionality.

Usage:
    python test_pluginsgui.py --autoclose
    python test_pluginsgui.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
from PluginsGUI import ModelPluginsManager

# Run the test
app = TestApp(0)
frame = ModelPluginsManager(parent=None, title="Test", model=None)
app.RunTest(frame)