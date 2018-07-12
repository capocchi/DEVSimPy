# -*- coding: utf-8 -*-

"""
Name: XML.py
Brief descritpion: All classes and functions linked with xml aspects
Author(s): L. Capocchi <capocchi@univ-corse.fr>
Version:  1.0
Last modified: 2012.12.18
GENERAL NOTES AND REMARKS:

GLOBAL VARIABLES AND FUNCTIONS:
"""

import os
import sys
import re
import copy
import tempfile

import xml.etree.ElementTree as ET
from xml.dom import minidom

if __name__ == '__main__':
    import __builtin__
    import sys
    ABS_HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
    __builtin__.__dict__['GUI_FLAG'] = True
    __builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {'PyDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyDEVS'),
									'PyPDEVS_221':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs221' ,'src'),
									'PyPDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','old')}
    __builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = 'PyDEVS'
    __builtin__.__dict__['HOME_PATH'] = ABS_HOME_PATH

import Container
import Components

def makeDEVSXML(label, D, filename):
	""" Make XML file from D graph of the diagram
	"""

	# build a tree structure
	root = ET.Element("CoupledModel", {'xmlns:xsi':"http://www.w3.org/2001/XMLSchema-instance", 'xmlns:xsd':"http://www.w3.org/2001/XMLSchema"})

	nom = ET.SubElement(root, "nom")
	nom.text = label

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
		if isinstance(component, Container.iPort):
			# nb iport
			n = ET.SubElement(inp, "nom")
			s = ET.SubElement(n, "string")
			s.text = component.label
			# IC
			for d in D[component]:
				for comp in d:
					c = ET.SubElement(ioc, "coupling")
					s = ET.SubElement(c, "source")
					s.text = label
					ps = ET.SubElement(c, "portSource")
					ps.text = str(d[comp][0])
					dest = ET.SubElement(c, "destination")
					dest.text = comp.label
					pd = ET.SubElement(c, "portDestination")
					pd.text = str(d[comp][1])

		elif isinstance(component, Container.oPort):
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
					dest.text = label
					pd = ET.SubElement(c, "portDestination")
					pd.text = str(d[comp][0])
		else:
			# IC
			for d in D[component]:
				for comp in filter(lambda c: isinstance(c, Container.Block),d):
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
			for i in xrange(component.input):
				s = ET.SubElement(n, "string")
				# label port dont exist ! replace by the port id
				s.text = str(i)
			po = ET.SubElement(model, "portsOut")
			n = ET.SubElement(po, "nom")
			for i in xrange(component.output):
				s = ET.SubElement(n, "string")
				s.text = str(i)

	## wrap it in an ElementTree instance, and save as XML
	tree = ET.ElementTree(root)
	file = open(filename, "w")
	file.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>" + "\n")
	tree.write(file)
	file.close()

