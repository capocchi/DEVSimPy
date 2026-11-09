"""Test script for WizardGUI functionality.

Usage:
    python test_wizardgui.py --autoclose
    python test_wizardgui.py --autoclose 10  # Auto-close after 10s delay
"""

import os  
import builtins

from ApplicationController import TestApp
from config import UpdateBuiltins # pyright: ignore[reportMissingImports]
from WizardGUI import ModelGeneratorWizard, atomicCode, coupledCode # type: ignore

UpdateBuiltins()


def _check_generated_templates():
	"""The generated python templates must be syntactically valid.

	Otherwise the wizard creates an archive whose python module cannot be
	imported, so the visual model is never saved and ``DEVSimPyModel.dat``
	keeps the "Call SaveFile method first!" placeholder.
	"""
	original_kernel = getattr(builtins, "DEFAULT_DEVS_DIRNAME", "PyDEVS")
	try:
		for kernel in ("PyDEVS", "PyPDEVS_221", "PyPDEVS_241", "BrokerDEVS"):
			builtins.DEFAULT_DEVS_DIRNAME = kernel
			compile(atomicCode("TestModel"), "<atomic-model>", "exec")
			compile(coupledCode("TestModel"), "<coupled-model>", "exec")
	finally:
		builtins.DEFAULT_DEVS_DIRNAME = original_kernel


_check_generated_templates()

DEVSIMPY_ICON = getattr(builtins, "DEVSIMPY_ICON", "iconDEVSimPy.ico")
ICON_PATH = getattr(builtins, "ICON_PATH", os.path.join(os.path.dirname(__file__), "..", "devsimpy", "icons"))

app = TestApp(0)
frame = ModelGeneratorWizard(
    parent=None,
    title='Test',
    img_filename=os.path.join(ICON_PATH, DEVSIMPY_ICON)
)
app.RunTest(frame)
