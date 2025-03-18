### lauch the test 
### python test_draglist.py --autoclose
### python test_draglist.py --autoclose 10 (sleep time before to close the frame is 10s)

from random import choice
import wx

from ApplicationController import TestApp

### import after ApplicationController that init sys.path ot avoid this import
from DragList import DragList 

items = ['Foo', 'Bar', 'Baz', 'Zif', 'Zaf', 'Zof']

### Run the test
app = TestApp(0)

frame = wx.Frame(None, title='Test')

dl1 = DragList(frame, style=wx.LC_LIST)
dl2 = DragList(frame, style=wx.LC_REPORT)
dl2.InsertColumn(0, "Column #0")
dl2.InsertColumn(1, "Column #1", wx.LIST_FORMAT_RIGHT)
dl2.InsertColumn(2, "Column #2")
sizer = wx.BoxSizer()
frame.SetSizer(sizer)
sizer.Add(dl1, proportion=1, flag=wx.EXPAND)
sizer.Add(dl2, proportion=1, flag=wx.EXPAND)


for item in items:
    dl1.InsertItem(dl1.GetItemCount(), item)
    idx = dl2.InsertItem(dl2.GetItemCount(), item)
    dl2.SetItem(idx, 1, choice(items))
    dl2.SetItem(idx, 2, choice(items))


app.RunTest(frame)