def getDiagramFromXML(xml_file="", name="", canvas=None, D={}):
	"""
	"""

	import WizardGUI

	xmldoc = minidom.parse(xml_file)

	### all item [2:] for id 0 and 1
	itemlist = xmldoc.getElementsByTagName('mxCell')[2:]

	### item corresponding to the block
	blocklist = []
	### item corresponding to the connection
	connectionlist = []
	for s in itemlist:
		if s.attributes.has_key('source') and s.attributes.has_key('target'):
			connectionlist.append(s)
		else:
			blocklist.append(s)

	#mxGraphModel = xmldoc.getElementsByTagName('mxGraphModel')[0]
	#dx = int(mxGraphModel.attributes['dx'].value)
	#dy = int(mxGraphModel.attributes['dy'].value)

	### parent of all block is canvas
	D['1'] = canvas

	### make block (atomic or coupled model)
	while(blocklist!=[]):

		s = blocklist[0]

		name = s.attributes['value'].value
		if s.attributes.has_key('style'):

			### coupled model have swimlane style or *couple{d}* in value filed
			if s.attributes['style'].value == 'swimlane' or re.match('[a-zA-Z0-9_ ]*[c|C]oupl[ed|e|é][a-zA-Z0-9_ ]*',name, re.IGNORECASE):
				attr = s.getElementsByTagName('mxGeometry')[0].attributes
				temp = tempfile.NamedTemporaryFile(suffix='.py')
				temp.write(WizardGUI.coupledCode('CoupledModel'))
				temp.seek(0)

				block = Components.BlockFactory.CreateBlock(x=int(attr['x'].value), y=int(attr['y'].value), name=name, python_file=temp.name, canvas=canvas)
				block.label = name

				parent_id = s.attributes['parent'].value
				id = str(s.attributes['id'].value)
				if parent_id == '1':
					canvas.AddShape(block)
					D[id] = block
					del blocklist[0]

				elif parent_id in D.keys():
					canvas_parent = D[parent_id]
					canvas_parent.AddShape(block)
					D[id] = block
					del blocklist[0]

				else:
					blocklist.insert(len(blocklist),blocklist.pop(0))

			elif re.match('[a-zA-Z0-9_ ]*[a|A]tomi[c|que][a-zA-Z0-9_ ]*',name, re.IGNORECASE):
				attr = s.getElementsByTagName('mxGeometry')[0].attributes
				temp = tempfile.NamedTemporaryFile(suffix='.py')
				temp.write(WizardGUI.atomicCode('AtomicModel'))
				temp.seek(0)

				block = Components.BlockFactory.CreateBlock(x=int(attr['x'].value), y=int(attr['y'].value), name=name, python_file=temp.name, canvas=canvas)
				block.label = name

				parent_id = s.attributes['parent'].value
				id = str(s.attributes['id'].value)

				if parent_id == '1':
					canvas.AddShape(block)
					D[id] = block
					del blocklist[0]

				elif parent_id in D.keys():
					canvas_parent = D[parent_id]
					canvas_parent.AddShape(block)
					D[id] = block
					del blocklist[0]

				else:
					blocklist.insert(len(blocklist),blocklist.pop(0))

		elif s.attributes.has_key('vertex'):
			if s.attributes['vertex'].value == '1' or re.match('[a-zA-Z0-9_ ]*[a|A]tomi[c|que][a-zA-Z0-9_ ]*',name, re.IGNORECASE):
				attr = s.getElementsByTagName('mxGeometry')[0].attributes
				temp = tempfile.NamedTemporaryFile(suffix='.py')
				temp.write(WizardGUI.atomicCode('AtomicModel'))
				temp.seek(0)

				block = Components.BlockFactory.CreateBlock(x=int(attr['x'].value), y=int(attr['y'].value), name=name, python_file=temp.name, canvas=canvas)
				block.label = name

				parent_id = s.attributes['parent'].value
				id = str(s.attributes['id'].value)
				if parent_id == '1':
					canvas.AddShape(block)
					D[id] = block
					del blocklist[0]

				elif parent_id in D.keys():
					canvas_parent = D[parent_id]
					canvas_parent.AddShape(block)
					D[id] = block
					del blocklist[0]

				else:
					blocklist.insert(len(blocklist),blocklist.pop(0))
		else:
			sys.stdout.write(_('Element not considered!\n'))

	### make connection
	while(connectionlist != []):
		s = connectionlist[0]

		source_id = s.attributes['target'].value
		target_id = s.attributes['source'].value
		parent_id = s.attributes['parent'].value
		#style = s.attributes['style'].value.split(';')

		source = D[source_id]
		target = D[target_id]
		c = D[parent_id]

		if source in canvas.diagram.shapes and target in canvas.diagram.shapes:
			a,b = canvas.GetNodeLists(source, target)
			if a == [] or b == []:
				a,b = canvas.GetNodeLists(target,source)
			canvas.sourceNodeList, canvas.targetNodeList = a,b
			
			if canvas.sourceNodeList != [] and canvas.targetNodeList !=[]:
				canvas.makeConnectionShape(canvas.sourceNodeList[0], canvas.targetNodeList[0])

		del connectionlist[0]

