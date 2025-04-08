"""Test script for SpreadSheet functionality.

Usage:
    python test_spreadsheet.py --autoclose
    python test_spreadsheet.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from SpreadSheet import Newt
import Container

# Run the test
app = TestApp(0)
devs =  Container.DiskGUI().getDEVSModel()
frame = Newt(None, -1, 'Test', devs)
app.RunTest(frame)
