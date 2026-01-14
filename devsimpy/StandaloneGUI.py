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
        self.SetSize((650, 640))
        
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        
        # Sizer principal avec marges uniformes
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- En-tête avec titre et bouton d'aide (NOUVEAU) ---
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        title_label = wx.StaticText(panel, label=_("Standalone Package Generator"))
        title_font = title_label.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title_label.SetFont(title_font)
        
        help_btn = wx.Button(panel, wx.ID_HELP, "?", size=(30, 30))
        help_btn.SetToolTip(_("Show help about standalone package generation"))
        
        header_sizer.Add(title_label, 0, wx.ALIGN_CENTER_VERTICAL)
        header_sizer.AddStretchSpacer()
        header_sizer.Add(help_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        main_sizer.Add(header_sizer, 0, wx.ALL|wx.EXPAND, border=15)
        
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
        
        # --- Section Build Options ---
        build_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Build Options"))
        
        build_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._cb_log = wx.CheckBox(panel, label=_('Enable Logging'))
        self._cb_log.SetToolTip(_("Enable detailed logging during package generation to track the build process."))
        build_sizer.Add(self._cb_log, flag=wx.ALL, border=5)
        
        build_box.Add(build_sizer, flag=wx.ALL, border=5)
        main_sizer.Add(build_box, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=15)
        
        # --- Section Kernel Configuration ---
        kernel_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Kernel Configuration"))
        
        kernel_grid = wx.FlexGridSizer(rows=2, cols=2, vgap=8, hgap=10)
        kernel_grid.AddGrowableCol(1, 1)
        
        # Kernel choice
        self.kernel_label = wx.StaticText(panel, -1, _("Kernel:"))
        self.kernel_label.Enable(False)
        kernel_grid.Add(self.kernel_label, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.kernel = wx.Choice(panel, -1, choices=["PyDEVS", "PyPDEVS", "BrokerDEVS"])
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
        self.Bind(wx.EVT_BUTTON, self.OnShowStandaloneHelp, id=wx.ID_HELP)  # NOUVEAU
        self.Bind(wx.EVT_CHECKBOX, self.OnChecked, id=self._cb1.GetId()) 
        self.Bind(wx.EVT_CHOICE, self.OnChoice, id=self.kernel.GetId())
        
        # Focus sur le champ de texte
        self._tc.SetFocus()
        self._tc.SetInsertionPointEnd()


    def OnShowStandaloneHelp(self, event):
        """Show help dialog about standalone package generation"""
        
        help_msg = _(
            "STANDALONE PACKAGE GENERATOR\n\n"
            "═══════════════════════════════════════\n\n"
            "OVERVIEW:\n\n"
            "This tool creates a standalone, executable package of your DEVS model.\n"
            "The generated package can run simulations WITHOUT DEVSimPy installed,\n"
            "making it perfect for deployment, distribution, and production use.\n\n"
            "═══════════════════════════════════════\n\n"
            "PACKAGE CONFIGURATION:\n\n"
            "• Filename: Name of the ZIP package to create\n"
            "  - Must end with .zip extension\n"
            "  - Example: MyModel-nogui-pkg.zip\n"
            "  - Default based on your model name\n\n"
            "• Directory: Where to save the generated package\n"
            "  - Click 'Browse...' to select location\n"
            "  - Package will be created in this directory\n"
            "  - Ensure you have write permissions\n\n"
            "• Format: Package complexity level\n"
            "  - Minimal: Only essential library files (smaller size)\n"
            "    • Faster to generate and transfer\n"
            "    • May miss some dependencies\n"
            "    • Good for simple models\n\n"
            "  - Full: All library dependencies included (larger size)\n"
            "    • More reliable and self-contained\n"
            "    • Works on any system\n"
            "    • Recommended for distribution\n\n"
            "═══════════════════════════════════════\n\n"
            "SIMULATION OPTIONS:\n\n"
            "• Add Simulation Kernel:\n"
            "  - Includes DEVS simulation engine files\n"
            "  - Required if package will run simulations\n"
            "  - Enables kernel selection below\n"
            "  - Uncheck only for model-only packages\n\n"
            "• Add Docker File:\n"
            "  - Includes Dockerfile for containerization\n"
            "  - Allows running in Docker containers\n"
            "  - Useful for cloud deployment\n"
            "  - Creates isolated, reproducible environment\n\n"
            "• Add NTL Flag (Infinite Loop):\n"
            "  - NTL = No Time Limit\n"
            "  - Simulation runs until models are inactive\n"
            "  - Good for event-driven simulations\n"
            "  - Package will use -ntl command line flag\n\n"
            "═══════════════════════════════════════\n\n"
            "KERNEL CONFIGURATION:\n\n"
            "(Only available when 'Add Simulation Kernel' is checked)\n\n"
            "• Kernel: Choose DEVS simulation engine\n\n"
            "  - PyDEVS:\n"
            "    • Classic DEVS simulator\n"
            "    • Single-threaded execution\n"
            "    • Simple and reliable\n"
            "    • Good for small models\n\n"
            "  - PyPDEVS:\n"
            "    • Parallel DEVS simulator (recommended)\n"
            "    • Multi-threaded execution\n"
            "    • Better performance\n"
            "    • Supports real-time mode\n\n"
            "  - BrokerDEVS:\n"
            "    • Distributed DEVS over Apache Kafka\n"
            "    • For large-scale simulations\n"
            "    • Requires Kafka infrastructure\n"
            "    • Advanced use only\n\n"
            "• Real Time Mode:\n"
            "  - Only available with PyPDEVS kernel\n"
            "  - Synchronizes simulation with wall clock\n"
            "  - Useful for hardware-in-the-loop\n"
            "  - Slower but matches real time\n\n"
            "═══════════════════════════════════════\n\n"
            "WHAT'S IN THE PACKAGE:\n\n"
            "The generated ZIP file contains:\n\n"
            "• Your DEVS model in YAML format\n"
            "• All referenced Python model files\n"
            "• Required library dependencies\n"
            "• Simulation kernel (if selected)\n"
            "• Dockerfile (if selected)\n"
            "• README with usage instructions\n"
            "• Command-line execution script\n\n"
            "═══════════════════════════════════════\n\n"
            "HOW TO USE THE PACKAGE:\n\n"
            "After generation:\n\n"
            "1. Extract the ZIP file on target system\n"
            "2. Install Python 3.x if not present\n"
            "3. Run the provided script:\n"
            "   python run_simulation.py\n\n"
            "4. (Optional) Build Docker image:\n"
            "   docker build -t mymodel .\n"
            "   docker run mymodel\n\n"
            "No DEVSimPy installation required!\n\n"
            "═══════════════════════════════════════\n\n"
            "USE CASES:\n\n"
            "• Deployment: Send model to users without DEVSimPy\n"
            "• Production: Run simulations on servers\n"
            "• Cloud: Deploy in Docker containers\n"
            "• Distribution: Share models with colleagues\n"
            "• Archiving: Preserve complete model state\n"
            "• Testing: Run models in isolated environments\n\n"
            "═══════════════════════════════════════\n\n"
            "REQUIREMENTS:\n\n"
            "• Valid YAML model file\n"
            "• All model Python files accessible\n"
            "• Write permissions in target directory\n"
            "• Sufficient disk space (varies by format)\n\n"
            "═══════════════════════════════════════\n\n"
            "TIPS:\n\n"
            "- Use 'Full' format for maximum compatibility\n"
            "- Include simulation kernel for executable packages\n"
            "- Add Docker file for cloud deployment\n"
            "- Test package on target system before distribution\n"
            "- PyPDEVS is recommended for better performance\n"
            "- Real-time mode useful for IoT/embedded systems\n"
            "- Check README in generated package for details\n\n"
            "═══════════════════════════════════════\n\n"
            "TROUBLESHOOTING:\n\n"
            "• Package generation fails:\n"
            "  → Check YAML file is valid\n"
            "  → Ensure all Python files are accessible\n"
            "  → Verify write permissions\n\n"
            "• Package won't run:\n"
            "  → Use 'Full' format instead of 'Minimal'\n"
            "  → Check Python version compatibility\n"
            "  → Install missing dependencies\n\n"
            "• Docker build fails:\n"
            "  → Ensure Docker is installed\n"
            "  → Check Dockerfile syntax\n"
            "  → Review Docker logs for errors"
        )
        
        try:
            import wx.lib.dialogs
            dlg = wx.lib.dialogs.ScrolledMessageDialog(
                self, 
                help_msg, 
                _("Standalone Package Generator Help"),
                size=(700, 650)
            )
            dlg.ShowModal()
            dlg.Destroy()
        except Exception as e:
            # Fallback
            wx.MessageBox(
                help_msg,
                _("Standalone Package Generator Help"),
                wx.OK | wx.ICON_INFORMATION
            )


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
        log_cb = self._cb_log.GetValue()
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
                kernel=kernel,
                enable_log=log_cb
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