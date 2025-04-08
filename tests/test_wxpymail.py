"""Test script for wxPyMail functionality.

Usage:
    python test_wxpymail.py --autoclose
    python test_wxpymail.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from wxPyMail import SendMailWx

# Run the test
app = TestApp(0)
frame = SendMailWx(None, title="Test")
app.RunTest(frame)
