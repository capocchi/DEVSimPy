# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Container.py ---
#                     --------------------------------
#                        Copyright (c) 2009
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 11/01/10
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

try:
	import wxversion
	wxversion.select('2.8')
except:
	pass

import wx
import wx.lib.dragscroller
import wx.aui
import  wx.lib.filebrowsebutton as filebrowse
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, TextEditMixin
import  wx.grid as gridlib
import os
import sys
import copy
import inspect
import linecache
import cPickle
import gzip
import tarfile
from tempfile import gettempdir
from urlparse import urlparse
import shutil
from random import randint
import xml.etree.ElementTree as ET

import __builtin__

for root, dirs, files in os.walk(os.pardir+os.sep):
	sys.path.append(os.path.abspath(root))

from SpreadSheet import *
from Editor import Editor
from ConnectDialog import *
from Plot import Plot
from SimulationGUI import *
from PriorityGUI import PriorityGUI
from DiagramConstantsDialog import DiagramConstantsDialog
from WizardGUI import ModelGeneratorWizard
from Domain.Basic import *
from DomainInterface.MasterModel import *
from DomainInterface.DomainBehavior import *
from DomainInterface.DomainStructure import *

#Global Stuff -------------------------------------------------
clipboard = []

PORT_RESOLUTION = True

##############################################################
#															 #
# GENERAL fUNCTIONS											 #
#															 #
##############################################################

_ = wx.GetTranslation

def PathToModule(abs_python_filename):
	
	# delete extention if exist
	abs_python_filename = os.path.splitext(abs_python_filename)[0]
	
	## si Domain est dans le chemin du module à importer (le fichier .py est dans un sous repertoire du rep Domain)
	if DOMAIN_DIR in abs_python_filename.split(os.sep):
		path = str(abs_python_filename[abs_python_filename.index(DOMAIN_DIR):]).strip('[]').replace(os.sep,'.')
	else:
		path = os.path.basename(abs_python_filename).replace(os.sep,'.')

		### Ajout du chemin dans le path pour l'import d'un lib exterieur
		domainPath = os.path.dirname(abs_python_filename)

		if domainPath not in sys.path:
			sys.path.append(domainPath)

		# si commence par . (transfo de /) supprime le
		if path.startswith('.'):
			path = path[1:]
		
	return path

def GetClassMember(python_file = ''):
	""" Get class member from python file
	"""
		
	module = PathToModule(python_file)

	# import module 
	try:
		exec "import %s"%(str(module))
	except Exception, info:
		sys.stderr.write(_("Import Error : %s\n"%info))
		return False

	# classes composing the imported module
	clsmembers = dict(inspect.getmembers(sys.modules[str(module)], inspect.isclass))

	return clsmembers

def GetPythonClass(python_file = ''):
	""" Get python class from filename.
	"""

	module = PathToModule(python_file)
	clsmembers = GetClassMember(python_file)

	for cls in clsmembers.values(): 
		if str(cls.__module__) == str(module):
			return cls

def GetArgs(cls = None):
	""" Get behavioral attribute from python file through constructor class.
	"""

	constructor = inspect.getargspec(cls.__init__)
	return dict(zip(constructor.args[1:], constructor.defaults)) if constructor.defaults != None else {}
	
	
def GetDEVSModel(abs_python_filename = '', args = {}):
	""" Function that return DEVS model from python file path.
	"""
	
	path = PathToModule(abs_python_filename)

	# try to import module. Necessary for sys.module
	try:
		exec "import %s"%(str(path))
	except Exception, info:
		sys.stderr.write(_("Import Error: %s\n"%info))
		return False

	# classes composing the imported module
	clsmembers = dict(inspect.getmembers(sys.modules[str(path)], inspect.isclass))

	# instanciate only the class corresponding to the module imported (note DomainStructure, Message, ...)
	for classe in clsmembers.values():
		if str(classe.__module__) == str(path):
			return apply(eval(str(classe)), (), args)

def BuzyCursorNotification(f):
	""" Decorator which give the buzy cursor for long process
	"""
	def wrapper(*args):
			wx.BeginBusyCursor()
			wx.Yield()
			r =  f(*args)
			wx.EndBusyCursor()
			return r
	return wrapper	

# allows  arguments for a decorator
decorator_with_args = lambda decorator: lambda *args, **kwargs: lambda func: decorator(func, *args, **kwargs)

@decorator_with_args
def StatusBarNotification(f, arg):
	""" Decorator which give information into status bar for the load and the save diagram operations
	"""
	
	def wrapper(*args):
		
		#print dir(args[0].func_globals)
		fn = os.path.basename(args[-1])
		txt = arg
		
		# main window
		mainW = wx.GetApp().GetTopWindow()
		mainW.statusbar.SetStatusText(_('%sing %s ...'%(txt,fn)), 0)
		r = f(*args)
		mainW.statusbar.SetStatusText(_('%s %sed'%(fn, txt)), 0)
		mainW.statusbar.SetStatusText('', 1)
		mainW.statusbar.SetStatusText('', 2)
		return r

	return wrapper

################################################################
#															   #
# GENERAL CLASS												   #
#															   #
################################################################

