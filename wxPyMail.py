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

import mail_ico
import math
import os
import smtplib
import sys
import urllib
import wx

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email import Encoders

from email.Message import Message

class SendMailWx(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, _('New Email Message (From Google account)'),
                          size=(600,400))
        self.panel = wx.Panel(self, wx.ID_ANY)

        # set your email address here
        self.email = 'your_email@gmail.com'

        self.filepaths = []
        self.currentDir = os.getcwd()
        
        self.createMenu()
        self.createToolbar()
        self.createWidgets()
#        try:
#            print sys.argv
#            self.parseURL(sys.argv[1])
#        except Exception, e:
#            print 'Unable to execute parseURL...'
#            print e
        
        self.layoutWidgets()
        
        self.attachTxt.Hide()
        self.editAttachBtn.Hide()

    def createMenu(self):
        menubar = wx.MenuBar()
        
        fileMenu = wx.Menu()
        send_menu_item = fileMenu.Append(wx.NewId(), _('&Send'), _('Sends the email'))
        close_menu_item = fileMenu.Append(wx.NewId(), _('&Close'), _('Closes the window'))
        menubar.Append(fileMenu, _('&File'))
        self.SetMenuBar(menubar)

        # bind events to the menu items
        self.Bind(wx.EVT_MENU, self.OnSend, send_menu_item)
        self.Bind(wx.EVT_MENU, self.OnClose, close_menu_item)

    def createToolbar(self):
        toolbar = self.CreateToolBar(wx.TB_3DBUTTONS|wx.TB_TEXT)
        toolbar.SetToolBitmapSize((31,31))
        bmp = mail_ico.getBitmap()
        sendTool = toolbar.AddTool(-1, _('Send'), bmp, _('Sends Email'))
        self.Bind(wx.EVT_MENU, self.OnSend, sendTool)        
        toolbar.Realize()

    def createWidgets(self):
        p = self.panel
              
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.fromLbl    = wx.StaticText(p, wx.ID_ANY, _('From'), size=(60,-1))
        self.fromTxt    = wx.TextCtrl(p, wx.ID_ANY, self.email)
        self.toLbl      = wx.StaticText(p, wx.ID_ANY, _('To:'), size=(60,-1))
        self.toTxt      = wx.TextCtrl(p, wx.ID_ANY, 'capocchi_l@univ-corse.fr')
        self.subjectLbl = wx.StaticText(p, wx.ID_ANY, _(' Subject:'), size=(60,-1))
        self.subjectTxt = wx.TextCtrl(p, wx.ID_ANY, '')
        self.attachBtn  = wx.Button(p, wx.ID_ANY, _('Attachments'))        
        self.attachTxt  = wx.TextCtrl(p, wx.ID_ANY, '', style=wx.TE_MULTILINE)
        self.attachTxt.Disable()
        self.editAttachBtn = wx.Button(p, wx.ID_ANY, _('Edit Attachments'))
        
        self.messageTxt = wx.TextCtrl(p, wx.ID_ANY, '', style=wx.TE_MULTILINE)

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
        fromSizer.Add(self.fromTxt, 1, wx.EXPAND)
        toSizer.Add(self.toLbl, 0)
        toSizer.Add(self.toTxt, 1, wx.EXPAND)
        subjSizer.Add(self.subjectLbl, 0)
        subjSizer.Add(self.subjectTxt, 1, wx.EXPAND)
        attachSizer.Add(self.attachBtn, 0, wx.ALL, 5)
        attachSizer.Add(self.attachTxt, 1, wx.ALL|wx.EXPAND, 5)
        attachSizer.Add(self.editAttachBtn, 0, wx.ALL, 5)

        mainSizer.Add(fromSizer, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(toSizer, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(subjSizer, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(attachSizer, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(self.messageTxt, 1, wx.ALL|wx.EXPAND, 5)        
        self.panel.SetSizer(mainSizer)
        self.panel.Layout()

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
            new_sections = urllib.unquote(sections[1]).split('&')
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
            print filepath
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
        print 'in onAttachEdit...'
        attachments = ''
        
        dialog = EditDialog(self.filepaths)
        dialog.ShowModal()
        self.filepaths = dialog.filepaths
        print 'Edited paths:\n', self.filepaths
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
            print 'add an address to the "To" field!'
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

            if self.filepaths != []:
                print 'attaching file(s)...'
                for path in self.filepaths:
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload( open(path,"rb").read() )
                    Encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(path))
                    msg.attach(part)

            # edit this to match your mail server (i.e. mail.myserver.com)
            server = smtplib.SMTP('smtp.gmail.com',587)

            # open login dialog
            dlg = LoginDlg(server)
            res = dlg.ShowModal()
            if dlg.loggedIn:
                dlg.Destroy()   # destroy the dialog
                try:
                    failed = server.sendmail(From, To, msg.as_string())
                    server.quit()                    
                    self.Close()    # close the program
                except Exception, e:
                    print 'Error - send failed!'
                    print e
                else:
                    if failed: print 'Failed:', failed
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
        lbl = wx.StaticText(self, wx.ID_ANY, instructions)
        deleteBtn = wx.Button(self, wx.ID_ANY, _('Delete Items'))
        cancelBtn = wx.Button(self, wx.ID_ANY, _('Cancel'))

        self.Bind(wx.EVT_BUTTON, self.onDelete, deleteBtn)
        self.Bind(wx.EVT_BUTTON, self.onCancel, cancelBtn)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(lbl, 0, wx.ALL, 5)       
        
        self.chkList = wx.CheckListBox(self, wx.ID_ANY, choices=self.filepaths)
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
        print 'in onDelete'
        numberOfPaths = len(self.filepaths)
        for item in range(numberOfPaths):            
            val = self.chkList.IsChecked(item)
            if val == True:
                path = self.chkList.GetString(item)
                print path
                for i in range(len(self.filepaths)-1,-1,-1):
                    if path in self.filepaths[i]:
                        del self.filepaths[i]
        print 'new list => ', self.filepaths
        self.Close()
                    
#######################################################################################
class LoginDlg(wx.Dialog):

    def __init__(self, server):
        wx.Dialog.__init__(self, None, -1, _('Gmail Account Login'), size=(190,150))
        self.server = server
        self.loggedIn = False

        # widgets
        userLbl = wx.StaticText(self, wx.ID_ANY, _('Username:'), size=(50, -1))
        self.userTxt = wx.TextCtrl(self, wx.ID_ANY, '', size=(150, -1))
        passwordLbl = wx.StaticText(self, wx.ID_ANY, _('Password:'), size=(50, -1))
        self.passwordTxt = wx.TextCtrl(self, wx.ID_ANY, '', size=(150, -1),
                                       style=wx.TE_PROCESS_ENTER|wx.TE_PASSWORD)
        loginBtn = wx.Button(self, wx.ID_YES, _('Login'))
        cancelBtn = wx.Button(self, wx.ID_ANY, _('Cancel'))

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

        self.SetSizer(mainSizer)
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
            self.server.ehlo()
            self.server.starttls()
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
        
#######################################################################################

# Start program
if __name__ == '__main__':
    app = wx.App()
    frame = SendMailWx()
    frame.Show()
    app.MainLoop() 