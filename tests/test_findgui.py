"""Test script for FindGUI functionality.

Usage:
    python test_findgui.py --autoclose
    python test_findgui.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
from FindGUI import FindReplace

# Run the test
app = TestApp(0)
frame = FindReplace(None, -1, 'Test')
app.RunTest(frame)