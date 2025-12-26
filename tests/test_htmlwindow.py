"""Test script for HtmlWindow functionality.

Usage:
    python test_htmlwinddw.py --autoclose
    python test_htmlwindow.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from HtmlWindow import HtmlFrame

# Run the test
app = TestApp(0)
frame = HtmlFrame(None, "Test", size=(800,600))
frame.SetPage("<h3>HTML OK</h3>")
app.RunTest(frame)
