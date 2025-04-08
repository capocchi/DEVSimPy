
"""Test script for DiagramConstantsDialog functionality.

Usage:
    python test_diagramconstantsdialog.py --autoclose
    python test_diagramconstantsdialog.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from DiagramConstantsDialog import DiagramConstantsDialog

# Run the test
app = TestApp(0)
diag = DiagramConstantsDialog(None, -1, "Test")
app.RunTest(diag)
