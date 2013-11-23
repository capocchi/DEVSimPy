# -*- coding: utf-8 -*-

#!/usr/bin/python
# ­*­ coding: iso­8859­15 ­*­
import wx
ID_PLUS = 100
ID_MOINS = 101
phrase1 = u"Ramener l'imageà sa taille d'origine"
phrase2 = u"Opération interdite"
if not wx.USE_UNICODE:
        phrase1 = phrase1.encode("iso8859­15", "replace")
        phrase1 = phrase1.encode("iso8859­15", "replace")

class Visu(wx.ScrolledWindow):
        def __init__(self, conteneur):
                wx.ScrolledWindow.__init__(self,parent = conteneur)
                self.bmp = None
                self.image = None

        def Affiche(self, bmp, ratio):
                if self.bmp != None:
                        posX, posY = self.GetViewStart()
                        self.image.Destroy()
                        self.SetScrollRate(0, 0)
                else:
                        posX = 0
                        posY = 0
                        self.bmp = bmp
                        self.SetVirtualSize(wx.Size(bmp.GetWidth(), bmp.GetHeight()))
                        self.image = wx.StaticBitmap(self, 1, self.bmp)
                        self.SetScrollRate((10*ratio)/100, (10*ratio)/100)
                        self.Scroll(posX, posY)
                        self.Refresh()

        def Efface(self):
                self.image.Destroy()
                self.bmp = None
                self.SetScrollRate(0, 0)

