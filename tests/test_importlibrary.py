"""Test script for ImportLibrary functionality.

Usage:
    python test_importlibrary.py --autoclose
    python test_importlibrary.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from ImportLibrary import ImportLibrary

# Run the test
app = TestApp(0)
frame = ImportLibrary(None, size=(600,600), id=-1, title="Test")
app.RunTest(frame)
