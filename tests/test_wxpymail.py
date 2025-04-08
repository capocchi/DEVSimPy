"""Test script for wxPyMail functionality.

Usage:
    python test_wxpymail.py --autoclose
    python test_wxpymail.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
from wxPyMail import SendMailWx

# Run the test
app = TestApp(0)
frame = SendMailWx(None, title="Test")
app.RunTest(frame)