def getDiagramFromXMLSES(xmlses_file="", canvas=None):
	"""
	"""

	def GetParent(node):
		for s in blocklist:
			if node.attributes['parentuid'].value == s.attributes['uid'].value:
				return s
		return False

	def GetChild(node):
		for s in blocklist:
			if s.attributes['parentuid'].value == node.attributes['uid'].value:
				return s
		return node	

	def GetNodeFromUID(uid):
		''' Return node form uid
		'''
		for b in blocklist:
			if b.attributes['uid'].value == uid:
				return b
		#if D != {}:
		#	for k,v in D.items():
		#		if v['uid'] == uid:
		#			return k
		#		else:	
		#			for d in filter(lambda a: isinstance(a,dict),v['components']):
		#				return GetNodeFromUID(uid,{d['node']:d})
	
	def InsertElemFromUID(elem,uid,D):
		''' Update and return the new D with new elem into the components of the uid coupled model
			elem: new element
			uid: uid of the coupled model 
			D: the dictionary to udpade
		'''
		if D != {}:
			for k,v in D.items():
				if v['uid'] == uid:
					D[k]['components'].append(elem)
					return D
				else:
					for d in filter(lambda a: isinstance(a,dict),v['components']):	
						return InsertElemFromUID(elem,uid,{d['node']:d})

	def GetDiagram(canvas, D, parent_block=None):
		''' Build the DEVSimpy diagram with the creation of the block models (atomic and coupled) and ports (input and output)
		'''
		if D != {}:
			for k,v in D.items():
				if v.has_key('components'):
    				### coupled model
					name = k.attributes['name'].value
					temp = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
					temp.write(WizardGUI.coupledCode('CoupledModel'))
					temp.seek(0)
					nbi,nbo = map(len,GetNbPort(k))
					cp_block = Components.BlockFactory.CreateBlock(x=100, y=100, inputs = nbi, outputs = nbo, name=name, python_file=temp.name, canvas=canvas)
					cp_block.label = name
					
					parent_block.AddShape(cp_block)

					for d in v['components']:
						if isinstance(d, dict):
							GetDiagram(canvas,{d['node']:d}, cp_block)
						else:
							GetDiagram(canvas,{d:{}}, cp_block)

					return parent_block
				else:
    				### atomic model
					name = k.attributes['name'].value
					temp = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
					temp.write(WizardGUI.atomicCode('AtomicModel'))
					temp.seek(0)
					nbi,nbo = map(len,GetNbPort(k))
					am_block = Components.BlockFactory.CreateBlock(x=100, y=100, inputs = nbi, outputs = nbo, name=name, python_file=temp.name, canvas=canvas)
					am_block.label = name
					
					parent_block.AddShape(am_block)

					return True

	def GetNbPort(node):
		''' Get a tuple that contain a list of input an output ports
		'''
		iport = []
		oport = []
		connectionlist = xmldoc.getElementsByTagName('coupling')
		name = node.attributes['name'].value
		for c in connectionlist:
			if name == c.attributes['sinkname'].value:
				p = c.attributes['sinkport'].value
				if p not in oport:
					oport.append(p)
			elif name == c.attributes['sourcename'].value:
				p = c.attributes['sourceport'].value
				if p not in iport:
					iport.append(p)

		### if numer od ports processing faild with name, try with uid (node correspond by uid often for multiaspect)
		if iport==oport==[]:
			uid = node.attributes['uid'].value
			for c in connectionlist:
				if uid == c.attributes['sinkuid'].value:
					p = c.attributes['sinkport'].value
					if p not in oport:
						oport.append(p)
				elif uid == c.attributes['sourceuid'].value:
					p = c.attributes['sourceport'].value
					if p not in iport:
						iport.append(p)

		return (iport, oport)

	def GetDiagramCoupling(canvas, D, parent_block=None):
    		''' Build the DEVSimpy diagram coupling 
		'''
		### make connection
		connectionlist = xmldoc.getElementsByTagName('coupling')

		### all blocks
		blocks = canvas.diagram.GetFlatBlockShapeList()

		### make connection
		while(connectionlist != []):
    		
			### take the first connection object (deleted at the end of while)
			s = connectionlist[0]

			### find corresponding block
			source_name = GetNodeFromUID(s.attributes['sourceuid'].value).attributes['name'].value
			target_name = GetNodeFromUID(s.attributes['sinkuid'].value).attributes['name'].value
			source_port_num =  s.attributes['sourceport'].value
			target_port_num =  s.attributes['sinkport'].value
			diagram_name = s.parentNode.attributes['name'].value

			### find the graphic block of the source, target and diagram
			source = target = diagram = None
			for b in blocks:
				if b.label == source_name:
					source = b
				if b.label == target_name:
					target = b
				if b.label == diagram_name:
					diagram = b

			### if source or target is the diagram, we change them with the corresponding iPort or oPort 
			if diagram == source:
				for m in filter(lambda a: isinstance(a,Container.iPort),source.GetShapeList()):
					if int(m.id)+1 == int(source_port_num):
						source = m

			if diagram == target:
				for n in filter(lambda a: isinstance(a,Container.oPort),target.GetShapeList()):
					if int(n.id)+1 == int(target_port_num):
						target = n

			### add the connexion to the diagram
			ci = Container.ConnectionShape()
			diagram.shapes.insert(0, ci)

			### find sourceNode and targetNode
			a,b = canvas.GetNodeLists(source, target)
			if a == [] or b == []:
				a,b = canvas.GetNodeLists(target,source)
			
			### GetNideList is not well ordered (TODO)
			if isinstance(a[0], Container.ONode):
				sourceNode, targetNode = a[0],b[0]
			else:
				sourceNode, targetNode = b[0],a[0]
			
			### item of node must be overwritted
			sourceNode.item = source
			targetNode.item = target
		
			### connexion
			if isinstance(sourceNode,  Container.ONode):
				ci.setInput(sourceNode.item, sourceNode.index)
				ci.x[0], ci.y[0] = sourceNode.item.getPortXY('output', sourceNode.index)
				ci.x[1], ci.y[1] = targetNode.item.getPortXY('input', targetNode.index)
				ci.setOutput(targetNode.item, targetNode.index)
			else:
				ci.setInput(targetNode.item, targetNode.index)
				ci.x[1], ci.y[1] = sourceNode.item.getPortXY('output', sourceNode.index)
				ci.x[0], ci.y[0] = targetNode.item.getPortXY('input', targetNode.index)
				ci.setOutput(sourceNode.item, sourceNode.index)
		
			### delete the first selected cinnection objet
			del connectionlist[0]
		
		return canvas.diagram

	def XMLToDict(blocklist):		
		### dictionnary building
		D = {}
		### Add high level coupled models
		for cm in filter(lambda a: a.attributes['parentuid'].value == '1' and a.attributes['type'].value == "Aspect Node", blocklist):
			### change the name with parent (comparing uid and parentuid)
			cm.attributes['name'].value = GetParent(cm).attributes['name'].value
			name = cm.attributes['name'].value
			uid = cm.attributes['uid'].value
			D[cm] = {'node':cm, 'uid':uid, 'name':name, 'components':[]}

		### Add other sub coupled models
		for uid in range(2,100):
			for sub_cm in filter(lambda a: a.attributes['parentuid'].value == str(uid) and a.attributes['type'].value == "Aspect Node", blocklist):
				sub_uid =  GetParent(sub_cm).attributes['parentuid'].value
				for parent_cm in D:
					parent_uid = parent_cm.attributes['uid'].value
					if parent_uid == sub_uid:
						### change the name with parent (comparing uid and parentuid)
						sub_cm.attributes['name'].value = GetParent(sub_cm).attributes['name'].value
						name = sub_cm.attributes['name'].value
						uid = sub_cm.attributes['uid'].value
						D[parent_cm]['components'].append({'node':sub_cm,'uid':uid,'name':name,'components':[]})

		### Add atomic models
		for am in filter(lambda a: a.attributes['type'].value == "Entity Node" and GetChild(a).attributes['type'].value != "Aspect Node", blocklist):
			am_parent_uid = am.attributes['parentuid'].value
			InsertElemFromUID(am,am_parent_uid,D)

		return D

	import WizardGUI

	try:
		xmldoc = minidom.parse(xmlses_file)
	except Exception, info:
		sys.stdout.write('Error importing %s: %s\n' % (xmlses_file, info))
		sys.stdout.write('Please check the XML SES file\n')
		return False

	### blocklist contains all the treenode xml nodes
	global blocklist
	blocklist = xmldoc.getElementsByTagName('treenode')

	D = XMLToDict(blocklist)

	if D != {}:
		try:
			### Make the DEVSimPy diagram
			dia = GetDiagram(canvas, D, parent_block=canvas)
		except Exception, info:
			sys.stdout.write(_('Error making the diagram from XML SES: %s\n')%info)
			return False
		else:
			try:
				### Make the DEVsimPy coupling
				dia = GetDiagramCoupling(canvas,D,parent_block=canvas)
			except Exception, info:
				sys.stdout.write(_('Error making the coupling into the diagram from XML SES: %s\n')%info)
				return False
			else:	
				return dia
	else:
		sys.stdout.write(_("XML SES file seems don't contain models!\n"))
		return False

