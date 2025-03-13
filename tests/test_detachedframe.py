	### lauch the test 
	### python test_detachedframe.py --autoclose
	### python test_detachedframe.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
import Container
from DetachedFrame import DetachedFrame

### Run the test
app = TestApp(0)
diagram = Container.Diagram()
frame = DetachedFrame(None, -1, "Test", diagram)
app.RunTest(frame)

