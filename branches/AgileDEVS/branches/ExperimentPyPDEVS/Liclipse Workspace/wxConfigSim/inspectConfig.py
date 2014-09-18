import inspect
import sys
import os
import json
import wx
from wx import xrc

sys.path.append('C:\\Users\\fj\Desktop\\version-2.8\\DEVSKernel\\PyPDEVS\\pypdevs221\\src')
from simconfig import SimulatorConfiguration


class SimConfigApp(wx.App):

    def OnInit(self):
        self.booleanConfigJSON={}
        self.booleanConfigDefault={}
        self.booleanConfig={}
        self.listCheckBox=[]

        self.res = xrc.XmlResource("XRC\\configSim.xrc")
        self.InitFrame()
        return True


    def InitFrame(self):
        self.frame = self.res.LoadFrame(None, "simConfigFrame")
        self.pan_booleans = xrc.XRCCTRL(self.frame, "pan_booleans")
        self.bs_booleans = wx.BoxSizer( wx.VERTICAL )
        self.pan_booleans.SetSizer(self.bs_booleans)
        self.addBooleanOptions()

        self.bt_reinit = xrc.XRCCTRL(self.frame, "bt_reinit")
        self.bt_reinit.Bind( wx.EVT_BUTTON, self.evt_click_reinit )

        self.bt_valider = xrc.XRCCTRL(self.frame, "bt_valider")
        self.bt_valider.Bind( wx.EVT_BUTTON, self.evt_click_validate )

        self.frame.Show()


    #Evenements
    def evt_cb_change( self, event ):
        option = list(self.booleanConfigDefault[event.GetId()])
        option[2] = event.EventObject.Value
        cb_id = event.GetId()
        self.booleanConfig[cb_id]=option
        if self.booleanConfig[cb_id][2] == self.booleanConfigDefault[cb_id][2]:
            del self.booleanConfig[cb_id]


    def evt_click_reinit( self, event ):
        for cb in self.listCheckBox:
            cb_id = cb.GetId()
            cb.SetValue(self.booleanConfigDefault[cb_id] [2])
        self.booleanConfig={}


    def evt_click_validate( self, event ):
        self.booleanConfigJSON = json.dumps(self.booleanConfig.values())
        print self.booleanConfigJSON

    def addBooleanOptions(self):
        simConf = SimulatorConfiguration(None)
        for i in inspect.getmembers(simConf):
            methodName = i[0]
            objMeth = i[1]
            if inspect.ismethod(objMeth):
                inspectResult = inspect.getargspec(objMeth)
                if len(inspectResult[0])>1: #Si la methode a des arguments (autres que self)
                    if inspectResult[3]!=None and isinstance(inspectResult[3][0], bool): #Si il y a une valeur par defaut et qu'elle est de type bool
                        argName=inspectResult[0][1]
                        argDefault=inspectResult[3][0]
                        m_cb = wx.CheckBox(self.pan_booleans, wx.ID_ANY, methodName, wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT)
                        m_cb.SetValue(inspectResult[3][0])
                        m_cb.Bind( wx.EVT_CHECKBOX, self.evt_cb_change )
                        self.listCheckBox.append(m_cb)
                        self.bs_booleans.Add(m_cb, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)
                        self.booleanConfigDefault[m_cb.GetId()]=[methodName, argName, argDefault]
        self.pan_booleans.Layout()


if __name__ == '__main__':
    app = SimConfigApp()
    app.MainLoop()