if __name__ == '__main__':
	import wx

	### ------------------------------------------------------------
	class TestApp(wx.App):
		""" Testing application
		"""

		def OnInit(self):

			import DetachedFrame
			import __builtin__
			import gettext
			from DomainInterface.DomainStructure import DomainStructure
			from DomainInterface.DomainBehavior import DomainBehavior

			__builtin__.__dict__['ICON_PATH']='icons'
			__builtin__.__dict__['ICON_PATH_16_16']=os.path.join(ICON_PATH,'16x16')
			__builtin__.__dict__['NB_HISTORY_UNDO']= 5
			__builtin__.__dict__['DOMAIN_PATH']='Domain'
			
			__builtin__.__dict__['FONT_SIZE']=12
			__builtin__.__dict__['_'] = gettext.gettext
			__builtin__.__dict__['LOCAL_EDITOR'] = False

			diagram = Container.Diagram()
			
			self.frame = DetachedFrame.DetachedFrame(None, -1, "Test", diagram)
			newPage = Container.ShapeCanvas(self.frame, wx.NewId(), name='Test')
			newPage.SetDiagram(diagram)

			path = os.path.join(os.path.expanduser("~"),'Downloads','example.xmlsestree')
			getDiagramFromXMLSES(path, canvas=newPage)
			#diagram.SetParent(newPage)

			self.frame.Show()

			return True

		def OnQuit(self, event):
			self.Close()

	app = TestApp(0)
	app.MainLoop()