class TextDrop(wx.PyDropTarget):
	""" TextDrop(canvas)
	""" 
	SOURCE = None

	def __init__(self, canvas = None):
		""" Constructor 
		"""

		wx.PyDropTarget.__init__(self)
		
		## dans le constructeur de l'application principale toujours initialiser la source du DnD
		assert(TextDrop.SOURCE != None)

		##local copy
		self.canvas = canvas
		self.nb = TextDrop.SOURCE

		self.setDo()

		
	def setDo(self):
		""" 
		"""

		# allows several drop format
		self.do = wx.DataObjectComposite()
		# file names
		self.fdo= wx.FileDataObject()
		self.do.Add(self.fdo)
		# text
		self.tdo= wx.TextDataObject()
		self.do.Add(self.tdo)
		
		self.SetDataObject(self.do)


	def OnData(self, *args):
		"""
		"""

		if self.GetData():
			#droped filenames and text
			filenames = self.fdo.GetFilenames()
			text = self.tdo.GetText()
			self.setDo()

			# mouse position
			x = args[0]
			y = args[1]

			# if text is not void, then the list is empty and we can add the text filename
			if text != "":
				filenames.append(text)

			# for all of the filename of selected files in the explorer
			for absFileName in filenames:
				# text is the filename and ext its extention
				text,ext=os.path.splitext(absFileName)
				# label is the file name
				label = os.path.basename(text)
				## Droped file extension is .dsp
				if ext == '.dsp':
					# its possible to use the orignal copy of the droped diagram
					dial = wx.MessageDialog(self, _('Do You want to open the orignal diagram in a new tab ?'), 'Question', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
					# load diagram in a new page
					if (dial.ShowModal() == wx.ID_YES):
						
						mainW = self.canvas.GetTopLevelParent()
						diagram = ContainerBlock()
						diagram.last_name_saved = absFileName
						
						if diagram.LoadFile(absFileName):
							mainW.nb2.AddEditPage('%s%s'%(label,ext),diagram)
							# status bar
							mainW.statusbar.SetStatusText('', 1)
						else:
							dlg = wx.MessageDialog(mainW, _('Error opening file\n'))
							dlg.ShowModal()
					#load the diagram in the current page
					else:
						diagram = self.canvas.GetDiagram()

						if not diagram.LoadFile(absFileName):
							dlg = wx.MessageDialog(self, _('Error opening file\n'))
							dlg.ShowModal()
				else:
		
					if ext == '.cmd':

						# nouveau model couple
						m = ContainerBlock(label)

						# attention on ne serialise pas le coupled devs, donc obligé de lui donner une instance vierge (de toute facon pas de ocde dans le coupled)
						m.AddCoupledModel(Coupled.Coupled())
						
						try:
							m.LoadFile(absFileName)
						
						except Exception, info:
							dial = wx.MessageDialog(None, _('Error loading cmd model : %s'%info), _('Error'), wx.OK | wx.ICON_ERROR)
							dial.ShowModal()
							return
						else:

							# coupled input ports
							m.input=0
							m.output=0
							for s in m.shapes:
								if isinstance(s,iPort):
									m.input +=1
								elif isinstance(s,oPort):
									m.output +=1

							# initial position
							m.move(x-50*self.canvas.scalex, y-50*self.canvas.scaley)

					elif  ext == '.amd':

						# New codeBlock model
						tmp = CodeBlock(label)
						
						try:
							m = tmp.LoadFile(absFileName)
						except Exception, info:
							dial = wx.MessageDialog(None, _('Error loading amd model : %s '%info), _('Error'), wx.OK | wx.ICON_ERROR)
							dial.ShowModal()
							return
						else:
							m.x = tmp.x
							m.y = tmp.y
							m.label = label

							m.move(x-50*self.canvas.scalex, y-50*self.canvas.scaley)
					# .py
					else:
						
						# block instance
						m = self.GetBlockModel( x = x,
												y = y, 
												label = os.path.basename(text),
												python_file = '%s.py'%text)

					if (m):
						#deselect all modeles
						self.canvas.deselect()
						# Adding graphical model to diagram
						self.canvas.AddShape(m)
						# Select m shape
						self.canvas.select(m)

						sys.stdout.write(_("Adding DEVSimPy model: \n").encode('utf-8'))
						sys.stdout.write(repr(m))

			# canvas refresh and focus
			self.canvas.Refresh()
			self.canvas.SetFocus()
	
	def GetBlockModel(self, *argv, **kwargs):
		""" Function that set block model knowing devs model.

			Warning: the class must derive from a class named with DomainBehavior or DomainStructure substring
		"""

		# local copy
		x = kwargs['x']
		y = kwargs['y']
		label = kwargs['label']
		iid = kwargs['id'] if kwargs.has_key('id') else self.canvas.diagram.GetiPortCount()
		oid = kwargs['id'] if kwargs.has_key('id') else self.canvas.diagram.GetoPortCount()
		inputs = kwargs['inputs'] if kwargs.has_key('inputs') else 1
		outputs = kwargs['outputs'] if kwargs.has_key('outputs') else 1
		python_file = kwargs['python_file']
		model_file = kwargs['model_file'] if kwargs.has_key('model_file') else ''

		# associated python class
		clsmbr = GetClassMember(python_file)

		#all class name into string sperated by --
		all_class_to_string = '--'.join(clsmbr.keys())

		# adding devs model on good graphical model
		if clsmbr.has_key('DomainBehavior') or 'DomainBehavior' in all_class_to_string:
			
			# new codeBlcok instance (to improve !)
			if clsmbr.has_key('To_Disk'):
				m = DiskGUI(label)
			elif clsmbr.has_key('QuickScope'):
				m = ScopeGUI(label)
			elif clsmbr.has_key('ExternalGen'):
				m = ExternalGenGUI(label)
			else:
				m = CodeBlock(label, inputs, outputs)
		
			# define behavioral args from python classe
			m.args = GetArgs(GetPythonClass(python_file))

			# get python file path for import during simulation
			m.python_path = python_file

			# move model from mouse position
			m.move(x-50*self.canvas.scalex, y-50*self.canvas.scaley)
			
		elif clsmbr.has_key('DomainStructure') or 'DomainStructure' in all_class_to_string:
			
			# new containerBlock model
			m = ContainerBlock(label, inputs, outputs)
			
			# input and output ports
			for i in range(inputs):
				id = self.canvas.diagram.nbiPort+i
				iport = iPort(label='IPort %d'%(id))
				iport.id = id
				m.AddShape(iport)

			for o in range(outputs):
				id = self.canvas.diagram.nboPort+o
				oport = oPort(label='OPort %d'%(id))
				oport.id = id
				m.AddShape(oport)
			
			m.python_path = python_file

			m.move(x-50*self.canvas.scalex, y-50*self.canvas.scaley)

		elif clsmbr.has_key('IPort'):
			m = iPort(label="%s %d"%(label,iid))
			m.id=iid
			m.move(x-70, y-70)

		elif clsmbr.has_key('OPort'):
			#id = self.canvas.diagram.GetoPortCount()
			m = oPort(label="%s %d"%(label,oid))
			m.id=oid
			m.move(x-70, y-70)

		else:
		
			dial = wx.MessageDialog(None, _('Object not instantiated !'), _('Exclamation'), wx.OK | wx.ICON_EXCLAMATION)
			dial.ShowModal()
			return False
		
		return m

#---------------------------------------------------------
class Savable:
	""" Savable class that allows methods to save and load diagram into file.
	"""

	###
	def __init__(self):
		""" Constructor.
		"""
		self.last_name_saved = ''

	def SaveFile(self, fileName = None):
		""" Save into fileName
		"""
		pass

	def LoadFile(self, fileName = None):
		""" Load from fileName
		"""
		pass
		
#-------------------------------------------------------------
class Diagram(Savable):
	""" Diagram class.
	"""

	def __init__(self):
		""" Constructor.
		"""

		Savable.__init__(self)

		# list of shapes in the diagram
		self.shapes = []
		
		# shape priority for simulation
		self.priority_list = []

		# constants dico
		self.constants_dico = {}

		# list of number of Block and Port under the diagram
		self.nbCodeBlock = 0
		self.nbContainerBlock = 0
		self.nbiPort = 0
		self.nboPort = 0

		# list of deleted id
		self.deletedCodeBlockId = []		
		self.deletedContainerBlockId = []
		self.deletediPortId = []
		self.deletedoPortId = []

		self.modify = False

	@BuzyCursorNotification 
	@StatusBarNotification("Sav")
	def SaveFile(self, fileName):
		""" Function that save the diagram into a file.
		"""
	
		if fileName is None:
			return False

		try:
			L = [self.shapes, self.priority_list, self.constants_dico, self.python_path]

			f = gzip.GzipFile(filename = fileName, mode = 'wb', compresslevel = 9)
			cPickle.dump(L,f)
			f.close()
		except Exception, info:
			sys.stderr.write(_("Problem saving: %s -- %s\n")%(str(fileName),info))
			return False
		else:
			return True

	@BuzyCursorNotification
	@StatusBarNotification("Load")
	def LoadFile(self, fileName = None):
		""" Function that load diagram from a file.
		"""

		if fileName is None:
			return False

		# try to open f with compressed mode
		try:
			f = gzip.GzipFile(filename = fileName, mode='rb')
			f.read(1) # trigger an exception if is not compressed
			f.seek(0)
		except IOError:
			# not compressed file
			try:
				f = open(fileName,'rb')
			except Exception, info:
				sys.stderr.write(_("Problem opening: %s -- %s \n")%(str(fileName),info))
				return False
		
		# try to load file
		try:

			self.shapes, self.priority_list, self.constants_dico, self.python_path = cPickle.load(f)
	
		except Exception, info:
			sys.stderr.write(_("Problem loading: %s -- %s \n")%(str(fileName),info))
			return False

		else:

			# load constants (like Rs, Lms...) into the general builtin (to use it, <title>['Lms'] into the expr) 
			if self.constants_dico != {}:
				# give title by basename of filename
				title = os.path.splitext(os.path.basename(fileName))[0]
				# load constants into the general builtin
				self.LoadConstants(title)

			return True

	@StatusBarNotification("Load")
	def LoadConstants(self, label):
		""" Load Constants to general builtin.
		"""
		__builtin__.__dict__[os.path.splitext(label)[0]] = self.constants_dico

	def OnPriority(self, parent):
		""" Method that show the priorityGUI frame in order to define the activation priority of components 
		"""
		
		#list of all components
		if self.priority_list == []:
			self.priority_list=[s for s in filter(lambda c: isinstance(c, Block),self.GetShapeList())]
		dlg = PriorityGUI(parent, wx.ID_ANY, "Priority", [s.label for s in self.priority_list])
		dlg.Bind(wx.EVT_CLOSE,self.OnClosePriorityGUI)
		dlg.Show()


	def OnClosePriorityGUI(self, event):
		""" Method that update the self.priority_list and close the priorityGUI Frame
		"""

		obj = event.GetEventObject()
		#update list of imminent component
		self.priority_list = [self.GetShapeByLabel(obj.listCtrl.GetItemText(i)) for i in range(obj.listCtrl.GetItemCount())]
		obj.Destroy()


	def AddConstants(self, parent):
		""" Method that add constant parameters in order to simplify the modling codeBlock model
		"""

		mainW = wx.GetApp().GetTopWindow()
		title = mainW.nb2.GetPageText(mainW.nb2.GetSelection())
		dlg = DiagramConstantsDialog(mainW, wx.ID_ANY, title, self)
		dlg.Show()

	def makeDEVSGraph(self, diagram = None, D = {}, type = object):
		""" Make a formated dictionnary to make the graph of the DEVS Network : {'S1': [{'C1': (1, 0)}, {'M': (0, 1)}], port 1 of S1 is connected to the port 0 of C1...
		"""

		# for all components in the diagram
		for c in diagram.GetShapeList():
			# if the component is the conncetionShape, then add the new element in the D dictionnary
			if isinstance(c, ConnectionShape):
				model1, portNumber1 = c.input	
				model2, portNumber2 = c.output
				
				# but if the model1 is a port, then make the correspondance with the parent coupled model
				#if isinstance(model1, Port):
					#label1 = diagram.label
					#portNumber1 = model1.id

				# return D with object representation 
				if type == object:
					# Now add or update the new element in the dico D
					if D.has_key(model2):
						D[model2].append({model1: (portNumber2 ,portNumber1)})
					else:
						D[model2] = [{model1: (portNumber2 ,portNumber1)}]

					if isinstance(model1, iPort) or isinstance(model1, oPort):
						if D.has_key(model1):
							D[model1].append({model2: (portNumber1 ,portNumber2)})
						else:
							D[model1] = [{model2: (portNumber1 ,portNumber2)}]

				# return D with string representation
				else:
					label1 = model1.label
					label2 = model2.label

					if D.has_key(label2):
						D[label2].update({label1: (portNumber2 ,portNumber1)})
					else:
						D[label2] = {label1: (portNumber2 ,portNumber1)}

					if isinstance(model1, iPort) or isinstance(model1, oPort):
						if D.has_key(label1):
							D[label1].update({label2: (portNumber1 ,portNumber2)})
						else:
							D[label1] = {label2: (portNumber1 ,portNumber2)}

			#if the component is a container block achieve the recurivity
			elif isinstance(c, ContainerBlock):
				self.makeDEVSGraph(c,D,type)
			
		return D

	def makeDEVSXML(self, D, filename):
		""" Make XML file from D graph of the diagram
		"""

		# build a tree structure
		root = ET.Element("CoupledModel", {'xmlns:xsi':"http://www.w3.org/2001/XMLSchema-instance", 'xmlns:xsd':"http://www.w3.org/2001/XMLSchema"})
		
		nom = ET.SubElement(root, "nom")
		nom.text = self.label
		
		# all of root (CoupledModel) children
		inp = ET.SubElement(root, "portsIn")
		outp = ET.SubElement(root, "portsOut")
		ioc = ET.SubElement(root, "inputCoupling")
		eoc = ET.SubElement(root, "outputCoupling")
		ic = ET.SubElement(root, "internalCoupling")
		composants = ET.SubElement(root, "composants")

		# for all models composing coupled model
		for component in D:
			# if iPort
			if isinstance(component, iPort):
				# nb iport
				n = ET.SubElement(inp, "nom")
				s = ET.SubElement(n, "string")
				s.text = component.label
				# IC
				for d in D[component]:
					for comp in d:
						c = ET.SubElement(ioc, "coupling")
						s = ET.SubElement(c, "source")
						s.text = self.label
						ps = ET.SubElement(c, "portSource")
						ps.text = str(d[comp][0])
						dest = ET.SubElement(c, "destination")
						dest.text = comp.label
						pd = ET.SubElement(c, "portDestination")
						pd.text = str(d[comp][1])

			elif isinstance(component, oPort): 
				n = ET.SubElement(outp, "nom")
				s = ET.SubElement(n, "string")
				s.text = component.label
				# IC
				for d in D[component]:
					for comp in d:
						c = ET.SubElement(eoc, "coupling")
						s = ET.SubElement(c, "source")
						s.text = comp.label
						ps = ET.SubElement(c, "portSource")
						ps.text = str(d[comp][1])
						dest = ET.SubElement(c, "destination")
						dest.text = self.label
						pd = ET.SubElement(c, "portDestination")
						pd.text = str(d[comp][0])
			else:
				# IC
				for d in D[component]:
					for comp in filter(lambda c: isinstance(c, Block),d):
						c = ET.SubElement(ic, "coupling")
						s = ET.SubElement(c, "source")
						s.text = component.label
						ps = ET.SubElement(c, "portSource")
						ps.text = str(d[comp][0])
						dest = ET.SubElement(c, "destination")
						dest.text = comp.label
						pd = ET.SubElement(c, "portDestination")
						pd.text = str(d[comp][1])
				#D
				class_name = os.path.splitext(os.path.basename(component.python_path))[0]
				model = ET.SubElement(composants, "Model", {'xsi:type':class_name})
				n = ET.SubElement(model, "nom")
				n.text = component.label
				pi = ET.SubElement(model, "portsIn")
				n = ET.SubElement(pi, "nom")
				for i in range(component.input):
					s = ET.SubElement(n, "string")
					# label port dont exist ! replace by the port id
					s.text = str(i)
				po = ET.SubElement(model, "portsOut")
				n = ET.SubElement(po, "nom")
				for i in range(component.output):
					s = ET.SubElement(n, "string")
					s.text = str(i)

		## wrap it in an ElementTree instance, and save as XML
		tree = ET.ElementTree(root)
		file = open(filename, "w")
		file.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>" + "\n")
		tree.write(file)
		file.close()

	def makeDEVSConnection(self, diagram = None, L = []):
		""" Make both DEVS ports and connections from diagram.
		"""

		# end of recursion
		if L == []:
			return diagram.getDEVSModel()
		else:
			m = L.pop()
			# creation des ports DEVS et des couplages pour la simulation
			if isinstance(m, CodeBlock) or isinstance(m, ContainerBlock):
		
				### recuperation du model DEVS
				devs = GetDEVSModel(m.python_path, m.args)

				## les ports des modeles couples sont pris en charge plus bas dans les iPorts et oPorts
				if isinstance(m, CodeBlock):
					## ajout des port par rapport aux ports graphiques
					for i in range(m.input):
						devs.addInPort()
					
					for i in range(m.output):
						devs.addOutPort()
						
				##  reaffectation
				m.setDEVSModel(devs)

				#ajout
				diagram.coupledModel.addSubModel(devs)
			
				# recursion sur le model couple 
				if isinstance(m, ContainerBlock):
					self.makeDEVSConnection(m, copy.copy(m.GetShapeList()))
		
			elif isinstance(m, iPort):
				diagram.coupledModel.addInPort()
				assert(len(diagram.coupledModel.IPorts) <= diagram.input)
			elif isinstance(m, oPort):
				diagram.coupledModel.addOutPort()
				assert(len(diagram.coupledModel.OPorts) <= diagram.output )
			elif isinstance(m, ConnectionShape):
				### est ce que le port de m1 est du type output (OPorts) ?
				try:
					m1 = m.input[0].getDEVSModel()
					p1 = m1.OPorts[m.input[1]]
				### non, il est de type input (IPorts)
				except AttributeError:
					m1 = diagram.getDEVSModel()
					index = m.input[0].id
					p1 = m1.IPorts[index]
				### alors la connectionShape est mal faite (un Node en l'air)
				except TypeError:
					return False
				### est ce que le port de m1 est du type output (OPorts) ?
				try:
					m2 = m.output[0].getDEVSModel()
					p2 = m2.IPorts[m.output[1]]
				### non, il est de type input (IPorts)
				except AttributeError:
					m2 = diagram.getDEVSModel()
					index = m.output[0].id
					p2 = m2.OPorts[index]
				### alors la connectionShape est mal faite (un Node en l'air)
				except TypeError:
					return False

				Structurable.ConnectDEVSPorts(diagram, p1, p2)
				
			return self.makeDEVSConnection(diagram, L)
             
	def OnSimulation(self, event):
		""" Method calling the simulationGUI
		"""
				
		# window that contain the diagram which will be simulate
		mainW = wx.GetApp().GetTopWindow()
		window = mainW.GetWindowByEvent(event)
		
		# diagram which will be simulate
		#diagram = copy.copy(self)
		diagram = self

		# copy of all shape into the diagram
		l = copy.copy(diagram.shapes)

		## la liste doit être rempli par makeDEVSConnection
		coupledModel = diagram.getDEVSModel()
		coupledModel.componentSet = []

		## fabrication du master DEVS à partir du digramme d
		master = self.makeDEVSConnection(diagram, l)
		
		# si le master contient des couplages mal connectés
		if not master:
			dial = wx.MessageDialog(window, _(str('You have an empty connection !')), 'Info', wx.OK)
			if dial.ShowModal() == wx.ID_OK:
				return False
		
		# si l'utilisateur n'a pas definit d'ordre de priorité pour l'activation des modèles, on la construit
		master.PRIORITY_LIST = [s.getDEVSModel() for s in diagram.priority_list]

		## graph pour simulation C# pour paul
		#D={}
		#graph = self.makeDEVSGraph(d, D)

		# test pour savoir si le modèle est a simuler est vide (fait aussi sur le bouton run pour le panel)
		if (master == None) or (master.componentSet == []):
			dial = wx.MessageDialog(window, _(str('You want to simulate an empty master model !')), 'Info', wx.OK)
			if dial.ShowModal() == wx.ID_OK:
				return False
		else:
			obj = event.GetEventObject()
			
			# si invocation à partir du bouton dans la toolBar (apparition de la frame de simulation dans une fenetre)
			if isinstance(obj, wx.ToolBar):
				frame = SimulationDialog(window, wx.ID_ANY, _(str('Simulator')), master)
				frame.Show()
			## si invocation par le menu (apparition de la frame de simulation dans le panel)
			elif isinstance(obj, wx.Menu) or isinstance(obj, wx.Frame):
				sizer3 = wx.BoxSizer(wx.VERTICAL)
				mainW.panel3.Show()
				mainW.SimDiag = SimulationDialog(mainW.panel3, wx.ID_ANY, _(str('Simulator')), master)
				sizer3.Add(mainW.SimDiag, 0, wx.EXPAND)
				mainW.panel3.SetSizer(sizer3)
				mainW.panel3.SetAutoLayout(True)
				mainW.nb1.InsertPage(2,mainW.panel3, _(str("Simulation")), imageId = 2)
			else:
				sys.stdout.write(_("This option has not been implemented yet.\n"))
				return False
		
		return True


	def AddShape(self, shape, after = None):
		""" Method that insert shape into the diagram at the position after
		"""

		if after:
			self.shapes.insert(self.shapes.index(after), shape)
		else:
			self.UpdateAddingCounter(shape)
			self.shapes.insert(0, shape)
		self.modify = True
	
	
	def AppendShape(self, shape):
		""" Method that add shape into the diagram
		"""

		self.shapes.append(shape)
		self.modify = True


	def InsertShape(self, shape, index=0):
		""" Method that insert shape into the diagram to the index position
		"""

		self.shapes.insert(index, shape)
		self.modify = True

		
	def DeleteShape(self,shape):
		""" Method that delete all shape links
		"""

		try:
			for cs in shape.connections:
				self.shapes.remove(cs)
		except:
			# passe pas parce que connections n'est pas vide
			pass
	
		# delete shape
		self.shapes.remove(shape)

		# update the number of shape depending to its type
		self.UpdateRemovingCounter(shape)

		##appel des del de chaque shape
		for base in shape.__class__.__bases__:
			shape.__del__()

		self.modify = True

		
	def UpdateRemovingCounter(self, shape):
		""" Method that update the removed shape counter
		"""

		# update number of components
		if isinstance(shape,CodeBlock):
			self.deletedCodeBlockId.append(shape.id)
			self.nbCodeBlock-=1
		elif isinstance(shape,ContainerBlock):
			self.deletedContainerBlockId.append(shape.id)
			self.nbContainerBlock-=1
		elif isinstance(shape,iPort):
			self.deletediPortId.append(shape.id)
			self.nbiPort-=1
		elif isinstance(shape,oPort):
			self.deletedoPortId.append(shape.id)
			self.nboPort-=1
		else:
			pass


	def UpdateAddingCounter(self, shape):
		""" Method that update the added shape counter
		"""

		# gestion du nombre de shape
		if isinstance(shape,CodeBlock):
			shape.id=self.GetCodeBlockCount()
			self.nbCodeBlock+=1
		elif isinstance(shape,ContainerBlock):
			shape.id=self.GetContainerBlockCount()
			self.nbContainerBlock+=1
		elif isinstance(shape,iPort):
			self.nbiPort+=1
		elif isinstance(shape,oPort):
			self.nboPort+=1
		else:
			pass


	def PopShape(self,index=-1):
		""" Function that pop the shape at the index position
		"""

		return self.shapes.pop(index)


	def DeleteAllShapes(self):
		""" Method that delete all shapes
		"""

		del self.shapes[:]
		self.modify = True

		
	def ChangeShapeOrder(self, shape, pos=0):
		"""
		"""

		self.shapes.remove(shape)
		self.shapes.insert(pos,shape)


	def GetCount(self):
		""" Function that return the number of shapes that composed the diagram
		""" 

		return len(self.shapes)

		
	def GetShapeByLabel(self,label=''):
		""" Function that return the shape instance from its label
		"""

		for s in filter(lambda block: isinstance(block, Block), self.shapes):
			if s.label==label:
				return s
		return False


	def GetShapeList(self):
		""" Function that return the shapes list
		"""

		return self.shapes


	def GetCodeBlockCount(self):
		""" Function that return the number of codeBlock shape
		"""

		if self.deletedCodeBlockId != []:
			return self.deletedCodeBlockId.pop()
		else:
			return self.nbCodeBlock


	def GetContainerBlockCount(self):
		""" Function that return the number of containerBlock shape
		"""

		if self.deletedContainerBlockId != []:
			return self.deletedContainerBlockId.pop()
		else:
			return self.nbContainerBlock


	def GetiPortCount(self):
		""" Function that return the number of iPort shape
		"""

		if self.deletediPortId != []:
			return self.deletediPortId.pop()
		else:
			return self.nbiPort


	def GetoPortCount(self):
		""" Function that return the number of oPort shape
		"""

		if self.deletedoPortId != []:
			return self.deletedoPortId.pop()
		else:
			return self.nboPort

# Generic Shape Event Handler------------------------------------
class ShapeEvtHandler:
	""" Handler class
	"""

	def OnLeftUp(self,event):
		pass
		
	def OnLeftDown(self,event):
		pass

	def leftUp(self,event):
		pass	

	def OnLeftDClick(self,event):
		pass

	def OnRightUp(self,event):
		pass
		
	def OnRightDown(self,event):
		pass
		
	def OnRightDClick(self,event):
		pass

	def OnSelect(self,event):
		pass
		
	def OnDeselect(self,event):
		pass
		
	def OnMove(self,event):
		pass
		
	def OnResize(self,event):
		pass
		
	def OnConnect(self,event):
		pass


# Generic Graphic items------------------------------------------
class Shape(ShapeEvtHandler):
	""" Shape class
	"""

	def __init__(self, x=[], y=[]):
		""" Constructor
		"""

		self.x = x                      # list of x coord
		self.y = y                      # list of y coords        
		self.pen = ['BLACK' , 1]    	# pen color and size
		self.fill= ['#f4d1ff']          # fill color


	def draw(self,dc):
		""" Draw method
		"""

		dc.SetPen(wx.Pen(self.pen[0], self.pen[1], wx.SOLID))
		dc.SetBrush(wx.Brush(self.fill[0], wx.SOLID))

	def move(self,x,y):
		""" Move method
		"""

		self.x = map((lambda v: v+x), self.x)
		self.y = map((lambda v: v+y), self.y)

	
	def Copy(self):
		""" Function that return the deep copy of shape
		"""

		return copy.deepcopy(self)
	
#---------------------------------------------------------
class LineShape(Shape):
	"""
	"""

	def __init__(self, x1 = 20, y1 = 20, x2 = 50, y2 = 50):
		""" Cosntructor
		"""

		Shape.__init__(self, [x1, x2] ,  [y1, y2])
		
	def draw(self, dc):
		""" Draw method
		"""

		Shape.draw(self,dc)
		dc.DrawLine(self.x[0], self.y[0], self.x[1], self.y[1])
	
	def HitTest(self, x, y):
		""" Hitest method
		"""
		if x < min(self.x)-3:return False
		if x > max(self.x)+3:return False
		if y < min(self.y)-3:return False
		if y > max(self.y)+3:return False
			
		top= (x-self.x[0]) *(self.x[1] - self.x[0]) + (y-self.y[0])*(self.y[1]-self.y[0])
		distsqr=pow(self.x[0]-self.x[1],2)+pow(self.y[0]-self.y[1],2)
		u=float(top)/float(distsqr)
		
		newx = self.x[0] + u*(self.x[1]-self.x[0])
		newy = self.y[0] + u*(self.y[1]-self.y[0])
	
		dist=pow(pow(newx-x,2) +  pow(newy-y,2),.5)
		
		if dist>7: return False
		return True

#---------------------------------------------------------
class RoundedRectangleShape(Shape):
	"""	RoundedRectangleShape class
	"""

	def __init__(self,x = 20, y = 20, x2 = 120, y2 = 120):
		""" constructor
		"""

		Shape.__init__(self, [x, x2] ,  [y, y2])

	def draw(self, dc):
		""" Draw method
		"""

		Shape.draw(self,dc)
		x,y=int(self.x[0]), int(self.y[0])
		width,height=int(self.x[1]-self.x[0]), int(self.y[1]-self.y[0])
		r=4.0
		dc.DrawRoundedRectangle(x,y,width,height,r)
		
	def HitTest(self, x, y):
		""" Hitest method
		"""
		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False
		
		return True

#---------------------------------------------------------
class RectangleShape(Shape):
	""" RectangleShape class
	"""

	def __init__(self,x = 20, y = 20, x2 = 120, y2 = 120):
		""" Constructor
		"""

		Shape.__init__(self, [x,x2] ,  [y,y2])

	def draw(self,dc):
		""" Draw paint method
		"""

		Shape.draw(self,dc)
		x,y = int(self.x[0]), int(self.y[0])
		width, height = int(self.x[1]-self.x[0]), int(self.y[1]-self.y[0])
		dc.DrawRectangle(x, y, width, height)
		
	def HitTest(self, x, y):
		""" Hitest method
		"""

		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False
		
		return True
#---------------------------------------------------------
class PolygonShape(Shape):
	""" PolygonShape class
	"""
	def __init__(self,x = 20, y = 20, x2 = 120, y2 = 120):
		""" Constructor
		"""

		Shape.__init__(self, [x,x2] , [y,y2])
		
	def draw(self, dc):
		"""
		"""

		Shape.draw(self, dc)
		
		dx = (self.x[1]-self.x[0])/2
		dy = (self.y[1]-self.y[0])/2
		p0 = wx.Point(self.x[0],self.y[0]-dy/2)
		p1 = wx.Point(self.x[0],self.y[1]+dy/2)
		p2 = wx.Point(self.x[1], self.y[0]+dy)
		offsetx = (self.x[1]-self.x[0])/2
		
		dc.DrawPolygon((p0,p1,p2),offsetx)
		
	def HitTest(self, x, y):
		""" Hitest method
		"""

		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False
		return True
		
#---------------------------------------------------------
class CircleShape(Shape):
	def __init__(self,x=20, y=20, x2=120, y2=120):
		Shape.__init__(self, [x,x2] ,  [y,y2])

	def draw(self,dc):
		Shape.draw(self,dc)
		dc.DrawCircle(int(self.x[0]+self.x[1])/2,int(self.y[0]+self.y[1])/2,30.0)
		dc.EndDrawing()
        
	def HitTest(self, x, y):
		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False
		return True
		
#---------------------------------------------------------
class PointShape(Shape):
	def __init__(self,x=20,y=20,size=4,type='rect'):
		Shape.__init__(self, [x] , [y])
		self.type = type
		self.size = size

		if self.type=='rondedrect':
			self.graphic = RoundedRectangleShape(x-size,y-size,x+size,y+size)
		elif self.type=='rect':
			self.graphic = RectangleShape(x-size,y-size,x+size,y+size)
		elif self.type=='circ':
			self.graphic = CircleShape(x-size,y-size,x+size,y+size)
		elif self.type=='poly':
			self.graphic = PolygonShape(x-size,y-size,x+size,y+size)
			
		self.graphic.pen = self.pen
		self.graphic.fill = self.fill
		
	def moveto(self,x,y):
		self.x = x
		self.y = y
		size = self.size
		self.graphic.x = [x-size,x+size]
		self.graphic.y = [y-size,y+size]
		
	def move(self,x,y):
		self.x = map((lambda v: v+x), self.x)
		self.y = map((lambda v: v+y), self.y)
		self.graphic.move(x,y)

	def HitTest(self, x, y):
		return self.graphic.HitTest(x,y)

	def draw(self,dc):
		self.graphic.pen = self.pen
		self.graphic.fill = self.fill
		self.graphic.draw(dc)

#-------------------------------------------------------------
class ShapeCanvas(wx.ScrolledWindow, TextDrop):
	""" ShapeCanvas class.
	"""

	ID = 0

	def __init__(self, parent, id=wx.ID_ANY, pos=(-1,-1), size=(-1,-1), style=0, name=""):
		""" Construcotr
		"""
		wx.ScrolledWindow.__init__(self,parent,id,pos,size,style,name)
		TextDrop.__init__(self,canvas=self)

		# un ShapeCanvas est Dropable
		self.SetDropTarget(self)
		
		self.name = name
		self.diagram = None
		self.nodes = []
		self.currentPoint = [0, 0] # x and y of last mouse click
		self.selectedShapes = []
		self.scalex = 1.0
		self.scaley = 1.0
		self.SetScrollbars(50, 50, 50, 50)
		ShapeCanvas.ID += 1
		
		# Rubber Bande Attributs
		# mouse selection start point
		self.m_stpoint = wx.Point(0,0)
		# mouse selection end point
		self.m_endpoint = wx.Point(0,0)
		# mouse selection cache point
		self.m_savepoint = wx.Point(0,0)
		# flags for left click/ selection
		self._leftclicked = False
		self._selected = False
			
		self.scroller = wx.lib.dragscroller.DragScroller(self)

		#Window Events        
		wx.EVT_PAINT(self, self.onPaintEvent)
		#Mouse Events
		wx.EVT_LEFT_DOWN(self, self.OnLeftDown)
		wx.EVT_LEFT_UP(self, self.OnLeftUp)
		wx.EVT_LEFT_DCLICK(self, self.OnLeftDClick)
		
		wx.EVT_RIGHT_DOWN(self, self.OnRightDown)
		wx.EVT_RIGHT_UP(self, self.OnRightUp)
		wx.EVT_RIGHT_DCLICK(self, self.OnRightDClick)
		
		wx.EVT_MIDDLE_DOWN(self, self.OnMiddleDown)
		wx.EVT_MIDDLE_UP(self, self.OnMiddleUp)
		
		wx.EVT_MOTION(self, self.OnMotion)
		#Key Events
		wx.EVT_KEY_DOWN(self,self.keyPress)

		#wx.EVT_SCROLLWIN(self, self.OnScroll) 
		
	def AddShape(self, shape, after = None):
		self.diagram.AddShape(shape, after)
			
	def AppendShape(self, shape):
		self.diagram.AppendShape(shape)
		
	def InsertShape(self, shape, index = 0):
		self.diagram.InsertShape(shape, index)

	def DeleteShape(self, shape):
		self.diagram.DeleteShape(shape)
		
	def RemoveShape(self, shape):
		self.diagram.DeleteShape(shape)
	
	def keyPress(self, event):
		key = event.GetKeyCode()
		if key == 127:  # DELETE
			self.OnDelete(event)
		elif key == 67 and event.ControlDown():  # COPY
			self.OnCopy(event)
		elif key == 86 and event.ControlDown():  # PASTE
			self.OnPaste(event)
		elif key==88 and event.ControlDown():  # CUT
			self.OnCut(event)
		elif key==65 and event.ControlDown():  # ALL
			for item in self.diagram.shapes:
				self.select(item)
		elif key==82 and event.ControlDown():  # Rotate model on the right
			for s in filter(lambda shape: not isinstance(shape,ConnectionShape),self.selectedShapes):
				s.OnRotateR(event)
		elif key==76 and event.ControlDown():  # Rotate model on the left
			for s in filter(lambda shape: not isinstance(shape,ConnectionShape),self.selectedShapes):
				s.OnRotateL(event)
		elif key == 9: # TAB
			if len(self.diagram.shapes)==0:
				return
			shape = self.select()
			if shape:
				ind = self.diagram.shapes.index(shape[0])
				self.deselect()
				try:
					self.select(self.diagram.shapes[ind+1])
				except:
					self.select(self.diagram.shapes[0])
			else:
					self.select(self.diagram.shapes[0])
		self.Refresh()
		event.Skip()
		
	def onPaintEvent(self, event):
		dc = wx.PaintDC(self)
		self.PrepareDC(dc)
		dc.SetUserScale(self.scalex,self.scaley)
		dc.BeginDrawing()
		for item in self.diagram.shapes + self.nodes:
			try:
				item.draw(dc)
			except AttributeError:
				sys.stderr.write(_("Draw error \n"))
		dc.EndDrawing()

	def OnRightDown(self,event):
		
		# current shape
		s = self.getCurrentShape(event)
		
		# dont clic on canvas
		if s is not None and self.isSelected(s):
			# Rigth click menu
			menu = wx.Menu()
			rotate_subMenu = wx.Menu()
			export_subMenu = wx.Menu()
			connectable_subMenu = wx.Menu()

			edit=wx.MenuItem(menu, wx.NewId(), _('Edit'), _('Edit the code'))
			copy=wx.MenuItem(menu, wx.NewId(), _('&Copy\tCtrl+C'), _('Copy the Model'))
			paste=wx.MenuItem(menu, wx.NewId(), _('&Paste\tCtrl+V'), _('Paste the Model'))
			cut=wx.MenuItem(menu, wx.NewId(), _('&Cut\tCtrl+X'), _('Cut the Model'))
			rotateR=wx.MenuItem(menu, wx.NewId(), _('&Right Rotate\tCtrl+R'), _('Rotate on the right'))
			rotateL=wx.MenuItem(menu, wx.NewId(), _('&Left Rotate\tCtrl+L'), _('Rotate on the left'))
			delete=wx.MenuItem(menu, wx.NewId(), _('Delete'), _('Delete the Model'))
			export=wx.MenuItem(menu, wx.NewId(), _('Export'), _('Export the Model'))
			exportCMD=wx.MenuItem(menu, wx.NewId(), _('CMD'), _('Model exported to cmd file'))
			exportXML=wx.MenuItem(menu, wx.NewId(), _('XML'), _('Model exported to the xml file'))
			properties=wx.MenuItem(menu, wx.NewId(), _('Properties'), _('Edit the attributs'))
				
			edit.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'edit.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			copy.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'copy.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			paste.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'paste.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			cut.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'cut.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			rotateL.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'rotateL.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			rotateR.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'rotateR.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			export.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'export.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			delete.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'delete.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			properties.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'properties.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			
			if isinstance(s,ConnectionShape):
				Delete_menu=menu.AppendItem(delete)
				self.Bind(wx.EVT_MENU, self.OnDelete, Delete_menu)
			
			elif isinstance(s, ResizeableNode):
				Delete_menu=menu.AppendItem(delete)
			else:	
				Edit_menu=menu.AppendItem(edit)
				menu.AppendSeparator()

				Copy_menu=menu.AppendItem(copy)
				Paste_menu=menu.AppendItem(paste)
				Cut_menu=menu.AppendItem(cut)
				Rotate_SubMenu1 = rotate_subMenu.AppendItem(rotateR)
				Rotate_SubMenu2 = rotate_subMenu.AppendItem(rotateL)
				Rotate_menu=menu.AppendMenu(-1,_("Rotate"),rotate_subMenu)

				menu.AppendSeparator()
				# pour tout les model sur le canvas ormis les connection et le model que l'on veut connecter (la source)
				for i, item in enumerate(filter(lambda a: a != s and not isinstance(a, ConnectionShape), self.GetDiagram().GetShapeList())):
					# on evite de proposer les connections suivante: iPort->iPort, oPort->oPort
					if (isinstance(s, iPort) and not isinstance(item, iPort)) or (isinstance(s, oPort) and not isinstance(item, oPort)) or isinstance(s, Block):
						new_item = wx.MenuItem(connectable_subMenu, wx.NewId(), item.label)
						connectable_subMenu.AppendItem(new_item)
						self.Bind(wx.EVT_MENU, self.OnConnectTo,id = new_item.GetId())
				menu.AppendMenu(-1, _('Connect to'), connectable_subMenu)

				if isinstance(s, CodeBlock):
					menu.AppendSeparator()
					Export_menu = menu.AppendItem(export)
				elif isinstance(s, ContainerBlock):
					menu.AppendSeparator()
					Export_menu=menu.AppendMenu(-1,_("Export"),export_subMenu)
					Export_SubMenu1 = export_subMenu.AppendItem(exportCMD)
					Export_SubMenu2 = export_subMenu.AppendItem(exportXML)

				menu.AppendSeparator()
				Delete_menu = menu.AppendItem(delete)

				menu.AppendSeparator()
				Properties_menu = menu.AppendItem(properties)
				
				if clipboard == []:
					menu.Enable(paste.GetId(),False)
				
				# binding events
				self.Bind(wx.EVT_MENU, s.OnRotateR, Rotate_SubMenu1)
				self.Bind(wx.EVT_MENU, s.OnRotateL, Rotate_SubMenu2)
				self.Bind(wx.EVT_MENU, self.OnDelete, Delete_menu)
				self.Bind(wx.EVT_MENU, self.OnCut, Cut_menu)
				self.Bind(wx.EVT_MENU, self.OnCopy, Copy_menu)
				self.Bind(wx.EVT_MENU, self.OnPaste, Paste_menu)
				self.Bind(wx.EVT_MENU, self.OnProperties, Properties_menu)

				# Codeblock specific binding
				if isinstance(s, CodeBlock):
					self.Bind(wx.EVT_MENU, self.OnEditor, Edit_menu)
					self.Bind(wx.EVT_MENU, s.OnExport, Export_menu)
				# ContainerBlock specific binding
				elif isinstance(s, ContainerBlock):
					self.Bind(wx.EVT_MENU, self.OnEditor, Edit_menu)
					self.Bind(wx.EVT_MENU, s.OnExportCMD, Export_SubMenu1)
					self.Bind(wx.EVT_MENU, s.OnExportXML, Export_SubMenu2)
				
			# show popUpMenu
			#menu.SetInvokingWindow(self.GetParent())
				
			if isinstance(s, ResizeableNode):
				s.OnDeleteNode(event)

			#elif isinstance(s, CodeBlock):
				#s.OnRightDown(event)

		else:
			menu = wx.Menu()
			
			new = wx.MenuItem(menu, wx.NewId(), _('&New'), _('New Model'))
			paste = wx.MenuItem(menu, wx.NewId(), _('&Paste\tCtrl+V'), _('Paste the Model'))
			add_constants = wx.MenuItem(menu, wx.NewId(), _('Add Constants'), _('Add constants parameters'))
			
			new.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'new_model.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			paste.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'paste.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			add_constants.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'properties.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			
			New_menu = menu.AppendItem(new)
			Paste_menu=menu.AppendItem(paste)
			AddConstants_menu = menu.AppendItem(add_constants)
			
			if clipboard == []:
				menu.Enable(paste.GetId(),False)
		
			self.Bind(wx.EVT_MENU, self.OnNewModel, New_menu)
			self.Bind(wx.EVT_MENU, self.OnPaste, Paste_menu)
			self.Bind(wx.EVT_MENU, self.diagram.AddConstants, AddConstants_menu)
			
		self.PopupMenu(menu, (event.GetX(),event.GetY()))
		menu.Destroy()

		#Refresh canvas
		self.Refresh()

	def OnConnectTo(self,event):
		id=event.GetId()
		menu = event.GetEventObject()

		#source model from diagram
		source = self.getSelectedShapes()[0]

		# Model Name
		targetName = menu.GetLabelText(id)
		sourceName = source.label
		
		# get target model from its name
		for s in filter(lambda m: not isinstance(m,ConnectionShape),self.diagram.shapes):
			if s.label == targetName:
				target=s
				break

		# list of node list for 
		sourceINodeList = filter(lambda n: not isinstance(n, ResizeableNode) and isinstance(n,INode),self.nodes)
		sourceONodeList = filter(lambda n: not isinstance(n, ResizeableNode) and isinstance(n,ONode),self.nodes)

		# deselect and select target in order to get its list of node (because the node are generated dynamicly)
		self.deselect()
		self.select(target)

		nodesList=filter(lambda n: not isinstance(n, ResizeableNode),self.nodes)
		
		if isinstance(target,Block):
			if isinstance(source, oPort):
				self.sourceNodeList = sourceINodeList
				self.targetNodeList = filter(lambda n: not n in sourceONodeList and isinstance(n,ONode),nodesList)
			elif isinstance(source, iPort):
				self.sourceNodeList = sourceONodeList
				self.targetNodeList = filter(lambda n: not n in sourceINodeList and isinstance(n,INode),nodesList)
			else:
				self.sourceNodeList = sourceONodeList
				if not PORT_RESOLUTION:
					self.sourceNodeList += sourceINodeList
					self.targetNodeList = filter(lambda n: not n in self.sourceNodeList,nodesList)
				else:
					self.targetNodeList = filter(lambda n: not n in self.sourceNodeList and isinstance(n,INode),nodesList)

		elif isinstance(target,iPort):
			if isinstance(source, oPort):
				self.sourceNodeList = sourceINodeList
			elif isinstance(source, iPort):
				self.sourceNodeList = sourceONodeList
			else:
				self.sourceNodeList = sourceINodeList

			self.targetNodeList = filter(lambda n: not n in sourceONodeList and isinstance(n,ONode),nodesList)
		
		elif isinstance(target,oPort):
			if isinstance(source, oPort):
				self.sourceNodeList = sourceINodeList
			elif isinstance(source, iPort):
				self.sourceNodeList = sourceONodeList
			else:
				self.sourceNodeList = sourceONodeList
			self.targetNodeList = filter(lambda n: not n in sourceINodeList and isinstance(n,INode),nodesList)
		else:
			self.targetNodeList = []

		# Now we, if the nodes list are not empty, the connection can be proposed form ConnectDialog
		if self.sourceNodeList != [] and self.targetNodeList != []:
			if len(self.sourceNodeList) == 1 and len(self.targetNodeList) == 1:
				self.makeConnectionShape(self.sourceNodeList[0],self.targetNodeList[0])
			else:
				self.dlgConnection = ConnectDialog(wx.GetApp().GetTopWindow(), -1, _("Connection"), sourceName, self.sourceNodeList, targetName, self.targetNodeList)
				self.dlgConnection.Bind(wx.EVT_BUTTON, self.OnDisconnect, self.dlgConnection.button_disconnect)
				self.dlgConnection.Bind(wx.EVT_BUTTON, self.OnConnect, self.dlgConnection.button_connect)
				self.dlgConnection.Bind(wx.EVT_CLOSE, self.OnCloseConnectionDialog)
				self.dlgConnection.Show()
	
	def OnDisconnect(self, event):
		"""	Disconnect selected ports from connectDialog
		"""

		sp,tp = self.dlgConnection.result

		for connectionShapes in filter(lambda s: isinstance(s,ConnectionShape), self.diagram.shapes):
			if (connectionShapes.getInput()[1] == sp) and  (connectionShapes.getOutput()[1] == tp):
				self.RemoveShape(connectionShapes)
		self.deselect()
		self.Refresh()

	def OnConnect(self, event):
		"""	Connect selected ports from connectDialog
		"""

		# dialog results
		sp,tp = self.dlgConnection.result

		### if one of selected option is All
		if (	self.dlgConnection.combo_box_tn.StringSelection == _('All') \
			and self.dlgConnection.combo_box_sn.StringSelection != _('All')):
			sn = self.sourceNodeList[sp]
			for tn in self.targetNodeList:
				self.makeConnectionShape(sn, tn)
		### if both combo box selection are All, delete all of the connection from the top to the bottom
		elif (	self.dlgConnection.combo_box_tn.StringSelection == _('All') \
			and self.dlgConnection.combo_box_sn.StringSelection == _('All')) \
			and len(self.sourceNodeList)==len(self.targetNodeList):
			for sn,tn in map(lambda a,b: (a,b), self.sourceNodeList ,self.targetNodeList):
				self.makeConnectionShape(sn,tn)
		### else make simple connection between sp and tp port number of source and target
		else:
			sn = self.sourceNodeList[sp]
			tn = self.targetNodeList[tp]
			self.makeConnectionShape(sn,tn)

		self.Refresh()

	def makeConnectionShape(self,sourceNode,targetNode):
		""" Make new ConnectionShape from input number(sp) to output number (tp)
		"""
	
		# préparation et ajout dans le diagramme de la connection
		ci = ConnectionShape()
		self.diagram.shapes.insert(0, ci)
	
		# connection physique 
		if isinstance(sourceNode, ONode):
			ci.setInput(sourceNode.item,sourceNode.index)
			ci.x[1],ci.y[1] = sourceNode.item.getPort('output',sourceNode.index)

			ci.setOutput(targetNode.item,targetNode.index)
			# Add connectionShapes to graphical models
			targetNode.item.connections.append(ci)
			ci.output[0].connections.append(ci)
		else:
			ci.setInput(targetNode.item,targetNode.index)
			ci.x[1],ci.y[1] = targetNode.item.getPort('output',targetNode.index)

			ci.setOutput(sourceNode.item,sourceNode.index)
			# Add connectionShapes to graphical models
			sourceNode.item.connections.append(ci)
			ci.output[0].connections.append(ci)

		# selection de la nouvelle connection
		self.deselect()
		self.select(ci)

	def OnCloseConnectionDialog(self, event):
		"""
		"""
		# deselection de la dernier connection creer
		self.deselect()
		self.Refresh()
		# destruction du dialogue
		self.dlgConnection.Destroy()

	def OnMiddleDown(self, event):
		"""
		"""
		self.scroller.Start(event.GetPosition())
		
	def OnMiddleUp(self, event):
		self.scroller.Stop()
		
	def OnCopy(self, event):
		"""
		"""
		del clipboard[:]
		for m in self.select():
			clipboard.append(m)
		
		# main windows statusbar update
		mainW=self.GetTopLevelParent()
		mainW.statusbar.SetStatusText(_('Copy'), 0)
		mainW.statusbar.SetStatusText('', 1)

	def  OnScroll(self,event):
		"""
		"""
		pass 

	def OnProperties(self,event):
		""" Properties sub menu has been clicked. Event is transmit to the model
		"""
		# pour passer la fenetre principale à OnProperties qui est deconnecte de l'application du faite de popup
		event.SetClientData(self.GetTopLevelParent())
		for s in self.select():
			s.OnProperties(event)

	def OnEditor(self,event):
		""" Edition sub menu has been clicked. Event is transmit to the model
		"""
		event.SetClientData(self.GetTopLevelParent())
		for s in self.select():
			s.OnEditor(event)

	def OnNewModel(self, event):
		""" New model menu has been pressed. Wizard is instanciate.
		"""
		
		# mouse postions
		xwindow, ywindow = wx.GetMousePosition()
		x,y = self.ScreenToClientXY(xwindow, ywindow)

		# Create wizard and run
		gmwiz = ModelGeneratorWizard(title = 'DEVSimPy Model Generator', parent = self, img_filename=os.path.join('bitmaps','IconeDEVSimPy.png'))
		gmwiz.run()

		# get all param for block model instance generation
		label = gmwiz.label
		inputs = gmwiz.inputs
		outputs = gmwiz.outputs
		python_path = gmwiz.python_path
		model_path = gmwiz.model_path
		id = gmwiz.id
	
		# Cleanup
		gmwiz.Destroy()

		# if wizard is finished witout closing
		if model_path != '' or (gmwiz.type in ('iPort', 'oPort')):
			m = self.GetBlockModel(x = x, y = y, label = label, id = id, inputs = inputs, outputs = outputs, python_file = python_path, model_file = model_path)
			if m:

				# save visual model
				if m.SaveFile(model_path):
					m.last_name_saved = model_path
				else:
					dlg = wx.MessageDialog(self, _('Error saving file %s\n')%os.path.basename(m.last_name_saved))
					dlg.ShowModal()

				#deselect all modeles
				self.deselect()
				# Adding graphical model to diagram
				self.AddShape(m)
				# Select m shape
				self.select(m)

				sys.stdout.write(_("Adding DEVSimPy model: \n").encode('utf-8'))
				sys.stdout.write(repr(m))

				# canvas refresh and focus
				self.Refresh()
				self.SetFocus()
				
				# try to update the librairy tree on left panel
				try:
					
					tree = wx.GetApp().frame.tree
					# for all charged domain
					for domain_dir in tree.GetChildRoot():
						# if the domain dir is in the model path then udpate de corresponding domain
						if domain_dir in model_path:
							tree.UpdateDomain(os.path.join(DOMAIN_DIR,domain_dir))
				except:
					pass

	@BuzyCursorNotification
	def OnPaste(self, event):
		""" Paste menu has been clicked.
		"""

		D = {}	# correspondance between the new and the paste model
		L = []	# list of original connectionShape components

		#
		for m in clipboard:
			if isinstance(m, ConnectionShape):
				L.append(m)
			else:
				# make new shape
				newShape=m.Copy()
				# store correspondance (for coupling)
				D[m]= newShape
				# move new modele
				newShape.x[0] +=35
				newShape.x[1] +=35
				newShape.y[0] +=35
				newShape.y[1] +=35
				self.AddShape(newShape)
				# select new model
				self.select(newShape)

		# Les couplages dépende des inodes et des onodes présent sur le canvas. En fait il n'y a pas 
		# de correspondance directe entre les modèles et les connectonShape. Cela rend difficile le copier/coller
		# des liaisons entre les modèle surtout que l'on travail sur des copier de modèle et donc que l'on perd les références
		# de couplage. Donc L stocke uniquement les connectionShape et D permet de faire la correcpondance entre les ancier
		# modèle et les nouveaux. L'algorithme consiste a retrouver les uinod eet les onode correspondant au moèlde qui douvenet être lié.

		# liste des inode et des onode selectionner apres le paste des modèles
		L_inode = filter(lambda n: isinstance(n, INode), self.nodes)
		L_onode = filter(lambda n: isinstance(n, ONode), self.nodes)
		
		# pour toute les connection (connectionSahpe)
		for cs in L:
		
			# determination des onode a couplé pour le modèle m1 (de gauche par exemple)
			# m1 modèle de gauche et ind1 numero du port à lier
			m1= D[cs.getInput()[0]]
			ind1 = cs.getInput()[1]
			
			for onode in L_onode:
				m2 = onode.item
				# si le onod etait bien sur le modèle m1 qui correspond au nouveau m2 et si le numéro de port est bien le bon
				if (m1 == m2 and ind1 == onode.index):
					a=onode

			# determination des inode a couplé pour le modèle m1 (de droite par exemple)
			m1 = D[cs.getOutput()[0]]
			ind1 = cs.getOutput()[1]
			
			for inode in L_inode:
				m2 = inode.item
				if (m1 == m2 and ind1 == inode.index):
					b=inode

			# creation de la nouvelle connextion
			self.makeConnectionShape(a,b)

		# specify the operation in status bar
		mainW=self.GetTopLevelParent()
		mainW.statusbar.SetStatusText(_('Paste'), 0)
		mainW.statusbar.SetStatusText('', 1)


	def OnCut(self, event):
		""" Cut menu has been clicked. Copy and delete event.
		"""

		self.OnCopy(event)
		self.OnDelete(event)

		
	def OnDelete(self, event):
		"""	Delete menu has been clicked. Delete all selected shape.
		"""

		for s in self.select():
			self.diagram.DeleteShape(s)
		self.deselect()
		self.SetFocus()

	def OnRightUp(self,event):
		"""
		"""
		try:
			self.getCurrentShape(event).OnRightUp(event)
		except AttributeError:
			pass

	def OnRightDClick(self,event):
		"""
		"""
		try:
			self.getCurrentShape(event).OnRightDClick(event)
		except AttributeError:
			pass

	def OnLeftDClick(self,event):
		"""
		"""
		try:
			self.getCurrentShape(event).OnLeftDClick(event)
		except AttributeError:
			pass
		
	def OnLeftDown(self,event):
		"""
		"""
		item = self.getCurrentShape(event)

		if item is None:   #clicked on empty space deselect all
			self.deselect()
	
			## Left mouse button down, change cursor to
			## something else to denote event capture
			self.m_stpoint = event.GetPosition()
			self.m_endpoint=wx.Point(0,0)
		
			## invalidate current canvas
			self.Refresh()
			# cache current position
			self.m_savepoint = self.m_stpoint

			self._selected = False
			self._leftclicked = True
			
		else:
			# si element pas encore selectionné alors selectionne et pas les autres		
			if item not in self.getSelectedShapes():
				item.OnLeftDown(event) # send leftdown event to current shape
				if isinstance(item,Selectable): 
						if not event.ShiftDown():self.deselect()
			
				self.select(item)
			# sinon les autres aussi participent
			else:
				for s in self.getSelectedShapes():
					s.OnLeftDown(event) # send leftdown event to current shape
	
		# main windows statusbar update
		mainW = self.GetTopLevelParent()
		mainW.statusbar.SetStatusText( '', 0)
		mainW.statusbar.SetStatusText('', 1)

		self.Refresh()
		self.SetFocus()

	###
	def OnLeftUp(self, event):
		"""
		"""
		shape = self.getCurrentShape(event)

		### clic sur un block
		if shape is not None:
			
			shape.OnLeftUp(event)
			shape.leftUp(self.select())

		### clique sur le canvas
		else:
			
			# User released left button, change cursor back
			self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))       
			self._selected = True  #selection is done
			self._leftclicked = False # end of clicking

			# gestion des shapes qui sont dans le rectangle
			recRubber=wx.Rect(self.m_stpoint.x,self.m_stpoint.y,(self.m_endpoint.x - self.m_stpoint.x),(self.m_endpoint.y - self.m_stpoint.y))

			for s in self.diagram.shapes:
				x = s.x[0]*self.scalex
				y = s.y[0]*self.scaley
				w = (s.x[1]-s.x[0])*self.scalex
				h = (s.y[1]-s.y[0])*self.scaley
				recS = wx.Rect(x,y,w,h)
		
				# si les deux rectangles se chevauche		
				try:
					if recRubber.ContainsRect(recS):
						self.select(s)
				except AttributeError:
					raise(_("use >= wx-2.8-gtk-unicode library"))

		self.Refresh()

	###
	def OnMotion(self, event):
		"""
		"""

		if event:
			# set mouse cursor
			self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
			# get device context of canvas
			dc= wx.ClientDC(self)
			
			# Set logical function to XOR for rubberbanding
			dc.SetLogicalFunction(wx.XOR)
			
			# Set dc brush and pen
			# Here I set brush and pen to white and grey respectively
			# You can set it to your own choices
			
			# The brush setting is not really needed since we
			# dont do any filling of the dc. It is set just for 
			# the sake of completion.
			
			wbrush = wx.Brush(wx.Colour(255,255,255), wx.TRANSPARENT)
			wpen = wx.Pen(wx.Colour(200, 200, 200), 1, wx.SOLID)
			dc.SetBrush(wbrush)
			dc.SetPen(wpen)
			
		if event.Dragging():
			self.diagram.modify = False

			point = self.getEventCoordinates(event)
			x = point[0] - self.currentPoint[0]
			y = point[1] - self.currentPoint[1]
			for i in self.getSelectedShapes():
				i.move(x,y)
				self.diagram.modify=True
				
			self.currentPoint = point			
			
			if self.diagram.modify:
				mainW=self.GetTopLevelParent()
				if isinstance(mainW, DetachedFrame):
					string = mainW.GetTitle()
				else:	
					string=mainW.nb2.GetPageText(mainW.nb2.GetSelection())

				mainW.statusbar.SetStatusText( "%s %s"%(string ,_("modified")), 0)
				mainW.statusbar.SetStatusText('', 1)
				mainW.statusbar.SetStatusText('', 2)
			
			# User is dragging the mouse, check if
			# left button is down
			if self._leftclicked:
			
				wbrush = wx.Brush(wx.Colour(15,15,15))
				wpen = wx.Pen(wx.Colour(200, 200, 200), 1, wx.SOLID)
				dc.SetBrush(wbrush)
				dc.SetPen(wpen)
				
				self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
				# reset dc bounding box
				dc.ResetBoundingBox()
				dc.BeginDrawing()
				w = (self.m_savepoint.x - self.m_stpoint.x)
				h = (self.m_savepoint.y - self.m_stpoint.y)
				
				# To erase previous rectangle
				dc.DrawRectangle(self.m_stpoint.x, self.m_stpoint.y, w, h)
				
				# Draw new rectangle
				self.m_endpoint =  event.GetPosition()
				
				w = (self.m_endpoint.x - self.m_stpoint.x)
				h = (self.m_endpoint.y - self.m_stpoint.y)
				
				# Set clipping region to rectangle corners
				dc.SetClippingRegion(self.m_stpoint.x, self.m_stpoint.y, w,h)
				dc.DrawRectangle(self.m_stpoint.x, self.m_stpoint.y, w, h) 
				dc.EndDrawing()
				
				self.m_savepoint = self.m_endpoint # cache current endpoint
					
			else:
				self.Refresh()
	
	def SetDiagram(self,diagram):
		self.diagram=diagram
		
	def GetDiagram(self):
		return self.diagram
	
	def getCurrentShape(self,event):
		# get coordinate of click in our coordinate system
		point = self.getEventCoordinates(event)
		self.currentPoint = point
		# Look to see if an item is selected
		for item in self.nodes + self.diagram.shapes:
			if item.HitTest(point[0],point[1]) :
				return item
		return None
		
	def getEventCoordinates(self, event):
		originX, originY = self.GetViewStart()
		unitX, unitY = self.GetScrollPixelsPerUnit()
		return [(event.GetX() + (originX * unitX)) / self.scalex, (event.GetY() + (originY * unitY))/ self.scaley]

	def getSelectedShapes(self):
		return self.selectedShapes

	def isSelected(self,s):
		return s in self.selectedShapes

	def getName(self):
		return self.name
	
	def deselect(self,item=None):
		if item is None:
			for s in self.selectedShapes:
				s.OnDeselect(None)
			del self.selectedShapes[:]
			del self.nodes[:]
		else:
			self.nodes=[ n for n in self.nodes if n.item != item]
			self.selectedShapes = [ n for n in self.selectedShapes if n != item]
			item.OnDeselect(None)
	
	### selectionne un shape
	def select(self,item = None):
		if item is None:
			return self.selectedShapes
		
		if isinstance(item,Node):
			del self.selectedShapes[:]
			self.selectedShapes.append(item) # items here is a single node
			return

		if not item in self.selectedShapes:
			self.selectedShapes.append(item)
			item.OnSelect(None)
			if isinstance(item,Connectable):
				self.nodes.extend( [INode(item,n,self) for n in range(item.input)] )
				self.nodes.extend( [ONode(item,n,self) for n in range(item.output)] )
			if isinstance(item,Resizeable):
				self.nodes.extend( [ResizeableNode(item,n,self) for n in range(len(item.x))] )
	
	### selection sur le canvas les ONodes car c'est le seul moyen d'y accéder pour effectuer l'appartenance avec les modèles
	def showOutputs(self,item=None):
		if item:
			self.nodes.extend( [ONode(item,n,self) for n in range(item.output)])
		elif item is None:
			for i in self.diagram.shapes:
				if isinstance(i,Connectable):
					self.nodes.extend( [ONode(i,n,self) for n in range(i.output)] )

	### selection sur le canvas les INodes car c'est le seul moyen d'y accéder pour effectuer l'appartenance avec les modèles
	def showInputs(self,item=None):
		if isinstance(item,Block):
			self.nodes.extend( [INode(item,n,self) for n in range(item.input)] )
		else:
			for i in self.diagram.shapes:
				if isinstance(i,Connectable):
					self.nodes.extend( [INode(i,n,self) for n in range(i.input)])

