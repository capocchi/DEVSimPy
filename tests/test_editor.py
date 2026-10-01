"""Test script for Editor functionality.

Usage:
    python test_editor.py --autoclose
    python test_editor.py --autoclose 10  # Auto-close after 10s delay
"""

from tempfile import gettempdir  
import os
import builtins

from ApplicationController import TestApp

from Editor import GetEditor # type: ignore

# Run the test
fn = os.path.join(os.path.realpath(gettempdir()), 'test.py')
with open(fn, 'w') as f:
    f.write("Hello world !")

# app1 = TestApp(0)
# frame1 = GetEditor(None, -1, 'Test1')
# frame1.AddEditPage("Hello world", fn)
# frame1.SetPosition((100, 100))
# app1.RunTest(frame1)

app2 = TestApp(0)
frame2 = GetEditor(None, -1, 'Test', file_type='test')
frame2.AddEditPage("Hello world", fn)
frame2.AddEditPage("Hello world", fn)
frame2.SetPosition((200, 200))
frame2.ai_assistant_panel.mode_choice.SetSelection(1)
frame2.ai_assistant_panel._on_mode_changed(None)
assert builtins.PARAMS_IA["AI_EDITOR_MODE"] == 1
frame2.ai_assistant_panel.mode_choice.SetSelection(0)
frame2.ai_assistant_panel._on_mode_changed(None)
assert builtins.PARAMS_IA["AI_EDITOR_MODE"] == 0
frame2.ToggleAIAssistantPanel(None)
assert frame2.editor_splitter.IsSplit()
assert frame2.ai_assistant_item.IsChecked()
frame2.ToggleAIAssistantPanel(None)
assert not frame2.editor_splitter.IsSplit()
assert not frame2.ai_assistant_item.IsChecked()
app2.RunTest(frame2)

# frame3 = GetEditor(None, -1, 'Test3', None, file_type='block')
# frame3.AddEditPage("Hello world", fn)
# frame3.SetPosition((300, 300))
# frame3.Show()