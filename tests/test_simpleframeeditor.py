### lauch the test 
### python test_simpleframeeditor.py --autoclose
### python test_simpleframeeditor.py --autoclose 10 (sleep time before to close the frame is 10s)

import wx

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from SimpleFrameEditor import FrameEditor

### Run the test
app = TestApp(0)
frame = FrameEditor(None, -1, "Test")
frame.AddText("Test \n Hello word!")
app.RunTest(frame)
