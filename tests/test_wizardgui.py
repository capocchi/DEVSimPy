### lauch the test 
### python WizardGUI.py --autoclose
### python WizardGUI.py --autoclose 10 (sleep time before to close the frame is 10s)

import os
import gettext

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from WizardGUI import ModelGeneratorWizard

_ = gettext.gettext

### Run the test
app = TestApp(0)
frame = ModelGeneratorWizard(parent=None, title=_('Test'), img_filename = os.path.join('bitmaps', DEVSIMPY_ICON))
# frame.run()
app.RunTest(frame)

