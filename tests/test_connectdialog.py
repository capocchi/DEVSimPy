### lauch the test 
### python test_connectdialog.py --autoclose
### python test_connectdialog.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from ConnectDialog import ConnectDialog 

### Run the test
app = TestApp(0)
frame = ConnectDialog(None, -1, 'Connect Manager')
app.RunTest(frame)
