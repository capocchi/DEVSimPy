"""Test script for AIPrompterDialog functionality.

Usage:
    python test_aiprompterdialog.py --autoclose
    python test_aiprompterdialog.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path ot avoid this import
from AIPrompterDialog import AIPrompterDialog

# Crée un objet d'adaptateur fictif (à remplacer par votre propre logique)
class DummyAdapter:
    def modify_model_part_prompt(self, code, prompt):
        return f"{code}\n# Prompt: {prompt}"

    def generate_output(self, full_prompt):
        return f"# Modified Code based on prompt:\n{full_prompt}"

# Code de démonstration
demo_code = ""

# Run the test
app = TestApp(0)
frame = AIPrompterDialog(None, 'Test', demo_code, DummyAdapter())
app.RunTest(frame)
