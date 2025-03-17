### Run the test 
### python test_labelgui.py --autoclose
### python test_labelgui.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from LabelGUI import LabelDialog

### Run the test
app = TestApp(0)
frame = LabelDialog(None, None, title="Test")
app.RunTest(frame)