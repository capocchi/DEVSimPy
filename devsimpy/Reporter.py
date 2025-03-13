# -*- coding: utf-8 -*-

import sys
import wx

_ = wx.GetTranslation

from wxPyMail import SendMailWx
from Utilities import FormatTrace, EnvironmentInfo, GetActiveWindow, getTopLevelWindow

ID_SEND = wx.NewIdRef()

class BaseDialog(wx.Dialog):
    """ A wx.Dialog base class.
    """

    def __init__(self, parent):
        """ Constructor.
        """

        wx.Dialog.__init__(self, parent, size=(500,600), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.MainFrame = parent

    def CreateButtons(self):
        """ Creates the Ok and cancel bitmap buttons. """

        # Build a couple of fancy and useless buttons
        self.cancelButton= wx.Button(self.panel, wx.ID_CANCEL, "")
        self.obButton = wx.Button(self.panel, wx.ID_OK, "")

    def SetProperties(self, title):
        """ Sets few properties for the dialog. """

        self.SetTitle(title)
        self.okButton.SetDefault()

    def BindEvents(self):
        """ Binds the events to specific methods. """

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUp)

    def OnOk(self, event):
        """ Handles the Ok wx.EVT_BUTTON event for the dialog. """

        self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        """ Handles the Cancel wx.EVT_BUTTON event for the dialog. """

        self.OnClose(event)

    def OnClose(self, event):
        """ User canceled the dialog. """

        self.EndModal(wx.ID_CANCEL)
        event.Skip()

    def OnKeyUp(self, event):
        """ Handles the wx.EVT_CHAR_HOOK event for the dialog. """

        if event.GetKeyCode() == wx.WXK_ESCAPE:
            # Close the dialog, no action
            self.OnClose(event)
        elif event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            # Close the dialog, the user wants to continue
            self.OnOk(event)

        event.Skip()

def ExceptionHook(exctype, value, trace):
    """
    Handler for all unhandled exceptions.


    **Parameters:**

    * exctype: Exception Type
    * value: Error Value
    * trace: Trace back info
    """

    ftrace = FormatTrace(exctype, value, trace)

    # Ensure that error gets raised to console as well
    sys.stdout.write(ftrace)

    if not ErrorDialog.REPORTER_ACTIVE:
        ErrorDialog(ftrace)

class ErrorReporter(object):
    """Crash/Error Reporter Service
    @summary: Stores all errors caught during the current session and
    is implemented as a singleton so that all errors pushed
    onto it are kept in one central location no matter where
    the object is called from.

    **Note:**

    * from Editra.dev_tool

    """

    instance = None
    _first = True

    def __init__(self):
        """Initialize the reporter

        **Note:**

        * The ErrorReporter is a singleton.

        """
        # Ensure init only happens once
        if self._first:
            object.__init__(self)
            self._first = False
            self._sessionerr = list()
        else:
            pass

    def __new__(cls, *args, **kargs):
        """Maintain only a single instance of this object

        **Returns:**

        * instance of this class

        """
        if not cls.instance:
            cls.instance = object.__new__(cls, *args, **kargs)
        return cls.instance

    def AddMessage(self, msg):
        """Adds a message to the reporters list of session errors

        **Parameters:**

        * msg: The Error Message to save

        """
        if msg not in self._sessionerr:
            self._sessionerr.append(msg)

    def GetErrorStack(self):
        """Returns all the errors caught during this session

        **Returns:**

        * formatted log message of errors

        """
        return "\n\n".join(self._sessionerr)

    def GetLastError(self):
        """Gets the last error from the current session

        **Returns:**

        * Error Message String

        """
        if len(self._sessionerr):
            return self._sessionerr[-1]

