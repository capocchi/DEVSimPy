"""Test script for StandaloneGUI functionality.

Usage:
    python test_standalonegui.py --autoclose
    python test_standalonegui.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
from StandaloneGUI import StandaloneGUI

# Run the test
app = TestApp(0)
frame = StandaloneGUI(None, -1, 'Test')
app.RunTest(frame)