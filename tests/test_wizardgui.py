### lauch the test 
### python test_wizardgui.py --autoclose
### python test_wizardgui.py --autoclose 10 (sleep time before to close the frame is 10s)

import os

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from WizardGUI import ModelGeneratorWizard

### Run the test
app = TestApp(0)
frame = ModelGeneratorWizard(parent=None, title='Test', img_filename = os.path.join('bitmaps', DEVSIMPY_ICON))
# frame.run()
app.RunTest(frame)