#------------------------------------------
class Selectable:
	""" Allows Shape to be selected
	"""

	def __init__(self):
		pass

#---------------------------------------------------------
class Resizeable:
	""" Creates resize Nodes that can be drug around the canvas to alter the shape or size of the Shape.
	"""
	def __init__(self):
		pass

#---------------------------------------------------------
class Rotable:
	""" Creates rotable Block can rotate under 4 direction (est, ouest, nord, sud)
	"""
	
	def __init__(self):
		""" Constructor.
		"""
		self.direction="ouest"	 

	###
	def OnRotateR(self, event):
		if self.direction == "ouest":
			self.direction = "nord"
		elif self.direction == "nord":
			self.direction = "est"
		elif self.direction == "est":
			self.direction = "sud"
		else:
			self.direction = "ouest"

	###
	def OnRotateL(self, event):
		if self.direction == "ouest":
			self.direction = "sud"
		elif self.direction == "nord":
			self.direction = "ouest"
		elif self.direction == "est":
			self.direction = "nord"
		else:
			self.direction = "est"

#---------------------------------------------------------
class Connectable:
	"""Creates connection nodes or ports 
	"""

	def __init__(self, nb_in=1, nb_out=3):
		""" Constructor
		"""
		
		self.input = nb_in
		self.output = nb_out
		self.connections = [] # this will be the list containing downstream connections
		self.direction = "ouest"	# direction of ports (left)
	
	def getPort(self, type, num):
		
		# width and height of model
		w = self.x[1]-self.x[0]
		h = self.y[1]-self.y[0]
		
		if type=='input':
			div = float(self.input)+1.0
			x=self.x[0]
			
		elif type=='output':
			div = float(self.output)+1.0
			x=self.x[1]
		
		dx=float(w)/div
		dy=float(h)/div
		y= self.y[0]+dy*(num+1)
		
		# ouest -> nord
		if self.direction == "nord":
			if type=='input':
				x+=dx*(num+1)
				y-=dy*(num+1)
			else:
				x-=dx*(num+1)
				y+=h-dy*(num+1)
		# nord -> est
		elif self.direction == "est":
			if type=='input':
				x+=w
				y+=0
			else:
				x-=w
				y+=0
		# est -> sud
		elif self.direction == "sud":
			if type=='input':
				x+=dx*(num+1)
				y+=h-dy*(num+1)
			else:
				x-=dx*(num+1)
				y-=dy*(num+1)
		# sud -> ouest
		elif self.direction == "ouest":
			if type=='input':
				x+=0
				y+=0
			else:
				x+=0
				y+=0		
		
		return(x,y)
		
