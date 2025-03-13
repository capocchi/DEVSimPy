### lauch the test 
### python test_preferencegui.py --autoclose
### python test_preferencegui.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from PreferencesGUI import PreferencesGUI

app = TestApp(0)
frame = PreferencesGUI(None, "Test")
app.RunTest(frame)