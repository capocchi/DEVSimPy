
### lauch the test 
### python test_importlibrary.py --autoclose
### python test_importlibrary.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from ImportLibrary import ImportLibrary

### Run the test
app = TestApp(0)
frame = ImportLibrary(None, size=(600,600), id=-1, title="Test")
app.RunTest(frame)