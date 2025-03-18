
### lauch the test 
### python test_yamlexportgui.py --autoclose
### python test_yamlexportgui.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from YAMLExportGUI import YAMLExportGUI

### Run the test
app = TestApp(0)
frame = YAMLExportGUI(None, -1, 'Test', path=r'test.yaml')
app.RunTest(frame)