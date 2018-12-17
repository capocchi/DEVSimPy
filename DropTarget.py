# -*- coding: utf-8 -*-

"""
Name: Components.py
Brief descritpion: All classes for components
Author(s): L. Capocchi <capocchi@univ-corse.fr>
Version:  1.0
Last modified: 2012.12.16
GENERAL NOTES AND REMARKS:

> pyreverse -a1 -s1 -f ALL -o png DropTarget.py

GLOBAL VARIABLES AND FUNCTIONS:
"""

import wx
import os
import sys

import Components
import DetachedFrame
import Container

class DropTarget(wx.PyDropTarget if wx.VERSION_STRING < '4.0' else wx.DropTarget):
	""" DropTarget(canvas)
	"""
	SOURCE = None

	def __init__(self, canvas = None):
		""" Constructor
		"""
		
		if wx.VERSION_STRING < '4.0':
			wx.PyDropTarget.__init__(self)
		else:
			wx.DropTarget.__init__(self)
			
		##local copy
		self.canvas = canvas

		self.mainW = wx.GetApp().GetTopWindow()

		self.__setDo()

	def __setDo(self):
		"""
		"""
	
		# file and text names
		self.__fdo = wx.FileDataObject()
		self.__tdo = wx.TextDataObject()
		
		# allows several drop format
		self._do = wx.DataObjectComposite()
		self._do.Add(self.__tdo)
		self._do.Add(self.__fdo)
		
		self.SetDataObject(self._do)
	
	#def OnEnter(self, x, y, d):
		#sys.stdout.write("OnEnter: %d, %d, %d\n" % (x, y, d))
		#return wx.DragCopy

	def OnDragOver(self,x,y,d):
		"""
		"""
		### list of ContainerBlock shape in canvas
		L = filter(lambda s: isinstance(s, Container.ContainerBlock), self.canvas.diagram.GetShapeList())

		### for all ContainerBlock we make a rect and test if the point x,y is in this rect to instance the DetachedFrame
		for shape in L:
			w = shape.x[1]-shape.x[0]
			h = shape.y[1]-shape.y[0]
 
			rect = wx.Rect(shape.x[0], shape.y[0], w, h)

			### point (x,y) in rect
			if rect.ContainsXY(x,y) if wx.VERSION_STRING < '4.0' else rect.Contains(x,y):
			
			### rect1 and rect2 intersect
			#if abs (x - shape.x[0]) < w and abs (y - shape.y[0]) < h:
				#frame = self.mainW.FindWindowByName(shape.label)
			
				#if frame:
				if hasattr(self, 'timer'):
					if not self.timer.IsRunning():
				#	frame.Show(True)
						self.timer.Start()
				else:
					self.timer = self.OnDetachedFrame(shape)
			else:
				if hasattr(self, 'timer'):
					self.timer.Stop()
					del self.timer

		return wx.DragCopy

	def OnDetachedFrame(self, shape):
		"""
		"""
		### Detached Frame
		frame = DetachedFrame.DetachedFrame(self.canvas, wx.ID_ANY, shape.label, shape)
		
		### to disabled transparency
		frame.Unbind(wx.EVT_IDLE)
		frame.Unbind(wx.EVT_MOVE)

		frame.SetIcon(self.canvas.GetTopLevelParent().GetIcon())
		frame.SetFocus()
		timer = wx.CallLater(1200, frame.Show)
		
		return timer

	#def OnDragOver(self, x, y, d):
	#   sys.stdout.write("OnDragOver: %d, %d, %d\n" % (x, y, d))
	#   return wx.DragCopy

	#def OnLeave(self):
		#sys.stdout.write("OnLeave\n")

	#def OnDrop(self, x, y):
	#	sys.stdout.write("OnDrop: %d %d\n" % (x, y))	
	#	return True
        
	def OnData(self, x, y, d):
		"""
		"""
		
		if self.GetData():
			
			df = self._do.GetReceivedFormat().GetType()
			
			### list of blocks to create
			block_list = []
			
			### dropped object come from devsimpy (Library frame)
			if df in [wx.DF_UNICODETEXT, wx.DF_TEXT]:
				filename = self.__tdo.GetText()
				# text is the filename
				text = os.path.splitext(filename)[0]
				### label is composed by the number of block in diagram
				label = "%s_%s"%(os.path.basename(text),str(self.canvas.GetDiagram().GetBlockCount()))
				
				m = self.GetBlock(filename, label, x, y)
		
				### Append new block 
				block_list.append(m)
				
			### dropped object come from system (like explorer)
			elif df == wx.DF_FILENAME:
				for filename in self.__fdo.GetFilenames():
					# text is the filename 
					text, ext = os.path.splitext(filename)
					# label is the file name
					label = os.path.basename(text)
					
					if not ext in (".amd", '.cmd', '.py'):
						m = Components.DSPComponent.Load(filename, label, self.canvas)
					else:
						m = self.GetBlock(filename, label, x, y)
						
						### Append new block
						block_list.append(m)
			
			### if bitmap is dropped
			elif df == wx.DF_BITMAP:
				pass
			
			### add all block in the diagram and trace this operation
			for block in block_list:
				if block:
					# Adding graphical model to diagram
					self.canvas.AddShape(block)
					sys.stdout.write(_("Adding DEVSimPy model: \n").encode('utf-8', 'ignore').strip())
					sys.stdout.write(repr(block))
				else:
					sys.stdout.write(_("ERROR: DEVSimPy model not added.\n").encode('utf-8', 'ignore').strip())
			
			return d
			
	def GetBlock(self, filename, label, x, y):
		"""
		"""
		### Block factory
		bf = Components.BlockFactory()
		### Get block
		m = bf.GetBlock(filename, label)
		
		### Move and append block
		if m:
			### convert coordinate depending on the canvas
			x,y = self.canvas.GetXY(m, x, y)

			# move model from mouse position
			m.move(x, y)
			
		return m