# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ImportLibrary.py --- Importing library dialog
#                     --------------------------------
#                                Copyright (c) 2009
#                                 Laurent CAPOCCHI
#                               University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  15/04/09
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import os
import  wx.lib.filebrowsebutton as filebrowse
import wx.aui

#-------------------------------------------------------------------
class ImportLibrary(wx.Dialog):
        def __init__(self, *args, **kwargs):
                wx.Dialog.__init__(self, *args, **kwargs)
                
		self.SetSize(wx.Size(400,250))
                
		#local copy
                self.parent=args[0]
                
                #list des item selectionnes
                self.selectedItem={}
                
		try:
			# recuperation des lib a partir du dico D du tree (library)
			lst= filter(lambda s: not self.parent.tree.IsChildRoot(s), self.parent.tree.GetDomainList(self.parent.tree.domainPath))
			# recuperation des model qui ne sont pas dans le Domain (export)
			self.parent.exportPathsList = eval(self.parent.cfg.Read("exportPathsList"))
			self.d={}
			for path in self.parent.exportPathsList:
				name=os.path.basename(path)
				if not self.parent.tree.IsChildRoot(name):
					lst += [name]
					self.d[name]=os.path.abspath(path)
                except AttributeError:
			# test mode
			lst=["Library 1","Library 2", "Library 3", "Library 4", "Library 5"]
		
		font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
		#font.SetPointSize(8)

		panel = wx.Panel(self, wx.ID_ANY)
		vbox = wx.BoxSizer(wx.VERTICAL)

		wx.StaticBox(panel, wx.ID_ANY, _("Library"),(5,5), (380,150))
		#wx.Size(-1,8)
		self.cb = wx.CheckListBox(panel, wx.ID_ANY, (10, 30),(370,120), lst)
		wx.StaticLine(panel, wx.LI_HORIZONTAL,size=((-1,10)))
		self.cb.SetFont(font)

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		self.dbb = filebrowse.DirBrowseButton(self, wx.ID_ANY,startDirectory=os.getcwd(),labelText=_("New"),changeCallback=self.OnChange)
		self.btn_Add=wx.Button(self,id=wx.ID_ADD)
                self.btn_Add.Enable(False)
                hbox1.Add(self.dbb, 1 ,wx.EXPAND)
                hbox1.Add(self.btn_Add, 0 ,wx.RIGHT|wx.CENTER,3)
		
		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		btn_Cancel = wx.Button(self, wx.ID_CANCEL)
                btn_Ok = wx.Button(self, wx.ID_OK)
                hbox2.Add(btn_Cancel, 0, wx.LEFT, 2)
                hbox2.Add(wx.Size(-1,10), 1, wx.EXPAND)
                hbox2.Add(btn_Ok, 0, wx.RIGHT, 3)

		vbox.Add(panel)
		vbox.Add(hbox1, 1,wx.ALIGN_CENTER| wx.TOP|wx.BOTTOM|wx.EXPAND)
		vbox.Add(hbox2, 1, wx.ALIGN_CENTER|wx.TOP |wx.BOTTOM|wx.EXPAND,3)

		self.SetSizer(vbox)
                panel.SetAutoLayout(True)
                
                #Gestionnaire evenement
                self.Bind(wx.EVT_BUTTON, self.OnAdd, self.btn_Add)
                self.Bind(wx.EVT_LISTBOX, self.EvtListBox, self.cb)
                self.Bind(wx.EVT_CHECKLISTBOX, self.EvtCheckListBox, self.cb)
                
        def EvtListBox(self, evt):
                pass
                
        def EvtCheckListBox(self, evt):
                index = evt.GetSelection()
                label = self.cb.GetString(index)
                
                #met a jour le dico des elements semlectionnes
                if self.cb.IsChecked(index) and not self.selectedItem.has_key(label):
                        self.selectedItem.update({str(label):index})
                elif not self.cb.IsChecked(index) and self.selectedItem.has_key(label):
                        del self.selectedItem[str(label)]
                                
        def OnChange(self, evt):
                self.btn_Add.Enable(True)
        
        def OnAdd(self, evt):
                
                path=self.dbb.GetValue()
                dName=str(os.path.basename(path))
                
                # si la lib n'est pas deja importee
                if not self.parent.tree.IsChildRoot(dName):
                        if not self.d.has_key(dName) or (self.d.has_key(dName) and self.d[dName] != path): 
                
                                # ajout dans la liste box
                                self.cb.Insert(dName,self.cb.GetCount())
                                
                                # mise a jour du fichier .devsimpy
                                self.parent.exportPathsList = eval(self.parent.cfg.Read('exportPathsList'))
                                if path not in self.parent.exportPathsList:
                                        self.parent.exportPathsList.append(str(path))
                                self.parent.cfg.Write('exportPathsList', str(eval('self.parent.exportPathsList')))
                                
                                # ajout dans le dictionnaire pour recupere le chemin à l'insertion dans DEVSimPy (voir OnImport)
                                self.d.update({dName:path})
                        else:
                                dial = wx.MessageDialog(self, _('Error %s already imported')%dName, _('Error'), wx.OK | wx.ICON_ERROR)
                                dial.ShowModal()
                                self.dbb.SetValue('')
                else:
                        dial = wx.MessageDialog(self, _('Error %s already imported')%dName, _('Error'), wx.OK | wx.ICON_ERROR)
                        dial.ShowModal()
                                
                # on reactive le bouton pour un eventuel autre ajout
                self.btn_Add.Enable(False)

if __name__ == '__main__':
	app = wx.App()
	t=ImportLibrary(None, wx.ID_ANY, 'DEVSimPy Library Dialog Test')
	t.Show()
	app.MainLoop()