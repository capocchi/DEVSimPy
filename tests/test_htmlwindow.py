"""Test script for HtmlWindow functionality.

Usage:
    python test_htmlwinddw.py --autoclose
    python test_htmlwindow.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
from HtmlWindow import HtmlFrame

# Run the test
app = TestApp(0)
frame = HtmlFrame(None, -1, "Test", size=(800,600))
app.RunTest(frame)