#---------------------------------------------------------
class Attributable:
	"""	Allows AttributeEditor to edit specified properties of the Shape
	"""

	def __init__(self):
		""" Constructor
		"""
		self.attributes = []
		
	def AddAttribute(self, name):
		self.attributes.append(name)

	def GetAttributes(self):
		return self.attributes

	def AddAttributes(self, atts):
		self.attributes.extend(atts)
		
	def RemoveAttribute(self, name):
		self.attributes.remove(name)

	def ShowAttributes(self, event):
		canvas = event.GetEventObject()
		parent = canvas.GetTopLevelParent()
		
		nb1 = TextDrop.SOURCE

		if isinstance(self, Block) and event.ControlDown():
			d = wx.TextEntryDialog(canvas,_('Block Label'),defaultValue=self.label,style=wx.OK)
			d.ShowModal()
			# changement du label
			self.label = d.GetValue()
			if nb1.GetSelection() == 1:
				newContent = AttributeEditor(nb1.propPanel, wx.ID_ANY, self, parent.GetId())
				nb1.UpdatePropertiesPage(newContent, self, parent)
		
		propertiesPage = nb1.GetPage(1)

		# gestion de la page Properties pour éviter le rechargement inutile
		if ((hasattr(propertiesPage, 'id') and propertiesPage.id != id(self)) or not hasattr(propertiesPage, 'id')) and nb1.GetSelection() == 1:
			newContent = AttributeEditor(nb1.propPanel, wx.ID_ANY, self, parent.GetId())
			nb1.UpdatePropertiesPage(newContent, self, parent)

		canvas.SetFocus()
		event.Skip()

