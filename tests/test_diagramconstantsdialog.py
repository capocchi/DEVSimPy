
"""Test script for DiagramConstantsDialog functionality.

Usage:
    python test_diagramconstantsdialog.py --autoclose
    python test_diagramconstantsdialog.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
from DiagramConstantsDialog import DiagramConstantsDialog

# Run the test
app = TestApp(0)
diag = DiagramConstantsDialog(None, -1, "Test")
app.RunTest(diag)