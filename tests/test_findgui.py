### lauch the test 
### python test_findgui.py --autoclose
### python test_findgui.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from FindGUI import FindReplace

### Run the test
app = TestApp(0)
frame = FindReplace(None, -1, 'Test')
app.RunTest(frame)
