
### lauch the test 
### python test_wxpymail.py --autoclose
### python test_wxpymail.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from wxPyMail import SendMailWx

### Run the test
app = TestApp(0)
frame = SendMailWx(None, title="Test")
app.RunTest(frame)

