### lauch the test 
### python PriorityGUI.py --autoclose
### python PriorityGUI.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from PriorityGUI import PriorityGUI

### Run the test
app = TestApp(0)
frame = PriorityGUI(None, -1, "Test", ['Model1', 'Model2'])
app.RunTest(frame)