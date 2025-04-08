"""Test script for PriorityGUI functionality.

Usage:
    python test_prioritygui.py --autoclose
    python test_prioritygui.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
from PriorityGUI import PriorityGUI

# Run the test
app = TestApp(0)
frame = PriorityGUI(None, -1, "Test", ['Model1', 'Model2'])
app.RunTest(frame)