### lauch the test 
### python FTPGUI.py --autoclose
### python FTPGUI.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from FTPGUI import FTPFrame

### Run the test
app = TestApp(0)
frame = FTPFrame(None, -1, 'Test')
app.RunTest(frame)
