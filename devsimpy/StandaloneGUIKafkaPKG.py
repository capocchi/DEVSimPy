# -*- coding: utf-8 -*-

'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# StandaloneGUIKafkaPKG.py ---
#                     --------------------------------
#                           Copyright (c) 2025
#                            Laurent CAPOCCHI 
#                         (capocchi@univ-corse.fr)
#                          University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/01/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
'''

import wx
import wx.lib.filebrowsebutton as filebrowse
import os

from StandaloneNoGUIKafkaPKG import StandaloneNoGUIKafkaPKG
from Decorators import BuzyCursorNotification
from Utilities import load_and_resize_image
from StandaloneGUI import ZipNameValidator

_ = wx.GetTranslation
    
class StandaloneGUIKafkaPKG(wx.Frame):
    """ Class used to generate the standalone version of DEVSimPy-nogui as a zip file.

    Args:
        wx (wx.Frame): GUI to configure the exportation of the zip file.
    """

    last_opened_directory = "."

    def __init__(self, *args, **kw):
        """Constructor.
        """

        ### local copy
        if 'block_model' in kw:
            self.block_model = kw['block_model']
            del kw['block_model']

            if self.block_model:
                if self.block_model.isAMD() or self.block_model.isCMD():
                    assert(os.path.exists(self.block_model.model_path))
                elif self.block_model.isPY():
                    assert(os.path.exists(self.block_model.python_path))
            else:
                if args[0]:
                    raise ValueError(_("The 'block_model' param must be not None"))
        else:
            raise KeyError(_("The 'block_model' keyword argument is required but was not provided."))

        super().__init__(*args, **kw)

        self.InitUI()
        self.Center()
        
    def InitUI(self):
        """Initialize the wx.Frame
        """
        
        icon = wx.Icon()
        icon.CopyFromBitmap(load_and_resize_image("properties.png"))
        self.SetIcon(icon)
        
        block_model_label = self.block_model.label if self.block_model else "model"

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        
        # Sizer principal avec marges uniformes
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- Section Filename ---
        filename_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Package Configuration"))
        
        # Filename field
        filename_grid = wx.FlexGridSizer(rows=2, cols=2, vgap=8, hgap=10)
        filename_grid.AddGrowableCol(1, 1)
        
        self.st1 = wx.StaticText(panel, label=_('Filename:'))
        self.st1.SetToolTip(_("Select a name for the standalone package"))
        filename_grid.Add(self.st1, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self._tc = wx.TextCtrl(panel, -1, 
                               f"{block_model_label}-nogui-pkg.zip",
                               validator=ZipNameValidator())
        self._tc.SetToolTip(_("Must end with .zip"))
        filename_grid.Add(self._tc, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        # Directory field
        dir_label = wx.StaticText(panel, label=_('Directory:'))
        dir_label.SetToolTip(_("Select a target directory"))
        filename_grid.Add(dir_label, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self._dbb = filebrowse.DirBrowseButton(
            panel, 
            -1,
            labelText="",
            buttonText=_("Browse..."),
            startDirectory=StandaloneGUIKafkaPKG.last_opened_directory,
            toolTip=_("Select a target directory to create the standalone package"),
            dialogTitle=_("Choose a directory")
        )
        filename_grid.Add(self._dbb, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        filename_box.Add(filename_grid, flag=wx.ALL|wx.EXPAND, border=10)
        main_sizer.Add(filename_box, flag=wx.ALL|wx.EXPAND, border=15)
        
        # --- Section Kernel ---
        kernel_box = wx.StaticBoxSizer(wx.HORIZONTAL, panel, _("Options"))
        
        self.kernel_label = wx.StaticText(panel, -1, _("Kernel:"))
        kernel_box.Add(self.kernel_label, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=10)
        
        self.kernel = wx.Choice(panel, -1, choices=["BrokerDEVS"])
        self.kernel.SetSelection(0)
        kernel_box.Add(self.kernel, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=10)
        
        # Ajout du séparateur
        kernel_box.Add((20, -1))  # Espacement
        
        self.strategy_label = wx.StaticText(panel, -1, _("Strategy:"))
        kernel_box.Add(self.strategy_label, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=10)
        
        self.strategy = wx.Choice(panel, -1, choices=list(BROKERDEVS_SIM_STRATEGY_DICT.keys()))
        self.strategy.SetSelection(0)
        kernel_box.Add(self.strategy, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=10)
        
        main_sizer.Add(kernel_box, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=15)
        
        # --- Section Kafka Configuration ---
        kafka_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Kafka Configuration"))

        kafka_grid = wx.FlexGridSizer(rows=5, cols=2, vgap=8, hgap=10)
        kafka_grid.AddGrowableCol(1, 1)

        # Label
        kafka_grid.Add(wx.StaticText(panel, label=_("Label:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self.kf_label = wx.TextCtrl(panel, -1, block_model_label)
        kafka_grid.Add(self.kf_label, flag=wx.EXPAND)

        # Container name
        kafka_grid.Add(wx.StaticText(panel, label=_("Container name:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self.kf_container = wx.TextCtrl(panel, -1, "broker")
        kafka_grid.Add(self.kf_container, flag=wx.EXPAND)

        # Bootstrap server
        kafka_grid.Add(wx.StaticText(panel, label=_("Bootstrap:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self.kf_bootstrap = wx.TextCtrl(panel, -1, "localhost:9092")
        kafka_grid.Add(self.kf_bootstrap, flag=wx.EXPAND)

        # Input topic
        kafka_grid.Add(wx.StaticText(panel, label=_("Input topic:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self.kf_input_topic = wx.TextCtrl(panel, -1, "")
        kafka_grid.Add(self.kf_input_topic, flag=wx.EXPAND)

        # Output topic
        kafka_grid.Add(wx.StaticText(panel, label=_("Output topic:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self.kf_output_topic = wx.TextCtrl(panel, -1, "")
        kafka_grid.Add(self.kf_output_topic, flag=wx.EXPAND)

        kafka_box.Add(kafka_grid, flag=wx.ALL | wx.EXPAND, border=10)

        main_sizer.Add(kafka_box, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=15)
        
        # --- Section Build Options ---
        build_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Build Options"))
        
        build_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._cb_log = wx.CheckBox(panel, label=_('Enable Logging'))
        self._cb_log.SetToolTip(_("Enable detailed logging during package generation to track the build process."))
        build_sizer.Add(self._cb_log, flag=wx.ALL, border=5)
        
        build_box.Add(build_sizer, flag=wx.ALL, border=5)
        main_sizer.Add(build_box, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=15)

        # --- Buttons ---
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, _("Cancel"), size=(120, 30))
        button_sizer.Add(btn_cancel)
        
        btn_ok = wx.Button(panel, wx.ID_OK, _("Generate Package"), size=(140, 30))
        btn_ok.SetDefault()
        button_sizer.Add(btn_ok, flag=wx.LEFT, border=5)
        
        main_sizer.Add(button_sizer, flag=wx.ALL|wx.ALIGN_RIGHT, border=15)
        
        # IMPORTANT: Définir le sizer AVANT d'appeler Fit()
        panel.SetSizer(main_sizer)
        
        # Forcer le calcul de la taille minimale
        main_sizer.SetSizeHints(self)
        
        # Laisser wxPython calculer la taille optimale
        panel.Layout()
        self.Fit()
        
        # Ajouter une marge de sécurité pour la hauteur
        size = self.GetSize()
        self.SetSize((max(600, size.width), size.height + 20))
        self.SetMinSize((600, size.height + 20))

        ### Binds
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_CHOICE, self.OnChoiceKernel, id=self.kernel.GetId())
        self.Bind(wx.EVT_CHOICE, self.OnChoiceStrategy, id=self.strategy.GetId())
        
        # Focus sur le champ de texte
        self._tc.SetFocus()
        self._tc.SetInsertionPointEnd()
    
    def OnChoiceKernel(self, event):
        selected_option = self.kernel.GetStringSelection()
        
    def OnChoiceStrategy(self, event):
        selected_option = self.strategy.GetStringSelection()

    @BuzyCursorNotification
    def OnOk(self, event):
        """
        Args:
            event (wx.Event): event emitted when the Ok button is clicked
        """
    
        ### call validator for zip name textctrl
        if not self._tc.GetValidator().Validate(self._tc):
            return
            
        zip_name = self._tc.GetValue()
        zip_dir = self._dbb.GetValue()
        
        if not zip_dir:
            wx.MessageBox(_("Please select a directory!"), _("Error"), 
                         wx.OK | wx.ICON_ERROR)
            return
        
        kernel = self.kernel.GetString(self.kernel.GetSelection())
        log_cb = self._cb_log.GetValue()
        
        try:
            ### call the StandaloneNoGUIKafkaPKG class to build the package
            standalone = StandaloneNoGUIKafkaPKG(
                self.block_model,
                label=self.kf_label.GetValue(),
                outfn=zip_name, 
                outdir=zip_dir,
                kafka_container_name=self.kf_container.GetValue(),
                kafka_boostrap=self.kf_bootstrap.GetValue(),
                input_topic=self.kf_input_topic.GetValue(),
                output_topic=self.kf_output_topic.GetValue(),
                enable_log=log_cb
            )
            
            ### Try to build the zip package
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
                    _("Export failed! Please check the configuration."), 
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