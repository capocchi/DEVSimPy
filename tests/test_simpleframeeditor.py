"""Test script for SimpleFrameEditor functionality.

Usage:
    python test_simpleframeeditor.py --autoclose
    python test_simpleframeeditor.py --autoclose 10  # Auto-close after 10s delay
"""


from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from SimpleFrameEditor import FrameEditor

# Run the test
app = TestApp(0)
frame = FrameEditor(None, -1, "Test")
frame.AddText("Hello word!")
app.RunTest(frame)