#-----------------------------------------------------------
class LinesShape(Shape, Resizeable):
	"""
	"""
	
	def __init__(self, points):
		""" Constructor
		"""

		Shape.__init__(self)

		self.x = []
		self.y = []
		for p in points:
			self.x.append(p[0])
			self.y.append(p[1])
		
	def draw(self, dc):
		Shape.draw(self, dc)
		ind = 0
		try:
			while 1:
				dc.DrawLine(self.x[ind], self.y[ind], self.x[ind+1], self.y[ind+1])
				ind += 1
		except:
			pass
		
		# pour la fleche
		dc.DrawRectanglePointSize(wx.Point(self.x[-1]-10/2,self.y[-1]-10/2), wx.Size(10,10))
		
	def HitTest(self, x, y):

		if x < min(self.x)-3:return False
		if x > max(self.x)+3:return False
		if y < min(self.y)-3:return False
		if y > max(self.y)+3:return False
		
		ind=0
		try:
			while 1:
				x1 = self.x[ind]
				y1 = self.y[ind]
				x2 = self.x[ind+1]
				y2 = self.y[ind+1]
	
				top= (x-x1) *(x2 - x1) + (y-y1)*(y2-y1)
				distsqr = pow(x1-x2,2)+pow(y1-y2,2)
				u = float(top)/float(distsqr)
			
				newx = x1 + u*(x2-x1)
				newy = y1 + u*(y2-y1)
		
				dist = pow(pow(newx-x,2) + pow(newy-y,2),.5)
	
				if dist < 7: 
					return True
				ind = ind +1

		except IndexError:
			pass
		
		return False

	def AddPoint(self, point = (0,0)):
		''' Add point under LineShape
		'''
		x,y = point

		# insertion sur les morceaux de droites d'affines
		for i in range(len(self.x)-1):
			x1 = self.x[i]
			x2 = self.x[i+1]
			y1 = self.y[i]
			y2 = self.y[i+1]
			
			b = float(y2-(x2/x1)*y1)/float(1-(x2/x1))
			a = float(y1-b)/x1
			
			# si le point (x,y) appartient au morceau
			if a*x+b-3 <= y <= a*x+b+3 :
				self.x.insert(i+1, x)
				self.y.insert(i+1, y)
				break

#---------------------------------------------------------
class Editable:
	""" Editable class
	"""

	###
	def OnEditor(self, event):
		""" Method that edit the python code of associated atomic model of the codeBlock
		"""

		path = self.python_path
		name = os.path.basename(path)		
		mainW = event.GetClientData()
		editorFrame = Editor(mainW, wx.ID_ANY, name, self)
		
		# chargement du fichier dans la fenetre d'edition (self.text)
		try:
			file = open(path, 'r')
			text = file.read()
			file.close()
			editorFrame.text.SetValue(text)
			editorFrame.last_name_saved = path
			editorFrame.statusbar.SetStatusText('', 1)
			editorFrame.modify = False

		except Exception, info:
			dlg = wx.MessageDialog(editorFrame, _('Error opening file : %s\n'%info))
			dlg.ShowModal()
		
		editorFrame.Show()