class Principale(wx.Frame):
        def __init__(self, titre):
                wx.Frame.__init__(self, None,1, title = titre, size = (499, 399))
                self.imgORIG = None
                self.imgORIX = 0
                self.imgORIY = 0
                self.bmpRESU = None
                self.ratio = 100
                self.inc = 5
                menuFichier = wx.Menu(style = wx.MENU_TEAROFF)
                menuFichier.Append(wx.ID_OPEN, "&Ouvrir\tCTRL+o", "Ouvrir un fichier image")
                menuFichier.Append(wx.ID_CLOSE,"&Fermer\tCTRL+f", "Fermer le fichier ouvert")
                menuFichier.AppendSeparator()
                menuFichier.Append(wx.ID_EXIT, "&Quitter\tCTRL+q", "Quitter l'application")
                menuAfficher = wx.Menu(style = wx.MENU_TEAROFF)
                menuAfficher.Append(wx.ID_UNDO,"&Taille d'origine\tCTRL+t",phrase1)
                menuAfficher.Append(ID_PLUS, "&Agrandir\tCTRL+a", "Agrandir l'image")
                menuAfficher.Append(ID_MOINS, "&Diminuer\tCTRL+a", "Diminuer l'image")
                menuBarre = wx.MenuBar()
                menuBarre.Append(menuFichier, "&Fichier")
                menuBarre.Append(menuAfficher, "&Afficher")
                self.SetMenuBar(menuBarre)
                self.barre = wx.StatusBar(self,1)
                self.barre.SetFieldsCount(2)

                self.barre.SetStatusWidths([1,1])
                self.SetStatusBar(self.barre)
                outils = wx.ToolBar(self,1,style = wx.TB_HORIZONTAL | wx.NO_BORDER)
                outils.AddSimpleTool(wx.ID_OPEN,wx.Bitmap("E:\DEVSSIMPY\DEVSIMPY200510\Python2_6\Domain\Myths\cartes\corse.png", wx.BITMAP_TYPE_PNG),shortHelpString = "Ouvrir",longHelpString = "Ouvrir un fichier image")
                outils.AddSimpleTool (wx.ID_CLOSE,wx.Bitmap("E:\DEVSSIMPY\DEVSIMPY200510\Python2_6\Domain\Myths\cartes\corse.png", wx.BITMAP_TYPE_PNG),shortHelpString = "Fermer",longHelpString = "Fermer le fichier ouvert")
                outils.AddSeparator()
                outils.AddSimpleTool(wx.ID_UNDO,wx.Bitmap("E:\DEVSSIMPY\DEVSIMPY200510\Python2_6\Domain\Myths\cartes\corse.png", wx.BITMAP_TYPE_PNG),shortHelpString = "Taille originale",longHelpString = phrase1)
                outils.AddSimpleTool(ID_PLUS,wx.Bitmap("E:\DEVSSIMPY\DEVSIMPY200510\Python2_6\Domain\Myths\cartes\corse.png", wx.BITMAP_TYPE_PNG),shortHelpString = "Agrandir",longHelpString = "Agrandir l'image")
                outils.AddSimpleTool(ID_MOINS,wx.Bitmap("E:\DEVSSIMPY\DEVSIMPY200510\Python2_6\Domain\Myths\cartes\corse.png", wx.BITMAP_TYPE_PNG),shortHelpString = "Diminuer",longHelpString = "Diminuer l'image")
                outils.AddSeparator()
                outils.AddSimpleTool(wx.ID_EXIT,wx.Bitmap("E:\DEVSSIMPY\DEVSIMPY200510\Python2_6\Domain\Myths\cartes\corse.png", wx.BITMAP_TYPE_PNG),shortHelpString = "Quitter",longHelpString = "Quitter l'application")
                #outils.Realize()
                self.SetToolBar(outils)
                sizer = wx.BoxSizer()
                self.panneau = Visu(self)
                sizer.Add(self.panneau, 1, wx.EXPAND|wx.ALL, 2)
                self.SetSizer(sizer)
                wx.EVT_MENU(self, wx.ID_OPEN, self.OnOpen)
                wx.EVT_MENU(self, wx.ID_CLOSE, self.OnClose)
                wx.EVT_MENU(self, wx.ID_EXIT, self.OnExit)
                wx.EVT_MENU(self, wx.ID_UNDO, self.Retour)
                wx.EVT_MENU(self, ID_PLUS, self.Plus)
                wx.EVT_MENU(self, ID_MOINS, self.Moins)

        def Retour(self, evt):
                if self.imgORIG != None:
                        self.ratio = 100
                        self.bmpRESU = self.imgORIG.ConvertToBitmap()
                        self.panneau.Affiche(self.bmpRESU, self.ratio)
                        self.barre.SetStatusText("(%s, %s) %s %%"%(self.imgORIX,self.imgORIY, self.ratio), 1)

        def Plus(self, evt):
                if self.imgORIG != None:
                        self.ratio = self.ratio + self.inc
                        largeur = (self.imgORIX * self.ratio)/100
                        hauteur = (self.imgORIY * self.ratio)/100
                        self.bmpRESU = self.imgORIG.Scale(largeur, hauteur).ConvertToBitmap()
                        self.panneau.Affiche(self.bmpRESU, self.ratio)
                        self.barre.SetStatusText("(%s, %s) %s %%"%(self.imgORIX, self.imgORIY, self.ratio), 1)

        def Moins(self, evt):
                if self.ratio > 5 and self.imgORIG != None:
                        self.ratio = self.ratio-self.inc
                        largeur = (self.imgORIX * self.ratio)/100
                        hauteur = (self.imgORIY * self.ratio)/100
                        self.bmpRESU = self.imgORIG.Scale(largeur, hauteur).ConvertToBitmap()
                        self.panneau.Affiche(self.bmpRESU, self.ratio)
                        self.barre.SetStatusText("(%s, %s) %s %%"%(self.imgORIX,self.imgORIY, self.ratio), 1)

        def OnOpen(self, evt):
                if self.imgORIG != None :
                        dlg = wx.MessageDialog(self,"Vous devez d'abord fermer l'image en cours d'utilisation",phrase2, style = wx.OK)
                        retour = dlg.ShowModal()
                        dlg.Destroy()
                else:
                        dlg = wx.FileDialog(self, "Choisissez un fichier",wildcard = "*.*",style = wx.OPEN)
                        retour = dlg.ShowModal()
                        chemin = dlg.GetPath()
                        fichier = dlg.GetFilename()
                        dlg.Destroy()
                        if retour == wx.ID_OK and fichier != "":
                                self.imgORIG = wx.Image(chemin, wx.BITMAP_TYPE_ANY)
                                self.imgORIX = self.imgORIG.GetWidth()
                                self.imgORIY = self.imgORIG.GetHeight()
                                self.bmpRESU = self.imgORIG.ConvertToBitmap()
                                self.panneau.Affiche(self.bmpRESU, self.ratio)
                                self.SetTitle("Visualiseur d'images [%s]"% fichier)
                                self.barre.SetStatusText("(%s, %s) %s %%"%(self.imgORIX,self.imgORIY, self.ratio), 1)

        def OnClose(self, evt):
                if self.imgORIG != None :
                        self.panneau.Efface()
                        self.imgORIG = None
                        self.imgORIX = 0
                        self.imgORIY = 0
                        self.bmpRESU = None
                        self.ratio = 100
                        self.SetTitle("Visualiseur d'images")
                        self.barre.SetStatusText("", 1)
                                                
        def OnExit(self, evt):
                self.Destroy()


class MonApp(wx.App):
        def OnInit(self):
                wx.InitAllImageHandlers()
                fen = Principale("Visualiseur d'images")
                fen.Show(True)
                self.SetTopWindow(fen)
                return True

app = MonApp()

app.MainLoop()                   
                        
