"""Test script for ConnectDialog functionality.

Usage:
    python test_connectdialog.py --autoclose
    python test_connectdialog.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from ConnectDialog import ConnectDialog 

# Run the test
app = TestApp(0)
frame = ConnectDialog(None, -1, 'Test')
app.RunTest(frame)