#---------------------------------------------------------
class Structurable(Editable, Savable):
	""" Structurable class interface for DEVS coupled model integration
	"""

	def __init__(self):
		""" Constructor of Structurable class interface.
		"""

		# coupled DEVS instance
		self.coupledModel = None

		# path of py file for import process
		self.python_path = ''

		# args of constructor
		self.args = {}
		
	def AddCoupledModel(self, m):
		""" Add a DEVS coupled model instance to ContainerBlock.
		
			@param m: DEVS coupled model
			@type m: instance
		"""
		self.coupledModel = m
		
	def ConnectDEVSPorts(self, p1, p2):
		""" Connect DEVS ports
		
			@param p1: DEVS port
			@param p2: DEVS port
			
			@type p1: instance
			@type p2: instance
		"""
		assert(self.coupledModel != None)
		self.coupledModel.connectPorts(p1, p2)
		
	def ClearAllPorts(self):
		""" Clear all DEVS ports.
		"""
		self.coupledModel.IC = []
		self.coupledModel.EIC = []
		self.coupledModel.EOC = []
		
	def getDEVSModel(self):
		""" Return the DEVS coupled model.
		"""
	
		return self.coupledModel
	
	def setDEVSModel(self, m):
		"""
		Set the DEVS coupeld model.
		
		@param m: DEVS coupled model
		@type: instance
		"""
		self.coupledModel = m

#---------------------------------------------------------
class ConnectionShape(LinesShape, Resizeable, Selectable, Structurable):
	""" ConnectionShape class.
	"""


	def __init__(self):
		""" Constructor
		""" 
		LinesShape.__init__(self,[(0,0),(1,1)])
		Resizeable.__init__(self)
		Selectable.__init__(self)
		Structurable.__init__(self)
		self.input = None
		self.output = None

	def setInput(self, item, index):
		self.input = (item, index)
		
	def setOutput(self, item, index):
		self.output = (item, index)
		
	def getInput(self):
		return self.input
	
	def getOutput(self):
		return self.output
		
	def draw(self, dc):		
		if self.input:
			self.x[0], self.y[0] = self.input[0].getPort('output', self.input[1])
		if self.output:
			self.x[-1],self.y[-1] = self.output[0].getPort('input', self.output[1])
		LinesShape.draw(self, dc)

	def OnLeftDClick(self, event):
		# faire l'ajout d'un noeud
		x,y = event.GetPositionTuple()
		self.AddPoint((x,y))
		
	def __del__(self):
		pass

#---------------------------------------------------------
class Block(RoundedRectangleShape, Connectable, Resizeable, Selectable, Attributable, Rotable):
	""" Generic Block class.
	"""
	
	def __init__(self, label = 'Block', nb_inputs = 1, nb_outputs = 1):
		""" Constructor
		"""
	
		RoundedRectangleShape.__init__(self)
		Resizeable.__init__(self)
		Connectable.__init__(self, nb_inputs, nb_outputs)
		Attributable.__init__(self)
		self.AddAttributes(['label','pen','fill','input','output'])
		self.label = label
		self.id = 0
		self.nb_copy = 0	# nombre de fois que le bloc est copié (pour le label des blocks copiés
		
	###
	def draw(self, dc):
		RoundedRectangleShape.draw(self, dc)
		w,h =  dc.GetTextExtent(self.label)
		mx = int((self.x[0] + self.x[1])/2.0 )-int(w/2.0)
		my = int((self.y[0]+self.y[1])/2.0)-int(h/2.0)
		dc.DrawText(self.label, mx, my)
		self.w = self.x[1]- self.x[0]
		self.h = self.y[1]- self.y[0]
		
	###
	def OnLeftUp(self, event):
		pass

	###
	def leftUp(self, event):
		pass

	###
	def OnLeftDown(self, event):
		Attributable.ShowAttributes(self, event)
		event.Skip()
	###
	def OnProperties(self, event):
		mainW = wx.GetApp().GetTopWindow()
		f = AttributeEditor(mainW, wx.ID_ANY, self, mainW.GetId())
		f.Show()

	def __del__(self):

		# effacement du notebook "property"
		parent = wx.GetApp().frame
		nb1 = parent.nb1
		activePage = nb1.GetSelection()
		#si la page "Properties" est active alors la met a jour et on reste dessus
		if activePage == 1:
			nb1.UpdatePropertiesPage(nb1.defaultPropertiesPage(), self, parent)
	###
	def __repr__(self):
		s = _("\t Label: %s\n")%self.label
		s += "\t Input/Output: %s,%s\n"%(str(self.input), str(self.output))
		return s

#---------------------------------------------------------
class Achievable(Editable, Savable):
	"""Creates corresponding behavioral model
	"""

	###
	def __init__(self):
		""" Constructor
		"""

		Savable.__init__(self)

		#atomic model instance
		self.atomicModel = None
		#path of py file for import process
		self.python_path = ''
		#dictionnaire des arguments du constructeur
		self.args = {}

	###
	def getDEVSModel(self):
		return self.atomicModel
	
	###
	def setDEVSModel(self, m):
		self.atomicModel = m

	###
	def AddAtomicModel(self , m):
		#Add a corresponding behavioral model
		#self.setDEVSModel(m)
		
		# les port devs sont generes dans la partie simulation en fonction du nombre de ports graphiques
		if 'Sources' in str(m.__class__).split('.'):
			self.input = 0
			self.output = 1
		elif 'Sinks' in str(m.__class__).split('.') or 'To_Disk' in str(m.__class__).split('.'):
			self.input = 1
			self.output = 0
		else:
			pass
		
		# initialisation des arguments du constructeur pour l'atomic model
		d = inspect.getargspec(m.__init__)

		if sys.version >= "2.6":
			args = d.args
			args.remove('self')
			defaults = d.defaults
		else:
			args = d[0]
			args.remove('self')
			defaults = d[-1]

		if args != []:
			self.args = dict(map(lambda a,b: (a,b),args,defaults))
		
#---------------------------------------------------------
class CodeBlock(Block, Achievable):
	""" CodeBlock(label, inputs, outputs)
	"""

	###
	def __init__(self, label = 'CodeBlock', nb_inputs = 1, nb_outputs = 1):
		""" Constructor
		"""

		Block.__init__(self, label, nb_inputs, nb_outputs)
		Achievable.__init__(self)

	###
	def OnLeftDClick(self, event):
		self.OnProperties(event)

	###
	def OnRightDown(self, event):
		sys.stdout.write(_("This option has not been implemented yet.\n"))

	def OnExport(self, event):
		""" Method that export CodeBlock into a amd file
		"""

		mainW = wx.GetApp().GetTopWindow()
		parent = event.GetClientData()
		domain_path = os.path.join(os.path.dirname(os.getcwd()), DOMAIN_DIR)

		wcd = _('DEVSimPy Atomic Models Files (*.amd)|*.amd|All files (*)|*')
		save_dlg = wx.FileDialog(	parent, 
									message = _('Export file as...'), 
									defaultDir = domain_path, 
									defaultFile = str(self.label)+'.amd', 
									wildcard = wcd, 
									style = wx.SAVE | wx.OVERWRITE_PROMPT)

		if save_dlg.ShowModal() == wx.ID_OK:
			path = save_dlg.GetPath()
			label = os.path.basename(path)
			try:
				
				self.SaveFile(path)

				mainW.statusbar.SetStatusText(label + _(' Exported'), 0)
				mainW.statusbar.SetStatusText('', 1)
				
				# chemin absolu du repertoir contenant le fichier a exporter (str() pour eviter l'unicode)
				newExportPath = str(os.path.dirname(path))
				
				# si export dans un repertoire local on insert le chemin dans le fichier de config
				if not os.path.basename(mainW.tree.domainPath) in newExportPath.split(os.sep):
					# mise a jour du fichier .devsimpy
					mainW.exportPathsList = eval(mainW.cfg.Read("exportPathsList"))
					if newExportPath not in mainW.exportPathsList:
						mainW.exportPathsList.append(str(newExportPath))
					mainW.cfg.Write("exportPathsList", str(eval("mainW.exportPathsList")))
				
				# si la librairie est deja charger dans l'environnement on met à jour ces modeles
				if mainW.tree.IsChildRoot(os.path.basename(newExportPath)):
					mainW.tree.UpdateDomain(newExportPath)
			
			except IOError, error:
				dlg = wx.MessageDialog(parent, _('Error exported file %s\n')%error)
				dlg.ShowModal()
				
		save_dlg.Destroy()
	
	@BuzyCursorNotification
	@StatusBarNotification('Sav')
	def SaveFile(self, fileName = None):
		""" Function that save the diagram into a file
		"""
	
		if fileName is None:
			return False

		try:	
			f = gzip.GzipFile(filename = fileName, mode = 'wb', compresslevel = 9)
			cPickle.dump([self],f)
			f.close()
		except Exception, info:
			sys.stderr.write(_("Problem saving: %s -- %s\n")%(str(fileName), info))
			return False
		finally:
			return True

	@BuzyCursorNotification
	@StatusBarNotification('Load')
	def LoadFile(self, fileName = None):
		""" Function that load diagram from a file. 
			The file can be compressed (gzip bz2) or not
			If the file is compressed, it(s composed by two files: the devsimpy model and the associated .py 
		"""

		if fileName is None:
			return False

		# try to open f with compressed mode
		try:
			f = gzip.GzipFile(filename = fileName, mode='rb')
			f.read(1) # trigger an exception if is not compressed
			f.seek(0)

		except IOError:
			# not compressed file (very old version of devsimpy)
			try:
				f = open(fileName,'rb')
			except Exception, info:
				sys.stderr.write(_("Problem opening: %s -- %s \n")%(str(fileName), info))
				return False

		# try to load file and to restore the .py file
		try:
			tmp = cPickle.load(f)[0]
		except Exception, info:
			sys.stderr.write(_("Problem loading: %s -- %s \n")%(str(fileName), info))
			return False

		finally:
			return tmp

	###
	def __repr__(self):
		s = Block.__repr__(self)
		s+="\t Ad-hoc DEVS Model: %s \n"%str(self.python_path)
		return s

#---------------------------------------------------------
class ContainerBlock(Block, Diagram, Structurable):
	""" ContainerBlock(label, inputs, outputs)
	"""

	###
	def __init__(self, label = 'ContainerBlock', nb_inputs = 1, nb_outputs = 1):
		""" Constructor
		"""
		Block.__init__(self, label, nb_inputs, nb_outputs)
		Diagram.__init__(self)
		Structurable.__init__(self)
		self.pen = ['BLACK' , 1]
		self.fill= ['#dae0ff']
		
	###
	def OnLeftDClick(self, event):
		""" Left Double Click Event Handel
		"""
		canvas = event.GetEventObject()
		canvas.deselect()
		p = canvas.GetTopLevelParent()
		frame = DetachedFrame(parent = p, title = self.label, diagram = self, name = self.label)
		frame.Show()
		

	def OnExportXML(self, event):
		""" Method that export ContainerBlock into a XML file
		"""

		# Graph of diagram
		D = self.makeDEVSGraph(self, {})

		#print self.makeDEVSGraph(self, {}, str)

		mainW = wx.GetApp().GetTopWindow()
		parent = event.GetClientData()
		domain_path = os.path.join(os.path.dirname(os.getcwd()), DOMAIN_DIR)
		diagram = self

		wcd = _('XML Files (*.xml)|*.xml|All files (*)|*')
		save_dlg = wx.FileDialog(parent, message = _('Export file as...'), defaultDir = domain_path, defaultFile = str(diagram.label)+'.xml', wildcard = wcd, style = wx.SAVE | wx.OVERWRITE_PROMPT)
		if save_dlg.ShowModal() == wx.ID_OK:
			path = save_dlg.GetPath()
			try:
				self.makeDEVSXML(D, path)
				mainW.statusbar.SetStatusText(diagram.last_name_saved + _(' Exported'), 0)
				mainW.statusbar.SetStatusText('', 1)
			
			except IOError, error:
				dlg = wx.MessageDialog(parent, _('Error exported file %s\n')%error)
				dlg.ShowModal()
				
		save_dlg.Destroy()

		
	def OnExportCMD(self, event):
		""" Method that export ContainerBlock into a cmd file
		"""

		mainW = wx.GetApp().GetTopWindow()
		parent = event.GetClientData()
		domain_path = os.path.join(os.path.dirname(os.getcwd()), DOMAIN_DIR)
		diagram = self

		wcd = _('DEVSimPy Coupled Models Files (*.cmd)|*.cmd|All files (*)|*')
		save_dlg = wx.FileDialog(	parent, 
									message = _('Export file as...'), 
									defaultDir = domain_path, 
									defaultFile = str(diagram.label)+'.cmd', 
									wildcard = wcd, 
									style = wx.SAVE | wx.OVERWRITE_PROMPT)

		if save_dlg.ShowModal() == wx.ID_OK:
			path = save_dlg.GetPath()

			try:
				diagram.SaveFile(path)

				mainW.statusbar.SetStatusText(diagram.last_name_saved + _(' Exported'), 0)
				mainW.statusbar.SetStatusText('', 1)
				diagram.modify = False
				
				# chemin absolu du repertoir contenant le fichier a exporter (str() pour eviter l'unicode)
				newExportPath=str(os.path.dirname(path))
				
				# si export dans un repertoir local on insert le chemin dans le fichier de config
				if not os.path.basename(mainW.tree.domainPath) in newExportPath.split(os.sep):
					# mise a jour du fichier .devsimpy
					mainW.exportPathsList = eval(mainW.cfg.Read("exportPathsList"))
					if newExportPath not in mainW.exportPathsList:
						mainW.exportPathsList.append(str(newExportPath))
					mainW.cfg.Write("exportPathsList", str(eval("mainW.exportPathsList")))
				
				# si la librairie est deja charger dans l'environnement on met à jour ces modeles
				if mainW.tree.IsChildRoot(os.path.basename(newExportPath)):
					mainW.tree.UpdateDomain(newExportPath)
			
			except IOError, error:
				dlg = wx.MessageDialog(parent, _('Error exported file %s\n')%error)
				dlg.ShowModal()
				
		save_dlg.Destroy()

	def __repr__(self):
		s = Block.__repr__(self)
		s += _("\t Ad-hoc DEVS Model: %s \n"%str(self.python_path))
		return s

#---------------------------------------------------------
# Nodes
class Node(PointShape):
	""" Node(item, index, cf, type)
	
		Node class for connection between model.
	"""

	def __init__(self, item, index, cf, t='rect'):
		""" Construcotr.
		"""

		self.item = item
		self.index = index
		self.cf = cf
		#self.label = ''
		PointShape.__init__(self, type = t)
	
	####
	#def OnLeftDClick(self, event):
		#d = wx.TextEntryDialog(wx.GetApp().frame ,_('Node Label'), defaultValue = self.label, style = wx.OK)
		#d.ShowModal()
		## changement du label
		#self.label = d.GetValue()

	def showProperties(self):
		""" Call item properties.
		"""
		self.item.showProperties

class ConnectableNode(Node):
	""" ConnectableNode(item, index, cf)
	"""

	def __init__(self, item, index, cf):
		Node.__init__(self, item, index, cf, t = 'rondedrect')

