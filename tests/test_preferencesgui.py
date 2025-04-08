"""Test script for PreferencesGUI functionality.

Usage:
    python test_preferencesgui.py --autoclose
    python test_preferencesgui.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
from PreferencesGUI import PreferencesGUI

app = TestApp(0)
frame = PreferencesGUI(None, "Test")
app.RunTest(frame)