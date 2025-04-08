"""Test script for PreferencesGUI functionality.

Usage:
    python test_preferencesgui.py --autoclose
    python test_preferencesgui.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from PreferencesGUI import PreferencesGUI

app = TestApp(0)
frame = PreferencesGUI(None, "Test")
app.RunTest(frame)
