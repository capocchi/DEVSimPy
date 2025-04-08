"""Test script for XMLModule functionality.

Usage:
    python test_xmlmodule.py --autoclose
    python test_xmlmodule.py --autoclose 10  # Auto-close after 10s delay
"""

import wx
import os

from ApplicationController import TestApp

from XMLModule import getDiagramFromXMLSES
import Container
import DetachedFrame


# Run the test
app = TestApp(0)

diagram = Container.Diagram()

frame = DetachedFrame.DetachedFrame(None, -1, "Test", diagram)
newPage = Container.ShapeCanvas(frame, wx.NewIdRef(), name='Test')
newPage.SetDiagram(diagram)

path = os.path.join(os.path.expanduser("~"), 'Downloads', 'Watershed.xml')
# path = os.path.join(os.path.expanduser("~"),'Downloads','example.xmlsestree')
getDiagramFromXMLSES(path, canvas=newPage)
# diagram.SetParent(newPage)

app.RunTest(frame)
