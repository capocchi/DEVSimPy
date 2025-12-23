# -*- coding: utf-8 -*-

'''
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
'''

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
        
        if len(text) == 0:
            wx.MessageBox(_("A text object must contain some text!"), "Error")
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        elif not text.endswith('.zip'):
            wx.MessageBox(_("Zip name must end with .zip extension!"), "Error")
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
        return True

    def TransferFromWindow(self):
        """ Transfer data from window to validator.

            The default implementation returns False, indicating that an error
            occurred.  We simply return True, as we don't do any data transfer.
        """
        return True
    
class StandaloneGUI(wx.Frame):
    """ Class used to generate the standalone version of DEVSimPy-nogui as a zip file.

    Args:
        wx (wx.Frame): GUI to configure the exportation of the zip file.
    """

    last_opened_directory = "."

    def __init__(self, *args, **kw):
        """Constructor.
        """

        ### local copy
        if 'yaml' in kw:
            self.yaml = kw['yaml']
            del kw['yaml']
            assert(os.path.exists(self.yaml))
            self.yaml_model_name = os.path.basename(self.yaml.split('.')[0])
        else:
            self.yaml_model_name = "Test.yaml"

        super(StandaloneGUI, self).__init__(*args, **kw)

        self.InitUI()
        self.Center()
        
    def InitUI(self):
        """Initialize the wx.Frame
        """
        
        icon = wx.Icon()
        icon.CopyFromBitmap(load_and_resize_image("properties.png"))
        self.SetIcon(icon)
  
        # Taille adaptée au contenu
        self.SetSize((650, 500))
        # self.SetMinSize((600, 450))
        
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        
        # Sizer principal avec marges uniformes
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- Section Package Configuration ---
        config_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Package Configuration"))
        
        # Grille pour filename et directory
        config_grid = wx.FlexGridSizer(rows=3, cols=2, vgap=10, hgap=10)
        config_grid.AddGrowableCol(1, 1)
        
        # Filename
        filename_label = wx.StaticText(panel, label=_('Filename:'))
        filename_label.SetToolTip(_("Select a name for the standalone package"))
        config_grid.Add(filename_label, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self._tc = wx.TextCtrl(panel, -1, 
                               f"{self.yaml_model_name}-nogui-pkg.zip",
                               validator=ZipNameValidator())
        self._tc.SetToolTip(_("Must end with .zip"))
        config_grid.Add(self._tc, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        # Directory
        dir_label = wx.StaticText(panel, label=_('Directory:'))
        dir_label.SetToolTip(_("Select a target directory"))
        config_grid.Add(dir_label, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self._dbb = filebrowse.DirBrowseButton(
            panel, 
            -1,
            labelText="",
            buttonText=_("Browse..."),
            startDirectory=StandaloneGUI.last_opened_directory,
            toolTip=_("Select a target directory to create the standalone package"),
            dialogTitle=_("Choose a directory")
        )
        config_grid.Add(self._dbb, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        # Format
        format_label = wx.StaticText(panel, -1, _("Format:"))
        format_label.SetToolTip(_("The minimal format includes only necessary library files.\n"
                                   "The full format includes all library dependencies (more secure)."))
        config_grid.Add(format_label, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.format = wx.Choice(panel, -1, choices=["Minimal", "Full"])
        self.format.SetSelection(0)
        config_grid.Add(self.format, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        config_box.Add(config_grid, flag=wx.ALL|wx.EXPAND, border=10)
        main_sizer.Add(config_box, flag=wx.ALL|wx.EXPAND, border=15)
        
        # --- Section Simulation Options ---
        sim_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Simulation Options"))
        
        # Checkboxes
        cb_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._cb1 = wx.CheckBox(panel, label=_('Add Simulation Kernel'))
        self._cb1.SetToolTip(_("Add all files needed to simulate the model."))
        cb_sizer.Add(self._cb1, flag=wx.ALL, border=5)
        
        self._cb2 = wx.CheckBox(panel, label=_('Add Docker File'))
        self._cb2.SetToolTip(_("Add Docker file to execute the simulation in a Docker Container."))
        cb_sizer.Add(self._cb2, flag=wx.ALL, border=5)
        
        self._cb3 = wx.CheckBox(panel, label=_('Add NTL Flag (Infinite Loop)'))
        self._cb3.SetToolTip(_("Add the flag -ntl to define an infinite simulation loop."))
        cb_sizer.Add(self._cb3, flag=wx.ALL, border=5)
        
        sim_box.Add(cb_sizer, flag=wx.ALL, border=5)
        main_sizer.Add(sim_box, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=15)
        
        # --- Section Kernel Configuration ---
        kernel_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Kernel Configuration"))
        
        kernel_grid = wx.FlexGridSizer(rows=2, cols=2, vgap=8, hgap=10)
        kernel_grid.AddGrowableCol(1, 1)
        
        # Kernel choice
        self.kernel_label = wx.StaticText(panel, -1, _("Kernel:"))
        self.kernel_label.Enable(False)
        kernel_grid.Add(self.kernel_label, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.kernel = wx.Choice(panel, -1, choices=["PyDEVS", "PyPDEVS", "KafkaDEVS"])
        self.kernel.SetSelection(0)
        self.kernel.Enable(False)
        kernel_grid.Add(self.kernel, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        # Real Time checkbox
        rt_label = wx.StaticText(panel, -1, _("Mode:"))
        rt_label.Enable(False)
        kernel_grid.Add(rt_label, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self._cb4 = wx.CheckBox(panel, label=_('Real Time'))
        self._cb4.Enable(False)
        kernel_grid.Add(self._cb4, flag=wx.ALIGN_CENTER_VERTICAL)
        
        kernel_box.Add(kernel_grid, flag=wx.ALL|wx.EXPAND, border=10)
        main_sizer.Add(kernel_box, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=15)
        
        # --- Buttons ---
        button_sizer = wx.StdDialogButtonSizer()
        
        btn_ok = wx.Button(panel, wx.ID_OK, _("Generate Package"))
        btn_ok.SetDefault()
        button_sizer.AddButton(btn_ok)
        
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, _("Cancel"))
        button_sizer.AddButton(btn_cancel)
        
        button_sizer.Realize()
        
        main_sizer.Add(button_sizer, flag=wx.ALL|wx.ALIGN_RIGHT, border=15)
        
        panel.SetSizer(main_sizer)
    
        ### Binds
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_CHECKBOX, self.OnChecked, id=self._cb1.GetId()) 
        self.Bind(wx.EVT_CHOICE, self.OnChoice, id=self.kernel.GetId())
        
        # Focus sur le champ de texte
        self._tc.SetFocus()
        self._tc.SetInsertionPointEnd()

    def OnChoice(self, event):
        selected_option = self.kernel.GetStringSelection()
        self._cb4.Enable(selected_option == 'PyPDEVS')
        
    def OnChecked(self, event): 
        """Add Simulation Kernel Checkbox has been clicked.

        Args:
            event (Event): event
        """
        cb = event.GetEventObject()
        is_checked = cb.IsChecked()
        
        self.kernel.Enable(is_checked)
        self.kernel_label.Enable(is_checked)
        
        # Enable/disable real-time based on kernel selection
        if is_checked:
            selected_kernel = self.kernel.GetStringSelection()
            self._cb4.Enable(selected_kernel == 'PyPDEVS')
        else:
            self._cb4.Enable(False)

    @BuzyCursorNotification
    def OnOk(self, event):
        """
        Args:
            event (wx.Event): event emitted when the Ok button is clicked
        """
    
        ### call validator for zip name textctrl
        if not self._tc.GetValidator().Validate(self._tc):
            return
            
        format = self.format.GetString(self.format.GetSelection())
        zip_name = self._tc.GetValue()
        zip_dir = self._dbb.GetValue()
        
        if not zip_dir:
            wx.MessageBox(_("Please select a directory!"), _("Error"), 
                         wx.OK | wx.ICON_ERROR)
            return
        
        sim_cb = self._cb1.GetValue()
        docker_cb = self._cb2.GetValue()
        ntl_cb = self._cb3.GetValue()
        rt = self._cb4.GetValue()
        kernel = self.kernel.GetString(self.kernel.GetSelection())
        
        try:
            ### call the StandaloneNoGUI class to build the package
            standalone = StandaloneNoGUI(
                self.yaml,
                zip_name,
                format=format,
                outdir=zip_dir,
                add_sim_kernel=sim_cb,
                add_dockerfile=docker_cb,
                sim_time=ntl_cb,
                rt=rt,
                kernel=kernel
            )
            
            ### Try to build the zip package of the standalone version
            if standalone.BuildZipPackage():
                resp = wx.MessageBox(
                    _("Zip file exported successfully!"), 
                    _("Success"), 
                    wx.OK | wx.ICON_INFORMATION
                )
                if resp == wx.OK:
                    self.Close()
            else:
                wx.MessageBox(
                    _("Export failed! Please check the YAML file."), 
                    _("Error"), 
                    wx.OK | wx.ICON_ERROR
                )
        except Exception as e:
            wx.MessageBox(
                _("An error occurred: {}").format(str(e)), 
                _("Error"), 
                wx.OK | wx.ICON_ERROR
            )
            
    def OnClose(self, event):
        """Event handler of the close event

        Args:
            event (wx.Event): wx event
        """
        self.Close()