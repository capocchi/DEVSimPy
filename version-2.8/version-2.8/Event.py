# -*- coding: utf-8 -*-

import wx

class LockEvent(wx.PyCommandEvent):
	""" Lock Event
	"""
	def __init__(self, evtType, id):
		wx.PyCommandEvent.__init__(self, evtType, id)
		### position of the pop up menu
		self.pos = None

	def SetPosition(self, val):
		self.pos = val

	def GetPosition(self):
		return self.pos

class UnLockEvent(LockEvent):
	""" UnLock Event
	"""
	def __init__(self, evtType, id):
		LockEvent.__init__(self, evtType, id)