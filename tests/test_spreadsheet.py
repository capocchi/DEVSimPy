### lauch the test 
### python test_spreadsheet.py --autoclose
### python test_spreadsheet.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from SpreadSheet import Newt
import Container

### Run the test
app = TestApp(0)
devs =  Container.DiskGUI().getDEVSModel()
frame = Newt(None, -1, 'Test', devs)
app.RunTest(frame)
