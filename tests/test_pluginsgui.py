### Run the test 
### python test_pluginsgui.py --autoclose
### python test_pluginsgui.py --autoclose 10 (sleep time before to close the frame is 10s)

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from PluginsGUI import ModelPluginsManager

### Run the test
app = TestApp(0)
frame = ModelPluginsManager(parent=None, title="Test", model=None)
app.RunTest(frame)
