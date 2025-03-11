# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# StandaloneGUI.py ---
#                     --------------------------------
#                           Copyright (c) 2022
#                            Laurent CAPOCCHI 
#                         (capocchi@univ-corse.fr)
#                          University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/11/23
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import wx
import os
import wx.lib.filebrowsebutton as filebrowse

from StandaloneNoGUI import StandaloneNoGUI
from Decorators import BuzyCursorNotification
from Utilities import load_and_resize_image

_ = wx.GetTranslation

class ZipNameValidator(wx.Validator):
    """ This validator is used to ensure that the user has entered something
        into the text object editor dialog's text field.
    """
    def __init__(self):
        """ Standard constructor.
        """
        wx.Validator.__init__(self)

    def Clone(self):
        """ Standard cloner.

            Note that every validator must implement the Clone() method.
        """
        return ZipNameValidator()

    def Validate(self, win):
        """ Validate the contents of the given text control.
        """
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        
        if len(text) == 0 :
            wx.MessageBox(_("A text object must contain some text!"), "Error")
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        elif text.endswith('.zip') == 0 :
            wx.MessageBox(_("Zip name must end with .zip extention!"), "Error")
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        else:
            textCtrl.SetBackgroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True

    def TransferToWindow(self):
        """ Transfer data from validator to window.

            The default implementation returns False, indicating that an error
            occurred.  We simply return True, as we don't do any data transfer.
        """
        return True # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        """ Transfer data from window to validator.

            The default implementation returns False, indicating that an error
            occurred.  We simply return True, as we don't do any data transfer.
        """
        return True # Prevent wxDialog from complaining.
    
class StandaloneGUI(wx.Frame):
    """ Class used to generate the standalone version of DEVSimPy-nogui as a zip file.

    Args:
        wx (wx.Frame): GUI to configure the exportation of the zip file.
    """

    last_opened_directory = "."  # Class variable to store the last opened directory

    def __init__(self, *args, **kw):
        """Constructor.
        """

        ### local copy
        self.yaml = kw['yaml']
        del kw['yaml']
        assert(os.path.exists(self.yaml))

        # This line calls the __init__ method of the parent class to initialize the GUI window.
        super(StandaloneGUI, self).__init__(*args, **kw)
       
        self.yaml_model_name = os.path.basename(self.yaml.split('.')[0])

        self.InitUI()
        self.Center()
        
    def InitUI(self):
        """Initialize the wx.Frame
        """
        
        icon = wx.Icon()
        icon.CopyFromBitmap(load_and_resize_image("properties.png"))
        self.SetIcon(icon)
  
        self.SetSize((-1, 250))
        panel = wx.Panel(self)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
 
        ### Zip name field
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.st1 = wx.StaticText(panel, label=_('Filename:'))
        self.st1.SetToolTip(_("Select a name for the standalone package"))
        
        hbox1.Add(self.st1, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, border=8)
        self._tc = wx.TextCtrl(panel, -1, f"{self.yaml_model_name}-nogui-pkg.zip", style=wx.TE_RICH2|wx.BORDER_NONE, validator=ZipNameValidator())
        self._tc.SetToolTip(_("Must end with .zip"))

        hbox1.Add(self._tc, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Set focus to StaticText object
        self.st1.SetFocus()

        vbox.Add((-1, 10))

        ### Zip directory field
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self._dbb = filebrowse.DirBrowseButton(panel, 
                                               -1, 
                                               size=(450, -1), 
                                               labelText = "Select Directory:",
                                               startDirectory = StandaloneGUI.last_opened_directory,
                                               toolTip=_("Select a target directory to create the standalone package"))
        # Set the initial directory
        self._dbb.startDirectory = StandaloneGUI.last_opened_directory

        hbox2.Add(self._dbb)
        vbox.Add(hbox2, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add((-1, 10))

        ### minimal (optimal) or full export
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)

        label_format = wx.StaticText(panel, -1, _("Format:"))
        label_format.SetToolTip("""The minimal format includes in the archive only the necessary library files\n (may lead to errors depending on your model's architecture).\n The full format includes all library dependencies (less optimal but more secure).""")
        self.format = wx.Choice(panel, -1, choices=["Minimal", "Full"])
        self.format.SetSelection(0)

        hbox3.Add(label_format, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL)
        hbox3.Add(self.format, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=10)    
        vbox.Add(hbox3, flag=wx.LEFT, border=10)
        vbox.Add((-1, 10))
        
        ### Options
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        self._cb1 = wx.CheckBox(panel, label=_('Add Simulation Kernel'))
        self._cb1.SetToolTip(_("Add all files needed to simulate the model."))
        self._cb2 = wx.CheckBox(panel, label=_('Add Docker File'))
        self._cb2.SetToolTip(_("Add Docker file to execute the simulation in a nogui model in a Docker Container."))
        self._cb3 = wx.CheckBox(panel, label=_('Add NTL Flag'))
        self._cb3.SetToolTip(_("Add the flag -ntl to the simulation in order to define an infinit simulation loop."))
    
        hbox4.Add(self._cb1)
        hbox4.Add(self._cb2, flag=wx.LEFT, border=10)    
        hbox4.Add(self._cb3, flag=wx.LEFT, border=10)
        vbox.Add(hbox4, flag=wx.LEFT, border=10)

        vbox.Add((-1, 10))
    
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        self._cb4 = wx.CheckBox(panel, label=_('Real Time'))
        self._cb4.Enable(False)
        self.kernel = wx.Choice(panel, -1, choices=["PyDEVS", "PyPDEVS"])
        self.kernel.SetSelection(0)
        self.kernel.Enable(False)
        self.kernel_label = wx.StaticText(panel, -1, _("Kernel:"))
        self.kernel_label.Enable(False)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.kernel_label, 0, wx.ALIGN_CENTER_VERTICAL)
        box.Add(self.kernel, 0, wx.ALIGN_CENTER_VERTICAL, border=5)
        
        hbox5.Add(box)
        hbox5.Add(self._cb4, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=10)
        vbox.Add(hbox5, flag=wx.LEFT, border=10)
        
        vbox.Add((-1, 10))

        ### Buttons
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        btn1 = wx.Button(panel, wx.ID_OK, _("Ok"), size=(70, 30))
        # btn2 = wx.Button(panel, wx.ID_CLOSE, _("Close"), size=(70, 30))
        # hbox5.Add(btn2)
        hbox5.Add(btn1, flag=wx.LEFT|wx.BOTTOM)
        vbox.Add(hbox5, flag=wx.ALIGN_RIGHT|wx.RIGHT, border=10)

        panel.SetSizer(vbox)
    
        ### Binds
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=btn1.GetId())
        # self.Bind(wx.EVT_BUTTON, self.OnClose, id=btn2.GetId())
        self.Bind(wx.EVT_CHECKBOX,self.OnChecked, id=self._cb1.GetId()) 
        self.Bind(wx.EVT_CHOICE, self.OnChoice, id=self.kernel.GetId())
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnDirChanged, id=self._dbb.GetId())
    
    def OnDirChanged(self, event):
        # Get the selected directory
        selected_dir = event.GetPath()
        StandaloneGUI.last_opened_directory = selected_dir

    def OnChoice(self, event):
        selected_option = self.kernel.GetStringSelection()
        self._cb4.Enable(selected_option == 'PyPDEVS')
        
    def OnChecked(self, event): 
        """Add Simulation Kernel Checkbox has been clicked.

        Args:
            event (Event): event
        """
        cb = event.GetEventObject() 
    #   cb.GetLabel(),' is clicked',cb.GetValue()

        self.kernel.Enable(cb.IsChecked())
        self.kernel_label.Enable(cb.IsChecked())

    @BuzyCursorNotification
    def OnOk(self, event):
        """
        Args:
            event (wx.Event): event emitted when the Ok button is clicked
        """
    
        ### call validator for zip name textctrl
        if self._tc.GetValidator().Validate(self._tc):
        
            format = self.format.GetString(self.format.GetSelection())
            zip_name = self._tc.GetLineText(0)
            zip_dir = self._dbb.GetValue()
            sim_cb = self._cb1.GetValue()
            docker_cb = self._cb2.GetValue()
            ntl_cb = self._cb3.GetValue()
            rt = self._cb3.GetValue()
            kernel = self.kernel.GetString(self.kernel.GetSelection())
            
            ### call the StandaloneNoGui class to build the package depending on the settings from the frame.
            standalone = StandaloneNoGUI(self.yaml,zip_name,format=format,outdir=zip_dir,add_sim_kernel=sim_cb,add_dockerfile=docker_cb,sim_time=ntl_cb,rt=rt, kernel=kernel)
            
            ### Try to build de zip package of the standalone version of DEVSimPy-nogui
            if standalone.BuildZipPackage():
                resp = wx.MessageBox(_("Zip file exported!"), _("Information"), wx.OK | wx.ICON_INFORMATION)
                if resp == wx.OK:
                    self.Close()
            else:
                resp = wx.MessageBox(_("Exportation failed! - Check the yaml file..."), _("Error"), wx.OK | wx.ICON_ERROR)
            
    def OnClose(self, event):
        """Event handler of the close event

        Args:
            event (wx.Event): wx event
        """
        self.Close()
             
def main():
    """To test the GUI
    """

    ex = wx.App()
    frame = StandaloneGUI(None, -1, 'Standalone Export')
    frame.Show(True)
    ex.MainLoop()

if __name__ == '__main__':
    main()