### lauch the test 
### python test_htmlwindow.py --autoclose
### python test_htmlwindow.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from HtmlWindow import HtmlFrame

### Run the test
app = TestApp(0)
frame = HtmlFrame(None, -1, "Alone Mode", size=(800,600))
app.RunTest(frame)

