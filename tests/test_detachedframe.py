"""Test script for DetachedFrame functionality.

Usage:
    python test_detachedframe.py --autoclose
    python test_detachedframe.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
import Container
from DetachedFrame import DetachedFrame

# Run the test
app = TestApp(0)
diagram = Container.Diagram()
frame = DetachedFrame(None, -1, "Test", diagram)
app.RunTest(frame)