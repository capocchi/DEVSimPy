"""Test script for PriorityGUI functionality.

Usage:
    python test_prioritygui.py --autoclose
    python test_prioritygui.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from PriorityGUI import PriorityGUI

# Run the test
app = TestApp(0)
frame = PriorityGUI(None, -1, "Test", ['Model1', 'Model2'])
app.RunTest(frame)
