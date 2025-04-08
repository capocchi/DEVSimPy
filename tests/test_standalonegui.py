"""Test script for StandaloneGUI functionality.

Usage:
    python test_standalonegui.py --autoclose
    python test_standalonegui.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from StandaloneGUI import StandaloneGUI

# Run the test
app = TestApp(0)
frame = StandaloneGUI(None, -1, 'Test')
app.RunTest(frame)
