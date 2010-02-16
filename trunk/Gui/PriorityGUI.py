# -*- coding: utf-8 -*-

import wx
import DragList
from sys import maxint

class PriorityGUI(wx.Frame):

	def __init__(self, parent, id, title, priorityDico):
		wx.Frame.__init__(self, parent, id, title, style=wx.FRAME_NO_WINDOW_MENU|wx.DEFAULT_FRAME_STYLE|wx.CLOSE_BOX, size=(210, 300))

		self.listCtrl = DragList.DragList(self, style=wx.LC_LIST, size=(210,240))
		
		# append to list
		for item in priorityDico:
			self.listCtrl.InsertStringItem(maxint,item)

		self.Center()

if __name__ == '__main__':
	
	class MyApp(wx.App):
		def OnInit(self):
			D = {"Atomic 1":None,"Atomic 2":None,"Atomic 3":None,"Coupled 1":None,"Coupled 11":None,"Coupled 12":None,"Coupled 41":None,"Coupled 31":None,"Coupled 11":None,"Coupled 14":None}
			dlg = PriorityGUI(None, -1, title='Priority', priorityDico=D)
			dlg.Show()
			return True

	app = MyApp(redirect=False)
	app.MainLoop()