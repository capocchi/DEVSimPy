"""Test script for StandaloneGUI functionality.

Usage:
    python test_standalonegui.py --autoclose
    python test_standalonegui.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from StandaloneGUIKafkaPKG import StandaloneGUIKafkaPKG

# Run the test
app = TestApp(0)
frame = StandaloneGUIKafkaPKG(None, -1, 'Standalone Settings', block_model=None)
app.RunTest(frame)