class ErrorDialog(BaseDialog):
    """
    Dialog for showing errors and and notifying gui2exe-users should the
    user choose so.

    **Note:**

    * partially from Editra.dev_tool
    """
    ABORT = False
    REPORTER_ACTIVE = False

    def __init__(self, message):
        """
        Initialize the dialog

        **Parameters:**

        * message: Error message to display
        """
        ErrorDialog.REPORTER_ACTIVE = True

        # Get version from the app since the main window may be dead or
        # not even ready yet.
        #version = wx.GetApp().GetVersion()

        BaseDialog.__init__(self, GetActiveWindow())

        # Give message to ErrorReporter
        ErrorReporter().AddMessage(message)
        
        self.SetTitle(_("Error/Crash Reporter"))

        # Attributes
        self.err_msg = "%s\n\n%s\n%s\n%s" % (EnvironmentInfo(), \
                                             "---- Traceback Info ----", \
                                             str(ErrorReporter().GetErrorStack()), \
                                             "---- End Traceback Info ----")

        self.textCtrl = wx.TextCtrl(self, value=self.err_msg, size=(-1,200),style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.abortButton = wx.Button(self, wx.ID_CANCEL, size=(-1, 26))
        self.sendButton = wx.Button(self, ID_SEND, _("Report Error"), size=(-1, 26))
        self.sendButton.SetDefault()
        self.closeButton = wx.Button(self, wx.ID_CLOSE, size=(-1, 26))

        # Layout
        self.DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Auto show at end of init
        self.CenterOnParent()
        self.ShowModal()

    def DoLayout(self):
        """ Layout the dialog and prepare it to be shown
            
            **Note:**

            *  Do not call this method in your code
        """

        # Objects
        mainmsg = wx.StaticText(self,
                                label=_("Help improve DEVSimPy by clicking on "
                                        "Report Error\nto send the Error "
                                        "Traceback shown below."))
        t_lbl = wx.StaticText(self, label=_("Error Traceback:"))

        t_lbl.SetFont(wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False))
        # Layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)

        #topSizer.Add(self.errorBmp, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 20)
        topSizer.Add(mainmsg, 0, wx.EXPAND|wx.RIGHT, 20)
        mainSizer.Add(topSizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 20)
        mainSizer.Add(t_lbl, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)
        mainSizer.Add((0, 2))
        mainSizer.Add(self.textCtrl, 1, wx.EXPAND|wx.ALL, 5)
        bottomSizer.Add(self.abortButton, 0, wx.ALL, 5)
        bottomSizer.Add((0, 0), 1, wx.EXPAND)
        bottomSizer.Add(self.sendButton, 0, wx.TOP|wx.BOTTOM, 5)
        bottomSizer.Add((0, 10))
        bottomSizer.Add(self.closeButton, 0, wx.TOP|wx.BOTTOM|wx.RIGHT, 5)
        mainSizer.Add(bottomSizer, 0, wx.EXPAND)

        self.SetSizerAndFit(mainSizer)
        self.SetAutoLayout(True)
        self.Fit()

    def OnButton(self, evt):
        """Handles button events

        **Parameters:**

        * evt: event that called this handler

        **Post-Conditions:**

        * Dialog is closed
        * If Report Event then email program is opened

        """
        e_id = evt.GetId()
        if e_id == wx.ID_CLOSE:
            self.Close()

        elif e_id == ID_SEND:
            frame = SendMailWx(None, _('New Email Message (From Google account)'))
            msg = self.err_msg
            msg = msg.replace("'", '')
            frame.messageTxt.SetValue(msg)
            mainW = getTopLevelWindow()
            msg = _('DEVSimPy %s Error Report')%str( mainW.GetVersion())
            frame.subjectTxt.SetValue(msg)
            frame.Show()
            self.Close()

        elif e_id == wx.ID_ABORT:
            ErrorDialog.ABORT = True
            # Try a nice shutdown first time through
            wx.CallLater(500, wx.GetApp().Destroy(),
                         wx.MenuEvent(wx.wxEVT_MENU_OPEN, wx.ID_EXIT),
                         True)
            self.Close()

        else:
            evt.Skip()

    def OnClose(self, evt):
        """Cleans up the dialog when it is closed

        **Parameters:**

        * evt: Event that called this handler

        """
        ErrorDialog.REPORTER_ACTIVE = False
        self.Destroy()
        evt.Skip()