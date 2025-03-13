
### lauch the test 
### python test_diagramconstantsdialog.py --autoclose
### python test_diagramconstantsdialog.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from DiagramConstantsDialog import DiagramConstantsDialog

### Run the test
app = TestApp(0)
frame = DiagramConstantsDialog(None, -1, "Test")
app.RunTest(frame)
