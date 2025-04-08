"""Test script for Editor functionality.

Usage:
    python test_editor.py --autoclose
    python test_editor.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from tempfile import gettempdir
import os

from ApplicationController import TestApp

from Editor import GetEditor

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
app2.RunTest(frame2)

# frame3 = GetEditor(None, -1, 'Test3', None, file_type='block')
# frame3.AddEditPage("Hello world", fn)
# frame3.SetPosition((300, 300))
# frame3.Show()