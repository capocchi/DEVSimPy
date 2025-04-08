"""Test script for FTPGUI functionality.

Usage:
    python test_ftpgui.py --autoclose
    python test_ftpgui.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from FTPGUI import FTPFrame

# Run the test
app = TestApp(0)
frame = FTPFrame(None, -1, 'Test')
app.RunTest(frame)
