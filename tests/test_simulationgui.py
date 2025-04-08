
"""Test script for SimulationGUI functionality.

Usage:
    python test_simulationgui.py --autoclose
    python test_simulationgui.py --autoclose 10  # Sleep time before closing frame is 10s
"""

import wx

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
from SimulationGUI import SimulationDialog

# Run the test
app = TestApp(0)
frame = SimulationDialog(wx.Frame(None), wx.NewIdRef(), 'Test')
app.RunTest(frame)