class INode(ConnectableNode):
	""" INode(item, index, cf)
	"""

	def __init__(self, item, index, cf):
		ConnectableNode.__init__(self, item, index, cf)
	
	def move(self, x, y):
		self.cf.deselect()
		ci = ConnectionShape()
		self.cf.diagram.shapes.insert(0, ci)
		ci.setOutput(self.item, self.index)
		ci.x[0], ci.y[0] = self.item.getPort('input', self.index)
		self.cf.showOutputs()
		self.cf.select(ci)
	
	def leftUp(self,items):
		if len(items) == 1 and isinstance(items[0], ConnectionShape):
			cs = items[0]
			if cs.output is None:
				cs.setOutput(self.item,self.index)
				# Add connectionShapes to graphical models
				self.item.connections.append(cs)
				cs.input[0].connections.append(cs)
					
	def draw(self,dc):
		x,y = self.item.getPort('input', self.index)
		self.moveto(x, y)
		self.fill = ['GREEN']
		PointShape.draw(self, dc)
		
class ONode(ConnectableNode):
	""" ONode(item, index, cf)
	"""

	def __init__(self, item, index, cf):
		ConnectableNode.__init__(self, item, index, cf)
		
	def move(self, x, y):
		self.cf.deselect()
		ci = ConnectionShape()
		self.cf.diagram.shapes.insert(0, ci)
		ci.setInput(self.item, self.index)
		ci.x[1], ci.y[1] = self.item.getPort('output', self.index)
		self.cf.showInputs()
		self.cf.select(ci)

	def leftUp(self,items):
		if len(items) == 1 and isinstance(items[0], ConnectionShape):
			cs = items[0]
			if cs.input is None:
				cs.setInput(self.item, self.index)
				# Add connectionShapes to graphical models
				self.item.connections.append(cs)
				cs.output[0].connections.append(cs)
		
	def draw(self,dc):
		x,y=self.item.getPort('output', self.index)
		self.moveto(x, y)
		self.fill = ['RED']
		PointShape.draw(self, dc)

###
class ResizeableNode(Node):
	""" Resizeable(item, index, cf, type)
	"""

	def __init__(self, item, index, cf, t = 'rect'):
		Node.__init__(self, item, index, cf, t)
		self.fill = ['BLACK']

	def draw(self, dc):
		try:
			self.moveto(self.item.x[self.index], self.item.y[self.index])
		except IndexError:
			pass
		PointShape.draw(self, dc)
		
	def move(self, x, y):
		self.item.x[self.index] += x
		self.item.y[self.index] += y
		
	def OnDeleteNode(self, event):
		if isinstance(self.item, ConnectionShape):
			for x in self.item.x:
				if x-3 <= event.GetX() <= x+3:
					y = self.item.y[self.item.x.index(x)]
					if y-3 <= event.GetY() <= y+3:
						self.item.x.remove(x)
						self.item.y.remove(y)
		
#---------------------------------------------------------
class Port(CircleShape, Connectable, Selectable, Attributable, Rotable):
	""" Port(x1,y1, x2, y2, label)
	"""
	
	def __init__(self, x1, y1, x2, y2, label = 'Port'):
		""" Constructor
		"""

		CircleShape.__init__(self, x1, y1, x2, y2)
		Connectable.__init__(self)
		Selectable.__init__(self)
		Attributable.__init__(self)
		self.label = label
		self.id = 0
		self.args = {}
			
	def draw(self, dc):
		CircleShape.draw(self, dc)
		w,h =  dc.GetTextExtent(self.label)
		mx = int(self.x[0])+2
		my = int(self.y[1])
		dc.DrawText(self.label, mx, my)
	
	def leftUp(self,event):
		pass
 
	###
	def OnLeftDown(self,event):
		Attributable.ShowAttributes(self, event)
		event.Skip()	

	def OnProperties(self, event):
		mainW = wx.GetApp().frame
		f = AttributeEditor(mainW, wx.ID_ANY, self, mainW.GetId())
		f.Show(True)
	
	###
	def OnLeftDClick(self, event):
		self.OnProperties(event)
	
	def __del__(self):
		# effacement du notebook "property"
		nb1 = wx.GetApp().frame.nb1
		activePage = nb1.GetSelection()
		parent = wx.GetApp().frame
		#si la page "Properties" est active alors la met a jour et on reste dessus
		if activePage == 1:
			nb1.UpdatePropertiesPage(nb1.defaultPropertiesPage(), self, parent)

	def __repr__(self):
		s="\t Label: %s\n"%self.label
		return s

#------------------------------------------------------------------
class iPort(Port):
	""" IPort(label)
	"""

	def __init__(self, label = 'iPort'):
		""" Constructor
		""" 

		Port.__init__(self,50,60,100,120, label)
		self.AddAttributes(['label','pen','fill','id'])
		self.input = 0
		self.output = 1
		
	def getDEVSModel(self):
		return self

	#def __del__(self):
		#pass

	def __repr__(self):
		s = Port.__repr__(self)
		s+="\t id: %d \n"%self.id
		return s

#----------------------------------------------------------------
class oPort(Port):
	""" OPort(label)
	"""

	def __init__(self, label = 'oPort'):
		""" Construcotr
		"""

		Port.__init__(self,50,60,100,120, label)
		self.AddAttributes(['label','pen','fill', 'id'])
		self.input = 1
		self.output = 0

	def getDEVSModel(self):
		return self
		
	def __repr__(self):
		s = Port.__repr__(self)
		s+="\t id: %d \n"%self.id
		return s

#--------------------------------------------------
class ScopeGUI(CodeBlock):
	""" ScopeGUI(label) 
	"""

	def __init__(self, label = 'QuickScope'):
		""" Constructor
		"""

		CodeBlock.__init__(self, label, 1, 0)
		
	def OnLeftDClick(self,event):
		"""
		"""

		if self.atomicModel.results != {}:
			canvas = event.GetEventObject()
			if self.atomicModel.fusion:
				frame = Plot(canvas, wx.ID_ANY,_("Plotting %s")%self.label, self.atomicModel.results)
				frame.Center()
				frame.Show()
			else:
				for i in self.atomicModel.results:
					frame=Plot(canvas, wx.ID_ANY, _("Plotting %s on port %d")%(self.label,i), self.atomicModel.results[i])
					frame.Center()
					frame.Show()
		else:
			dial = wx.MessageDialog(None, _('No data available \n Go to the simulation process !'), 'Info', wx.OK)
			dial.ShowModal()
	
#------------------------------------------------
class DiskGUI(CodeBlock):
	""" DiskGUI(label)
	"""

	def __init__(self, label = 'DiskGUI'):
		""" Constructor
		"""
		CodeBlock.__init__(self, label, 1, 0)

	def OnLeftDClick(self,event):
		"""
		"""

		if self.atomicModel.results != {}:
			mainW = wx.GetApp().frame
			frame=Newt(mainW, wx.ID_ANY, _("SpreadSheet %s")%self.label, self.atomicModel.results)
			frame.Center()
			frame.Show()
		else:
			dial = wx.MessageDialog(None, _('No data available\n Go to the simulation process !'), 'Info', wx.OK)
			dial.ShowModal()

#----------------------------------------------------
class ExternalGenGUI(CodeBlock):
	"""
	"""

	def __init__(self, label = 'ExternalGen'):
		""" Constructor
		"""
		CodeBlock.__init__(self, label, 0, 1)
		
	def OnLeftDClick(self,event):
		"""
		"""

		wcd = _('Comma-separated values files (*.csv)|*.csv|All files(*)|*')
		# Create the dialog. In this case the current directory is forced as the starting
		# directory for the dialog, and no default file name is forced. This can easilly
		# be changed in your program. This is an 'open' dialog, and allows multitple
		# file selections as well.
		#
		# Finally, if the directory is changed in the process of getting files, this
		# dialog is set up to change the current working directory to the path chosen.
		
		dlg = wx.FileDialog(
			None, message =_("Choose a csv file"),
			defaultDir = HOME_PATH, 
			defaultFile = "",
			wildcard = wcd,
			style = wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
			)

		# Show the dialog and retrieve the user response. If it is the OK response, 
		# process the data.
		if dlg.ShowModal() == wx.ID_OK:
			# This returns a Python list of files that were selected.
			paths = dlg.GetPaths()
			
			self.atomicModel._T = []
			self.atomicModel._V = []
			
			self.atomicModel.fileName = paths[0]
		
		# Destroy the dialog. Don't do this until you are done with it!
		# BAD things can happen otherwise!
		dlg.Destroy()

#----------------------------------------------------------------------------------
class CustomDataTable(gridlib.PyGridTableBase):
	""" CustomDataTable(model)
	"""

	def __init__(self, model):
		""" Constructor
		"""

		gridlib.PyGridTableBase.__init__(self)

		self.colLabels = [_("Attribute"),_('Value'),_("Information")]	
		infoBlockLabelList = [_("Name"), _("Color and size pen"), _("Background Color"), _("Input port"), _("output port")]+\
				     [_("DEVS specific attribute")]*len(model.args)
		
		if isinstance(model, Port):
			infoBlockLabelList.insert(3,_('Id number'))
		
		self.dataTypes = []
		self.data = []

		### Graphical values fields
		n = len(model.GetAttributes())		# graphical attributes number
		for i in range(n):
			attr = str(model.GetAttributes()[i])
			val = getattr(model, attr)

			self.data.append([attr,val,infoBlockLabelList[i]])
			self.dataTypes.append(self.GetTypeList(val))

		## Behavioral values fields
		for i,s in enumerate(model.args):
			val = model.args[s]
			self.data.append([s, val, infoBlockLabelList[n+i]])
			self.dataTypes.append(self.GetTypeList(val))

		## Python File Path
		if hasattr(model, 'python_path'):
			val = os.path.basename(model.python_path)
			self.data.append(['python_path',val, "Python file path"])
			self.dataTypes.append(self.GetTypeList(val))
		
	def GetTypeList(self,val):
		if isinstance(val,bool):
			return [gridlib.GRID_VALUE_STRING,gridlib.GRID_VALUE_BOOL,gridlib.GRID_VALUE_STRING]
		elif isinstance(val,int):
			return [gridlib.GRID_VALUE_STRING,gridlib.GRID_VALUE_NUMBER + ':0,1000', gridlib.GRID_VALUE_STRING]
		elif isinstance(val,float):
			return [gridlib.GRID_VALUE_STRING,gridlib.GRID_VALUE_FLOAT + '10,10', gridlib.GRID_VALUE_STRING]
		elif isinstance(val,list):
			return [gridlib.GRID_VALUE_STRING,'list', gridlib.GRID_VALUE_STRING]
		else:
			return [gridlib.GRID_VALUE_STRING,gridlib.GRID_VALUE_STRING,gridlib.GRID_VALUE_STRING]
			
	def GetNumberRows(self):
		return len(self.data)

	def GetNumberCols(self):
		return len(self.data[0])

	def IsEmptyCell(self, row, col):
		try:
			return not self.data[row][col]
		except IndexError:
			return True

	# Get/Set values in the table.  The Python version of these
	# methods can handle any data-type, (as long as the Editor and
	# Renderer understands the type too,) not just strings as in the
	# C++ version.
	def GetValue(self, row, col):
		return self.data[row][col]

	def SetValue(self, row, col, value):
		# conserve le type de données dans la table :-)
		old = self.data[row][col]
		if value != '':
			if isinstance(old,float):
				self.data[row][col] = float(value)
			elif isinstance(old,bool):
				self.data[row][col] = bool(value)
			elif isinstance(old,int):
				self.data[row][col] = int(value)
			elif isinstance(old,list):
				self.data[row][col] = list(eval(str(value)))
			else:
				self.data[row][col] = value
		
	#--------------------------------------------------
	# Some optional methods

	# Called when the grid needs to display labels
	def GetColLabelValue(self, col):
		return self.colLabels[col]

	# Called to determine the kind of editor/renderer to use by
	# default, doesn't necessarily have to be the same type used
	# natively by the editor/renderer if they know how to convert.
	def GetTypeName(self, row, col):
		return self.dataTypes[row][col]

	# Called to determine how the data can be fetched and stored by the
	# editor and renderer.  This allows you to enforce some type-safety
	# in the grid.
	def CanGetValueAs(self, row, col, typeName):
		return typeName == self.dataTypes[row][col].split(':')[0]

	def CanSetValueAs(self, row, col, typeName):
		return self.CanGetValueAs(row, col, typeName)

