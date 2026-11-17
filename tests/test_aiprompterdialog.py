"""Test script for AIPrompterDialog functionality.

Usage:
    python test_aiprompterdialog.py --autoclose
    python test_aiprompterdialog.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp  

# import after ApplicationController that inits sys.path ot avoid this import
from AIPrompterDialog import AIPrompterDialog # type: ignore

# Crée un objet d'adaptateur fictif (à remplacer par votre propre logique)
class DummyAdapter:
    def __init__(self):
        self.received_prompt = None

    def modify_model_part_prompt(self, code, prompt):
        return f"{code}\n# Prompt: {prompt}"

    def generate_output(self, full_prompt, on_token=None, stop_event=None):
        response = f"# Modified Code based on prompt:\n{full_prompt}"
        if on_token is not None and not (stop_event and stop_event.is_set()):
            on_token(response)
        return response

    def generate_model_json(self, prompt, on_token=None, stop_event=None):
        self.received_prompt = prompt
        return {"specifications": {"model_name": "Test"}}

    def generate_model_code(self, model_json=None, on_token=None, stop_event=None):
        return "# generated model code"

# Code de démonstration
demo_code = ""

# Run the test
app = TestApp(0)
frame = AIPrompterDialog(None, 'Test', demo_code, DummyAdapter())

# File attachment UI
assert hasattr(frame, "attach_button")
assert frame.attach_button.IsEnabled()
assert frame.attachments_summary.GetLabel() == "No file attached."

import os
import tempfile
import shutil

handle, attachment_path = tempfile.mkstemp(suffix=".txt")
os.close(handle)

with open(attachment_path, "w", encoding="utf-8") as attachment_file:
    attachment_file.write("Attached model specification")

frame._add_attachments([attachment_path])
assert len(frame.attachments) == 1
assert "1 file(s)" in frame.attachments_summary.GetLabel()
assert frame.attachments_list.IsShown()
assert frame.clear_attachments_button.IsEnabled()

# The attached text is added to the prompt sent to the model
frame._generate_in_background("describe the model", "")
assert "Attached model specification" in frame.adapter.received_prompt
assert "--- Begin attached file:" in frame.adapter.received_prompt

frame.on_clear_attachments(None)
assert not frame.attachments
assert frame.attachments_list.IsEmpty()

os.unlink(attachment_path)

# ----------------------------------------------------------------------
# Coupled-model AI session: restore from the .cmd archive and persist it
# ----------------------------------------------------------------------
import json
import zipfile

import AICoupledSession

coupled_dir = tempfile.mkdtemp()
coupled_archive = os.path.join(coupled_dir, "Coupled.cmd")

with zipfile.ZipFile(coupled_archive, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("DEVSimPyModel.dat", b"payload")
    zf.writestr("Coupled.py", "class Coupled: pass\n")

coupled_structure = {
    "name": "Coupled",
    "inputs": 1,
    "outputs": 1,
    "submodels": [],
    "connections": [],
}

coupled_session = {
    "session_id": "20260101_000000_abcdef12",
    "model_name": "Coupled",
    "provider": "Ollama",
    "ai_model": "mistral",
    "messages": [
        {"role": "user", "content": "build a generator"},
        {"role": "assistant", "content": '{"name": "Coupled", "submodels": []}'},
    ],
    "structure": coupled_structure,
    "structure_only": True,
}

coupled_frame = AIPrompterDialog(
    None,
    "Coupled",
    "",
    DummyAdapter(),
    model_kind="coupled",
    model_name="Coupled",
    inputs=1,
    outputs=1,
    archive_path=coupled_archive,
    session=coupled_session,
)

# The conversation and the last structure are restored
assert len(coupled_frame.coupled_messages) == 2
assert "Session restored (2 message(s))" in coupled_frame.trace_text.GetValue()
assert json.loads(coupled_frame.code_text.GetValue())["name"] == "Coupled"

# The dialog exposes the session payload to the wizard
import builtins

previous_provider = getattr(builtins, "SELECTED_IA", "")
builtins.SELECTED_IA = ""

try:
    payload = coupled_frame.session_payload()
finally:
    builtins.SELECTED_IA = previous_provider

assert payload["structure"]["name"] == "Coupled"
assert len(payload["messages"]) == 2
assert payload["provider"] == "Ollama"
assert payload["ai_model"] == "mistral"

# Structure-only mode: the checkbox is restored from the session and persisted
assert coupled_frame.structure_only_check is not None
assert coupled_frame.structure_only_check.GetValue() is True
assert payload["structure_only"] is True

coupled_frame.structure_only_check.SetValue(False)
assert coupled_frame.session_payload()["structure_only"] is False
coupled_frame.structure_only_check.SetValue(True)

# Behavior submodels without code become empty stubs in structure-only mode
structure_only_sample = {
    "name": "Coupled",
    "submodels": [
        {"label": "Gen", "generate": "existing", "model": "Generator"},
        {"label": "Queue", "generate": "behavior", "behavior": "FIFO queue"},
        {
            "label": "Sink",
            "generate": "behavior",
            "behavior": "sink",
            "code": "class Sink: pass\n",
        },
    ],
    "connections": [],
}

kept = coupled_frame._skip_coupled_submodel_code(structure_only_sample)

assert kept["submodels"][1]["generate"] == "stub"
assert kept["submodels"][2]["generate"] == "behavior"
assert kept["submodels"][2]["code"] == "class Sink: pass\n"

# ----------------------------------------------------------------------
# Graphical preview: the structure can be checked before it is applied
# ----------------------------------------------------------------------
assert coupled_frame.structure_notebook is not None
assert coupled_frame.structure_notebook.GetPageCount() == 2
assert coupled_frame.structure_notebook.GetPageText(0) == "JSON"
assert coupled_frame.structure_notebook.GetPageText(1) == "Graphical view"
assert coupled_frame.structure_preview is not None
assert coupled_frame.preview_refresh_button is not None

# The restored structure has no submodel: the preview reports it
assert coupled_frame.structure_preview.GetLayout() is None
assert "at least one submodel" in coupled_frame.structure_preview.GetMessage()

preview_structure = {
    "name": "Coupled",
    "inputs": 1,
    "outputs": 1,
    "submodels": [
        {"label": "Gen", "generate": "stub", "inputs": 0, "outputs": 1},
        {"label": "Sink", "generate": "stub", "inputs": 1, "outputs": 1},
    ],
    "connections": [
        {"source": "__input__", "source_port": 0, "target": "Sink", "target_port": 0},
        {"source": "Gen", "source_port": 0, "target": "Sink", "target_port": 0},
        {"source": "Sink", "source_port": 0, "target": "__output__", "target_port": 0},
    ],
}

coupled_frame.code_text.SetValue(json.dumps(preview_structure))
coupled_frame._refresh_structure_preview()

layout = coupled_frame.structure_preview.GetLayout()
assert layout is not None
assert [box["label"] for box in layout["boxes"]] == ["Gen", "Sink"]
assert len(layout["connections"]) == 3
assert "2 submodel(s), 3 connection(s)" in (
    coupled_frame.structure_preview_message.GetLabel()
)

# An invalid JSON is reported inside the preview instead of a diagram
coupled_frame.code_text.SetValue("{ not json")
coupled_frame._refresh_structure_preview()
assert coupled_frame.structure_preview.GetLayout() is None
assert "Preview unavailable" in coupled_frame.structure_preview.GetMessage()

# Restore the session structure for the persistence assertions below
coupled_frame.code_text.SetValue(json.dumps(coupled_structure))
coupled_frame._refresh_structure_preview()

# Storing updates the archive the dialog was opened from
assert coupled_frame._store_session() == coupled_session["session_id"]

loaded_session = AICoupledSession.load_session(coupled_archive)
assert loaded_session["session_id"] == coupled_session["session_id"]
assert loaded_session["structure"]["name"] == "Coupled"
assert len(loaded_session["messages"]) == 2

coupled_frame.Destroy()
shutil.rmtree(coupled_dir, ignore_errors=True)

app.RunTest(frame)
