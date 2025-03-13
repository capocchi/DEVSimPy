################################################################################################################################################################################
# wxPyMail_gui.py
#
# Created: June 6, 2008
# Author:  Mike Driscoll
# email:   mike@pythonlibrary.org
#
# Feel free to email with questions, comments, or suggestions
#
# Need to edit HKEY_CLASSES_ROOT\mailto\shell\open\command and point it to this
# file.
#
# Ex. cmd /C "SET PYTHONHOME=c:\path\to\Python24&&c:\path\to\python24\python.exe c:\path\to\wxPyMail.py %1"
#     "C:\Program Files\PyMail\wxPyMail.exe" %1
#################################################################################################################################################################################

import math
import os
import smtplib
import urllib.request, urllib.parse, urllib.error
import wx
import wx.lib.agw.hyperlink as hl

_ = wx.GetTranslation

try:
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEBase import MIMEBase
    from email.MIMEText import MIMEText
    from email.Utils import formatdate
    from email import Encoders
except:
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email.utils import formatdate
    from email import encoders as Encoders

from Utilities import load_and_resize_image

class SendMailWx(wx.Frame):
    
    def __init__(self, *args, **kw):
        super(SendMailWx, self).__init__(*args, **kw)

        # set your email address here
        self.email = 'your_email@gmail.com'

        self.filepaths = []
        self.currentDir = os.getcwd()

        self.InitUI()

    def InitUI(self):

        self.panel = wx.Panel(self)
        
        self.createMenu()
        self.createToolbar()
        self.createWidgets()        
        self.layoutWidgets()
        
        self.attachTxt.Hide()
        self.editAttachBtn.Hide()

    def createMenu(self):
        menubar = wx.MenuBar()
        
        fileMenu = wx.Menu()
        send_menu_item = fileMenu.Append(wx.NewIdRef(), _('&Send'), _('Sends the email'))
        close_menu_item = fileMenu.Append(wx.NewIdRef(), _('&Close'), _('Closes the window'))
        menubar.Append(fileMenu, _('&File'))
        self.SetMenuBar(menubar)

        # bind events to the menu items
        self.Bind(wx.EVT_MENU, self.OnSend, send_menu_item)
        self.Bind(wx.EVT_MENU, self.OnClose, close_menu_item)

    def createToolbar(self):
        tb = wx.ToolBar(self, wx.NewIdRef(), name='tb', style=wx.TB_HORIZONTAL | wx.NO_BORDER)
        tb.SetToolBitmapSize((16,16))
        sendTool = tb.AddTool(wx.NewIdRef(), _('Send'), load_and_resize_image('mail.png'), _('Sends Email'))
        self.Bind(wx.EVT_MENU, self.OnSend, sendTool)        
        tb.Realize()
        self.SetToolBar(tb)

    def createWidgets(self):
        p = self.panel
              
        font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.fromLbl    = wx.StaticText(p, wx.NewIdRef(), _('From:'), size=(70,-1))
        self.fromTxt    = wx.TextCtrl(p, wx.NewIdRef(), self.email)
        self.toLbl      = wx.StaticText(p, wx.NewIdRef(), _('To:'), size=(70,-1))
        self.toTxt      = wx.TextCtrl(p, wx.NewIdRef(), 'capocchi_l@univ-corse.fr')
        self.subjectLbl = wx.StaticText(p, wx.NewIdRef(), _('Subject:'), size=(70,-1))
        self.subjectTxt = wx.TextCtrl(p, wx.NewIdRef(), '')
        self.attachBtn  = wx.Button(p, wx.NewIdRef(), _('Attachments'))        
        self.attachTxt  = wx.TextCtrl(p, wx.NewIdRef(), '', style=wx.TE_MULTILINE)
        self.attachTxt.Disable()
        self.editAttachBtn = wx.Button(p, wx.NewIdRef(), _('Edit Attachments'))
        
        self.messageTxt = wx.TextCtrl(p, wx.NewIdRef(), '', style=wx.TE_MULTILINE)

        # Web link with underline rollovers, opens in same window
        self.url = hl.HyperLinkCtrl(self.panel, -1, "Allow the access to Google for your less secure app", pos=(100, 150), URL="https://myaccount.google.com/lesssecureapps?pli=1")

        self.url.AutoBrowse(True)
        self.url.SetColours("BLUE", "BLUE", "BLUE")
        self.url.EnableRollover(True)
        self.url.SetUnderlines(False, False, True)
        self.url.SetBold(True)
        #self.url.OpenInSameWindow(True)
        self.url.SetToolTip(wx.ToolTip("In a nutshell, google is not allowing you to log in via smtplib because it has flagged this sort of login as 'less secure', so what you have to do is go to this link while you're logged in to your google account, and allow the access"))
        self.url.UpdateLink()

        self.Bind(wx.EVT_BUTTON, self.onAttach, self.attachBtn)
        self.Bind(wx.EVT_BUTTON, self.onAttachEdit, self.editAttachBtn)

        self.fromLbl.SetFont(font)
        self.toLbl.SetFont(font)
        self.subjectLbl.SetFont(font)

    def layoutWidgets(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        fromSizer = wx.BoxSizer(wx.HORIZONTAL)
        toSizer   = wx.BoxSizer(wx.HORIZONTAL)
        subjSizer = wx.BoxSizer(wx.HORIZONTAL)
        attachSizer = wx.BoxSizer(wx.HORIZONTAL)

        fromSizer.Add(self.fromLbl, 0)
        fromSizer.Add(self.fromTxt, 1, wx.EXPAND|wx.ALL)
        toSizer.Add(self.toLbl, 0)
        toSizer.Add(self.toTxt, 1, wx.EXPAND|wx.ALL)
        subjSizer.Add(self.subjectLbl, 0)
        subjSizer.Add(self.subjectTxt, 1, wx.EXPAND|wx.ALL)
        attachSizer.Add(self.attachBtn, 0, wx.ALL, 5)
        attachSizer.Add(self.attachTxt, 1, wx.ALL|wx.EXPAND, 5)
        attachSizer.Add(self.editAttachBtn, 0, wx.ALL, 5)

        mainSizer.Add(fromSizer, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(toSizer, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(subjSizer, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(attachSizer, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(self.messageTxt, 1, wx.ALL|wx.EXPAND, 5)        
        mainSizer.Add(self.url, 1, wx.ALL|wx.EXPAND, 5)
                
        self.panel.SetSizerAndFit(mainSizer)
        self.panel.SetAutoLayout(True)
        self.Fit()

    def parseURL(self, url):
        # split out the mailto
        sections = 1
        mailto_string = url.split(':')[1]               
        
        if '?' in mailto_string:
            sections = mailto_string.split('?')
        else:
            address = mailto_string
            
        if sections > 1:
            address = sections[0]
            new_sections = urllib.parse.unquote(sections[1]).split('&')
            for item in new_sections:
                if 'subject' in item.lower():
                    Subject = item.split('=')[1]
                    self.subjectTxt.SetValue(Subject)
                if 'body' in item.lower():
                    Body = item.split('=')[1]
                    self.messageTxt.SetValue(Body)
                    
        self.toTxt.SetValue(address)
                   
    def sendStrip(self, lst):
        string = ''
        for item in lst:
            item = item.strip()
            if string == '':
                string = string + item
            else:
                string = string + ';' + item 
        return string

    def onAttach(self, event):
        '''
        Displays a File Dialog to allow the user to choose a file
        and then attach it to the email.
        '''        
        attachments = self.attachTxt.GetLabel()
        filepath = ''

        # create a file dialog
        wildcard = _("All files (*.*)|*.*")
        dialog = wx.FileDialog(None, _('Choose a file'), self.currentDir,
                               '', wildcard, wx.OPEN)
        # if the user presses OK, get the path
        if dialog.ShowModal() == wx.ID_OK:
            self.attachTxt.Show()
            self.editAttachBtn.Show()
            filepath = dialog.GetPath()
            print(filepath)
            # Change the current directory to reflect the last dir opened
            os.chdir(os.path.dirname(filepath))
            self.currentDir = os.getcwd()
        

            # add the user's file to the filepath list
            if filepath != '':
                self.filepaths.append(filepath)

            # get file size
            fSize = self.getFileSize(filepath)
            
            # modify the attachment's label based on it's current contents
            if attachments == '':
                attachments = '%s (%s)' % (os.path.basename(filepath), fSize)
            else:
                temp = '%s (%s)' % (os.path.basename(filepath), fSize)
                attachments = attachments + '; ' + temp
            self.attachTxt.SetLabel(attachments)
        dialog.Destroy()

    def onAttachEdit(self, event):
        ''' Allow the editing of the attached files list '''
        print('in onAttachEdit...')
        attachments = ''
        
        dialog = EditDialog(self.filepaths)
        dialog.ShowModal()
        self.filepaths = dialog.filepaths
        print('Edited paths:\n', self.filepaths)
        dialog.Destroy()

        if self.filepaths == []:
            # hide the attachment controls
            self.attachTxt.Hide()
            self.editAttachBtn.Hide()
        else:
            for path in self.filepaths:
                # get file size
                fSize = self.getFileSize(path)
                # Edit the attachments listed
                if attachments == '':
                    attachments = '%s (%s)' % (os.path.basename(path), fSize)
                else:
                    temp = '%s (%s)' % (os.path.basename(path), fSize)
                    attachments = attachments + '; ' + temp            

            self.attachTxt.SetLabel(attachments)

    def getFileSize(self, f):
        ''' Get the file's approx. size '''
        fSize = os.stat(f).st_size
        if fSize >= 1073741824: # gigabyte
            fSize = int(math.ceil(fSize/1073741824.0))
            size = '%s GB' % fSize
        elif fSize >= 1048576:  # megabyte
            fSize = int(math.ceil(fSize/1048576.0))
            size = '%s MB' % fSize
        elif fSize >= 1024:           # kilobyte
            fSize = int(math.ceil(fSize/1024.0))
            size = '%s KB' % fSize
        else:
            size = '%s bytes' % fSize
        return size
    
    def OnSend(self, event):
        ''' Send the email using the filled out textboxes.
            Warn the user if they forget to fill part
            of it out.
        '''
                
        From = self.fromTxt.GetValue()
        To = self.toTxt.GetValue()
        Subject = self.subjectTxt.GetValue()
        text = self.messageTxt.GetValue()

        colon = To.find(';')
        period = To.find(',')
        if colon != -1:
            temp = To.split(';')
            To = self.sendStrip(temp) #';'.join(temp)
        elif period != -1:
            temp = To.split(',')
            To = self.sendStrip(temp) #';'.join(temp)
        else:
            pass

        if To == '':
            print('add an address to the "To" field!')
            dlg = wx.MessageDialog(None, _('Please add an address to the "To" field and try again'), _('Error'), wx.OK|wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()  
        elif Subject == '':
            dlg = wx.MessageDialog(None, _('Please add a "Subject" and try again'), _('Error'), wx.OK|wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        elif From == '':
            lg = wx.MessageDialog(None, _('Please add an address to the "From" field and try again'),
                                  _('Error'), wx.OK|wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()  
        else:            
            msg = MIMEMultipart()
            msg['From']    = From
            msg['To']      = To
            msg['Subject'] = Subject
            msg['Date']    = formatdate(localtime=True)
            msg.attach( MIMEText(text) )

            if self.filepaths:
                print('attaching file(s)...')
                for path in self.filepaths:
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload( open(path,"rb").read() )
                    Encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(path))
                    msg.attach(part)

            # edit this to match your mail server (i.e. mail.myserver.com)
            server = smtplib.SMTP('smtp.gmail.com:587')

            # open login dialog
            dlg = LoginDlg(server)

            res = dlg.ShowModal()
            if dlg.loggedIn:
                dlg.Destroy()   # destroy the dialog
                try:
                    failed = server.sendmail(From, To, msg.as_string())
                    server.quit()                    
                    self.Close()    # close the program
                except Exception as e:
                    print('Error - send failed!')
                    print(e)
                else:
                    if failed: print('Failed:', failed)
            else:
                dlg.Destroy()
        
    def OnClose(self, event):
        self.Close()
        
#############################################################################################################
class EditDialog(wx.Dialog):

    def __init__(self, filepaths):
        wx.Dialog.__init__(self, None, -1, _('Edit Attachments'), size=(190,150))

        self.filepaths = filepaths
        
        instructions = _('Check the items below that you no longer wish to attach to the email')
        lbl = wx.StaticText(self, wx.NewIdRef(), instructions)
        deleteBtn = wx.Button(self, wx.NewIdRef(), _('Delete Items'))
        cancelBtn = wx.Button(self, wx.NewIdRef(), _('Cancel'))

        self.Bind(wx.EVT_BUTTON, self.onDelete, deleteBtn)
        self.Bind(wx.EVT_BUTTON, self.onCancel, cancelBtn)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(lbl, 0, wx.ALL, 5)       
        
        self.chkList = wx.CheckListBox(self, wx.NewIdRef(), choices=self.filepaths)
        mainSizer.Add(self.chkList, 0, wx.ALL, 5)

        btnSizer.Add(deleteBtn, 0, wx.ALL|wx.CENTER, 5)
        btnSizer.Add(cancelBtn, 0, wx.ALL|wx.CENTER, 5)
        mainSizer.Add(btnSizer, 0, wx.ALL|wx.CENTER, 5)
        
        self.SetSizer(mainSizer)
        self.Fit()
        self.Layout()

    def onCancel(self, event):
        self.Close()

    def onDelete(self, event):
        numberOfPaths = len(self.filepaths)
        for item in range(numberOfPaths):            
            val = self.chkList.IsChecked(item)
            if val == True:
                path = self.chkList.GetString(item)
                print(path)
                for i in range(len(self.filepaths)-1,-1,-1):
                    if path in self.filepaths[i]:
                        del self.filepaths[i]
        print('new list => ', self.filepaths)
        self.Close()
                    
#######################################################################################
class LoginDlg(wx.Dialog):

    def __init__(self, server):
        wx.Dialog.__init__(self, None, -1, _('Gmail Account Login'), size=(200,150))
        self.server = server
        self.loggedIn = False

        # widgets
        userLbl = wx.StaticText(self, wx.NewIdRef(), _('Username:'), size=(70, -1))
        self.userTxt = wx.TextCtrl(self, wx.NewIdRef(), '', size=(150, -1))
        passwordLbl = wx.StaticText(self, wx.NewIdRef(), _('Password:'), size=(70, -1))
        self.passwordTxt = wx.TextCtrl(self, wx.NewIdRef(), '', size=(150, -1),
                                       style=wx.TE_PROCESS_ENTER|wx.TE_PASSWORD)
        loginBtn = wx.Button(self, wx.ID_YES, _('Login'))
        cancelBtn = wx.Button(self, wx.NewIdRef(), _('Cancel'))

        self.Bind(wx.EVT_BUTTON, self.OnLogin, loginBtn)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnter, self.passwordTxt)
        self.Bind(wx.EVT_BUTTON, self.OnClose, cancelBtn)

        # sizer / layout 
        userSizer     = wx.BoxSizer(wx.HORIZONTAL)
        passwordSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer      = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer     = wx.BoxSizer(wx.VERTICAL)

        userSizer.Add(userLbl, 0, wx.ALL, 5)
        userSizer.Add(self.userTxt, 0, wx.ALL, 5)
        passwordSizer.Add(passwordLbl, 0, wx.LEFT|wx.RIGHT, 5)
        passwordSizer.Add(self.passwordTxt, 0, wx.LEFT, 5)
        btnSizer.Add(loginBtn, 0, wx.ALL, 5)
        btnSizer.Add(cancelBtn, 0, wx.ALL, 5)
        mainSizer.Add(userSizer, 0, wx.ALL, 0)
        mainSizer.Add(passwordSizer, 0, wx.ALL, 0)
        mainSizer.Add(btnSizer, 0, wx.ALL|wx.CENTER, 5)

        self.SetSizerAndFit(mainSizer)
        self.Fit()
        self.Layout()
        
    def OnTextEnter(self, event):
        ''' When enter is pressed, login method is run. '''
        self.OnLogin('event')

    def OnLogin(self, event):
        '''
        When the "Login" button is pressed, the credentials are authenticated.
        If correct, the email will attempt to be sent. If incorrect, the user
        will be notified.
        '''
        try:
            user = self.userTxt.GetValue()
            pw   = self.passwordTxt.GetValue()
            self.server.starttls()
            self.server.ehlo()
            res = self.server.login(user, pw)
            self.loggedIn = True
            self.OnClose('')            
        except:
            message = _('Your username or password is incorrect. Please try again.')
            dlg = wx.MessageDialog(None, message, _('Login Error'), wx.OK|wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            
    def OnClose(self, event):
        self.Close()
        