#--------------------------------------------------------------------------
class PropertiesGridCtrl(gridlib.Grid):
	""" PropertiesGridCtrl (parent)
	"""

	def __init__(self, parent):
		""" Constructor
		"""

		gridlib.Grid.__init__(self, parent, -1)
		
		# local copy
		self.parent = parent

		# Table setting
		table = CustomDataTable(self.parent.model)
		self.SetTable(table, True)

		self.SetRowLabelSize(0)
		self.SetMargins(0,0)
		self.EnableDragRowSize(False)
		self.SetColSize(0,100)
		self.SetColSize(1,130)
		self.SetColSize(2,215)
		
		for i in range(len(parent.model.GetAttributes())+len(parent.model.args)):
			self.SetReadOnly(i, 0, True)
			self.SetReadOnly(i, 2, True)

		self.AutoSizeColumns()
		
		self.Bind(gridlib.EVT_GRID_CELL_CHANGE, self.OnAcceptProp)
		self.Bind(gridlib.EVT_GRID_SELECT_CELL, self.OnSelectProp)
		#self.Bind(gridlib.EVT_GRID_EDITOR_CREATED, self.OnGridEditorCreated)

	###
	def OnAcceptProp(self, evt):
		
		row = evt.GetRow()
		table= self.GetTable()
		prop = self.GetCellValue(row, 0)
		val = table.GetValue(row,1)

		model = self.parent.model
		
		# si behavioral propertie
		if model.args.has_key(prop):
			model.args[prop] = val
			# si attribut comportemental definit 
			# (donc au moins une simulation sur le modele, parce que les instances DEVS ne sont faites qu'à la simulation) 
			# alors on peut mettre a jour dynamiquement pendant la simulation :-)
			# attention necessite une local copy dans le constructeur des model DEVS (generalement le cas lorsqu'on veux réutiliser les param du constructeur dans les methodes)
			if model.atomicModel != None:
				setattr(model.atomicModel, prop, val)
		else:
			setattr(model, prop, val)

		### determination du canvas contenant les modeles à updater
		### si fenetre d'attribut est dans le NoteBook
		if isinstance(self.parent.GetParent(),wx.Notebook):			
			mainW = self.parent.GetTopLevelParent()
			parentWindow = mainW.FindWindowById(self.parent.modelParentId)
			
			### pas de codeFrame ouverte pour item ! Tout ce passe dans le nb2
			if isinstance(parentWindow, wx.Notebook):
				canvas = mainW.nb2.GetPage(mainW.nb2.GetSelection())
			### un codeFrame est ouvert pour le model
			elif isinstance(parentWindow, DetachedFrame):
				canvas = parentWindow.GetCanvas()
			else:
				canvas = parentWindow.nb2.GetPage(parentWindow.nb2.GetSelection())
				
		## si fenetre d'attribut autonome
		elif isinstance(self.parent.GetParent(),DetachedFrame):
			canvas = self.parent.GetParent().GetCanvas()
		## autonome et modèle dans nb 
		else:
			#mainW = self.parent.GetTopLevelParent().parent
			mainW = wx.GetApp().frame
			canvas = mainW.nb2.GetPage(mainW.nb2.GetSelection())

		## update graphique des modeles selectionnés
		self.parent.UpdateSelectedModels(canvas)

		## save modification
		if hasattr(model,'last_name_saved') and model.last_name_saved != '':
			model.SaveFile(model.last_name_saved)

		evt.Skip()

	###
	def OnSelectProp(self, evt):
		
		row = evt.GetRow()
		prop = self.GetCellValue(row, 0)
		
		if prop == 'fill':
			val = self.GetCellValue(row, 1)
			dlg = wx.ColourDialog(self.parent)
			dlg.GetColourData().SetChooseFull(True)
			if dlg.ShowModal() == wx.ID_OK:
				data = dlg.GetColourData()
				val = str([data.GetColour().Get()])
				self.SetCellValue(row,1,val)
			else:
				dlg.Destroy()
				return False

			dlg.Destroy()
			
		elif prop == 'fileName':
			wcd = 'Data files (*.dat)|*.dat|All files (*)|*'
			dlg = wx.FileDialog( self, message=_("Save file as ..."), defaultDir = HOME_PATH, defaultFile = "result", wildcard = wcd, style = wx.SAVE)
			if dlg.ShowModal() == wx.ID_OK:
				self.SetCellValue(row, 1, dlg.GetPath())
			else:
				dlg.Destroy()
				return False

			dlg.Destroy()

		elif prop == 'python_path':
			wcd = 'Python files (*.py)|*.py|All files (*)|*'
			model = self.parent.model
			domain_dir = os.path.dirname(model.python_path)
			
			dlg = wx.FileDialog( self, message=_("Import python file ..."), defaultDir = domain_dir, defaultFile = "", wildcard = wcd, style = wx.SAVE)
			if dlg.ShowModal() == wx.ID_OK:
				new_python_path = dlg.GetPath()
				self.SetCellValue(row, 1, new_python_path)

				# behavioral args update (because depends of the new class coming from new python file)
				cls = GetPythonClass(new_python_path)
				model.args = GetArgs(cls)
			else:
				dlg.Destroy()
				return False

			dlg.Destroy()
		else:
			pass
		
		self.OnAcceptProp(evt)
		
		# all properties grid update (because the python classe has been changed)
		# here, because OnAcceptProp should be executed before
		if prop == 'python_path':
			
			# table update
			table = CustomDataTable(model)
			self.SetTable(table, True)
			self.AutoSizeColumns()
			
			if isinstance(self.parent.model, Achievable):
				# code update
				new_code = CodeCB(self.parent, -1, self.parent.model)
				#self.parent.boxH.Remove(0)
				# DeleteWindows work better in vista
				self.parent.boxH.DeleteWindows()
				self.parent.boxH.AddWindow(new_code, 1, wx.EXPAND, userData='code')
				self.parent.boxH.Layout()

		self.parent.Refresh()
		evt.Skip()

	#def OnGridEditorCreated(self, event):
		#""" Bind the kill focus event to the newly instantiated cell editor """
		#editor = event.GetControl()
		#editor.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
		#event.Skip()

	#def OnKillFocus(self, event):
		## Cell editor's grandparent, the grid GridWindow's parent, is the grid.
		#grid = event.GetEventObject().GetGrandParent()
		#grid.SaveEditControlValue()
		#grid.HideCellEditControl()
		#event.Skip()

class CodeCB(wx.Choicebook):
	def __init__(self, parent, id, model = None):
		wx.Choicebook.__init__(self, parent, id)
		
		cls = GetPythonClass(model.python_path)

		pageTexts={	_('Doc'): inspect.getdoc(cls),
					_('Class'): inspect.getsource(cls),
					_('Constructor'):inspect.getsource(cls.__init__),
					_('Internal Transition'):inspect.getsource(cls.intTransition),
					_('External Transition'):inspect.getsource(cls.extTransition),
					_('Output Function'):inspect.getsource(cls.outputFnc), 
					_('Time Advance Function'):inspect.getsource(cls.timeAdvance)
				}
		
		# Now make a bunch of panels for the choice book
		count = 1
		#from Editor import DemoCodeEditor
		for nameFunc in pageTexts:
			win = wx.Panel(self)
			box = wx.BoxSizer( wx.HORIZONTAL)
			#st = DemoCodeEditor(self)
			#st.SetValue(pageTexts[nameFunc])
			st = wx.TextCtrl(win, wx.NewId(), '', style = wx.TE_MULTILINE)
			st.AppendText(str(pageTexts[nameFunc]))
			st.ShowPosition(wx.TOP)
			st.SetEditable(False)
			box.Add(st,1,wx.EXPAND)
			win.SetSizer(box)

			self.AddPage(win, nameFunc)

			#marche pas sous Windows
			if wx.Platform == '__WXGTK__':
				self.SetSelection(5)

		#self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.OnPageChanged)
		#self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGING, self.OnPageChanging)


	def OnPageChanged(self, event):
		old = event.GetOldSelection()
		new = event.GetSelection()
		sel = self.GetSelection()
		event.Skip()

	def OnPageChanging(self, event):
		old = event.GetOldSelection()
		new = event.GetSelection()
		sel = self.GetSelection()
		event.Skip()

###
class AttributeEditor(wx.Frame, wx.Panel):
	"""	Model attributes in Frame or Panel
	"""
	
	def __init__(self, parent, ID, model, modelParentId):
		"""	Constructor
			
			@param parent: wxWindows parent
			@param ID: Id
			@param title: window title
			@param model: considered model
			@param modelParentId: windows parent id (just for panel update)

			@type parent: instance
			@type ID: integer
			@type title: String
			@type model: Block or Port
			@type modelParentId: integer
		"""

		# pour gerer l'affichage dans la page de gauche dans le notebook
		if isinstance(parent, wx.Panel):
			wx.Panel.__init__(self, parent, ID)
			self.SetBackgroundColour(wx.WHITE)
		else:
			wx.Frame.__init__(self, parent, ID, model.label, wx.DefaultPosition, wx.Size(400, 550))
			self.SetIcon(self.MakeIcon(wx.Image(os.path.join(ICON_PATH_20_20, 'properties.png'), wx.BITMAP_TYPE_PNG)))
			
		#local copy
		self.model = model
		self.parent = parent
		self.modelParentId = modelParentId
		
		# pour garder la relation entre les propriétés affichier et le model associé (voir OnLeftClick de Block)
		self.parent.id = id(self.model)
	
		# properties list
		self.list = PropertiesGridCtrl(self)

		# Create a box sizer for self
		self.box = wx.BoxSizer(wx.VERTICAL)
		self.box.Add(self.list, 1, wx.EXPAND)
				
		## text doc de la classe
		#linecache.clearcache()
		#doc=inspect.getdoc(self.model.getDEVSModel().__class__)
		
		if isinstance(self.model, Achievable):
			self.boxH = wx.BoxSizer( wx.HORIZONTAL)
			self.code = CodeCB(self, -1, self.model)
			self.boxH.Add(self.code, 1, wx.EXPAND, userData='code')
			self.box.Add(self.boxH, 1, wx.EXPAND, userData='code')
	
		self.SetSizer(self.box)
		self.CenterOnParent()

	###
	def MakeIcon(self, img):
		"""
		The various platforms have different requirements for the
		icon size...
		"""

		if "wxMSW" in wx.PlatformInfo:
			img = img.Scale(16, 16)
		elif "wxGTK" in wx.PlatformInfo:
			img = img.Scale(22, 22)
		
		# wxMac can be any size upto 128x128, so leave the source img alone....
		return wx.IconFromBitmap(img.ConvertToBitmap() )

	###
	def UpdateSelectedModels(self, canvas):
		"""Methode that update the graphic of the models composing the canvas
		"""

		#all selected models in the canvas
		for subModel in canvas.getSelectedShapes():
			canvas.deselect(subModel)
			canvas.select(subModel)
		canvas.Refresh()
	
#---------------------------------------------------------
class DetachedFrame(wx.Frame):
	"""
	"""
	def __init__(self, parent=None, ID = wx.ID_ANY, title = "", diagram = None, name = ""):
		""" Constructor
		"""
		wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition, wx.Size(500, 300), name = name)

		self.SetIcon(parent.GetIcon())
		
		#local copy
		self.title = title
		self.parent = parent

		# Menu ToolBar
		vbox = wx.BoxSizer(wx.VERTICAL)
		toolbar = wx.ToolBar(self, wx.ID_ANY, style=wx.TB_HORIZONTAL | wx.NO_BORDER)
		toolbar.SetToolBitmapSize((25,25)) # juste for windows
		save = toolbar.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'save.png')), _('Save File') ,_('Save the current diagram'))
		saveas = toolbar.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'save_as.png')), _('Save File As'), _('Save the diagram with an another name'))
		toolbar.AddSeparator()
		zoomin = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'zoom+.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), _('Zoom +'), _('Zoom in'))
		zoomout = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'zoom-.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), _('Zoom -'), _('Zoom out'))
		unzoom=toolbar.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'no_zoom.png')), _('AnnuleZoom'),_('Initial view'))
		toolbar.AddSeparator()
		priority = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'priority.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), _('Priority'), _('Activation model priority'))
		simulation = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'simulation.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), _('Simulation'), _('Simulate the diagram'))
		toolbar.Realize()

		# on ne permet la simulation que pour les codeFrame detaché par pour les modeles couplés
		if isinstance(self.parent, DetachedFrame):
			toolbar.EnableTool(4, False)

		# Canvas Stuff
		self.canvas = ShapeCanvas(self,wx.ID_ANY)
		self.canvas.SetDiagram(diagram)
		self.canvas.SetBackgroundColour(wx.WHITE)
		self.canvas.scalex = 1.0
		self.canvas.scaley = 1.0

		# sans ca le EVT_KEY_DOWN ne fonctionne pas
		self.canvas.SetFocus()
		
		vbox.Add(toolbar, 0, wx.EXPAND, border = 5)
		vbox.Add(self.canvas, 1, wx.EXPAND, border = 5)

		self.SetSizer(vbox)
		
		self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)
		self.statusbar.SetFieldsCount(3)
		self.statusbar.SetStatusWidths([-5, -2, -1])

		self.Bind(wx.EVT_TOOL, self.OnZoomIn, zoomin)
		self.Bind(wx.EVT_TOOL, self.OnZoomOut, zoomout)
		self.Bind(wx.EVT_TOOL, self.OnAnnuleZoom, unzoom)
		self.Bind(wx.EVT_TOOL, self.OnSimulation, simulation)
		self.Bind(wx.EVT_TOOL, self.OnPriority, priority)
		self.Bind(wx.EVT_TOOL, self.OnSaveFile, save)
		self.Bind(wx.EVT_TOOL, self.OnSaveAsFile, saveas)
		self.Bind(wx.EVT_CLOSE,self.OnCloseWindow)

		self.Center()	

	def GetCanvas(self):
		return self.canvas

	def OnCloseWindow(self, event):
		self.Destroy()
		
	def OnZoomIn(self,event):
		self.canvas.scalex = max(self.canvas.scalex+.05, .3)
		self.canvas.scaley = max(self.canvas.scaley+.05, .3)
		self.canvas.Refresh()
		self.statusbar.SetStatusText(_('Zoom In'))

	def OnZoomOut(self,event):
		self.canvas.scalex = self.canvas.scalex-.05
		self.canvas.scaley = self.canvas.scaley-.05
		self.canvas.Refresh()
		self.statusbar.SetStatusText(_('Zoom Out'))

	def OnAnnuleZoom(self,event):
		self.canvas.scalex = 1.0
		self.canvas.scaley = 1.0
		self.canvas.Refresh()
		self.statusbar.SetStatusText(_('No Zoom'))

	#------------------------------------------------------------
	def OnSaveFile(self, event):
		currentPage = self.canvas
		diagram = currentPage.diagram

		if diagram.last_name_saved:
			assert(os.path.isabs(diagram.last_name_saved))
		
			if diagram.SaveFile(diagram.last_name_saved):
					
					diagram.modify = False
					self.statusbar.SetStatusText(os.path.basename(diagram.last_name_saved) + _(' saved'), 0)
					self.statusbar.SetStatusText('', 1)
				
					#Refresh corresponding page in nb2
					self.parent.nb2.GetPageByName(os.path.basename(diagram.last_name_saved)).Refresh()
					# Refresh canvas
					currentPage.Refresh()
			else:
				dlg = wx.MessageDialog(self, _('Error saving file %s\n')%os.path.basename(diagram.last_name_saved))
				dlg.ShowModal()
		else:
			self.OnSaveAsFile(event)

	def OnSaveAsFile(self, event):
		currentPage =self.canvas
		diagram = currentPage.diagram
		
		wcd = _('DEVSimPy files (*.dsp)|*.dsp|All files (*)|*')
		save_dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=HOME_PATH, defaultFile='', wildcard=wcd, style=wx.SAVE | wx.OVERWRITE_PROMPT)
		if save_dlg.ShowModal() == wx.ID_OK:
			path = save_dlg.GetPath()

			#ajoute .dsp si il existe pas ou si pas de .cmd
			if not path.endswith('.dsp') and not path.endswith('.cmd'):
				path=''.join([str(path),'.dsp'])
				
				#sauvegarde dans le nouveau fichier
				if diagram.SaveFile(path):
					diagram.last_name_saved = path
					self.SetTitle(os.path.basename(path))
					self.statusbar.SetStatusText('', 1)

				else:
					dlg = wx.MessageDialog(self, _('Error saving file %s\n')%os.path.basename(diagram.last_name_saved))
					dlg.ShowModal()

		save_dlg.Destroy()

	def OnSimulation(self, event):
		# on ne permet la simulation que pour les codeFrame detaché (pour pour les modeles couplé)
		if not isinstance(self.parent, DetachedFrame):
			self.parent.OnSimulation(event)

	def OnPriority(self,event):
		currentPage = self.canvas
		diagram = currentPage.diagram
		diagram.OnPriority(parent=self)

	def newCodeBlock(self, event):
		i = CodeBlock()
		self.canvas.AddShape(i)
		self.canvas.deselect()
		self.canvas.Refresh()

	def newContBlock(self, event):
		i = ContainerBlock()
		self.canvas.AddShape(i)
		self.canvas.deselect()
		self.canvas.Refresh()
				
	def newPointShape(self, event):
		i = PointShape(50,50)
		self.canvas.AddShape(i)
		self.canvas.deselect()
		self.canvas.Refresh()
		
	def newLinesShape(self, event):
		points=[
			(5,30),(10,20),(20,25),(30,50),(40,70),
			(50,30),(60,20),(70,25),(80,50),(90,70),
			(100,30),(110,20),(115,25),(120,50),(125,70),
			(130,30),(135,20),(140,25),(150,50),(160,70),
			(165,30),(170,20),(175,25),(180,50),(200,70),
			]
		i = LinesShape(points)
		self.canvas.AddShape(i)
		self.canvas.deselect()
		self.canvas.Refresh()
		
class MyApp(wx.App):
	def OnInit(self): 
		frame = DetachedFrame(None,wx.ID_ANY,'DEVSimPy DetachedFrame Test',ContainerBlock())
		frame.newCodeBlock(self)
		frame.newContBlock(self)
		frame.Show()
		return True

########################################

if __name__ == '__main__':
	app = MyApp(0)
	app.MainLoop()
