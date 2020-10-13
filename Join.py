# -*- coding: utf-8 -*-

import sys
import os

import Container
from Utilities import getOutDir

def makeJoin(diagram = None, addInner = [], liaison = [], model = {}, bool = False, x = [40], y = [40], labelEnCours = ""):
	"""
	"""
	# print "--------------------------------------"
	#Largeurs et hauteurs d'un modele de base
	dim_m_width = 100
	dim_m_height = 60

	if bool == True:
		if labelEnCours == "DoubleAdd":
			print(" --> " , diagram , " <-- ")
		if isinstance(diagram, Container.Diagram) and not isinstance(diagram, Container.ContainerBlock):
			# print "cest un diagram mais pas un container block ..."
			model = addModel(model, diagram, labelEnCours, 20, 20, 1300, 300)[:1][0];
			addInner = makeAddInner(diagram, addInner)
		else:
			model = addModel(model, diagram, None, 20, 20, 1300, 300)[:1][0];
			addInner = makeAddInner(diagram, addInner)

	for c in diagram.GetShapeList():

		if isinstance(c, Container.ConnectionShape):
			# print "Le C actuel est un ConnectionShape"
			model1, portNumber1 = c.input
			model2, portNumber2 = c.output
			if (isinstance(model1, Container.iPort) and isinstance(model2, (Container.ContainerBlock, Container.CodeBlock))):
				# print "-> 1 <-"
				liaison.append(labelEnCours.replace(' ', '_')+".port(\"i\", \"in"+str(model1.id)+"\").joint("+model2.label.replace(' ', '_')+".port(\"i\", \"in"+str(portNumber2)+"\"), arrow);\n")
				model , x, y = addModel(model, model2, None, x, y, dim_m_width, dim_m_height);
			elif (isinstance(model1, (Container.ContainerBlock, Container.CodeBlock)) and isinstance(model2, Container.oPort)):
				# print "-> 2 <-"
				liaison.append(model1.label.replace(' ', '_')+".port(\"o\", \"out"+str(portNumber1)+"\").joint("+labelEnCours.replace(' ', '_')+".port(\"o\", \"out"+str(model2.id)+"\"), arrow);\n")
				model , x, y = addModel(model, model1, None, x, y, dim_m_width, dim_m_height);
			elif (isinstance(model1, (Container.ContainerBlock, Container.CodeBlock)) and isinstance(model2, (Container.ContainerBlock, Container.CodeBlock))):
				# print "-> 3 <-"
				liaison.append(model1.label.replace(' ', '_')+".port(\"o\", \"out"+str(portNumber1)+"\").joint("+model2.label.replace(' ', '_')+".port(\"i\", \"in"+str(portNumber2)+"\"), arrow);\n")
				model , x, y = addModel(model, model1, None, x, y, dim_m_width, dim_m_height);
			# print "----------------------"
			# print "----------------------"

		#if the component is a container block achieve the recursivity
		elif isinstance(c, Container.ContainerBlock):
			# print "Le C actuel est un containerBlock"
			addInner = makeAddInner(c, addInner)
			bool = False
			makeJoin(c, addInner, liaison, model, bool, x, y, c.label)
	# print "--------------------------------------------"
	return [model, liaison, addInner]

def xyPositionDefine(x, y, tmp, dim_m_height):

	if isinstance(x, int):
		pass
	elif isinstance(x, list):
		lenX = len(x) -1
		tmp_x = x[lenX]

		lenY = len(y) -1
		tmp_y = y[lenY]

		if tmp_x > 1080:
			tmp_x = 40
			tmp_y = tmp_y + 100 + dim_m_height
			x.append(tmp_x)
			y.append(tmp_y)
		else:
			tmp_x = tmp_x + tmp + 160
			x.append(tmp_x)

	return [x, y]

def makeAddInner(c, addInner):
	# Re-vérification pour ere sur qu'il s'agit bien d'un modele couple
	if isinstance(c, Container.ContainerBlock):
		# print "Le C actuel est un containerBlock"
		shapeList = c.GetShapeList()
		for s in shapeList:
			#Si il s'agit d'un modele atom ou couple, alors on l'ajoute a notre liste addInner
			if (isinstance(s, Container.CodeBlock) or isinstance(s, Container.ContainerBlock)):
				addInner.append(str(c.label.replace(' ', '_')+".addInner("+s.label.replace(' ', '_')+");"))
	return addInner
'''
def coupledStruct(c):
	tab = []
	bool = False
	shapeList = c.GetShapeList()
	for s in shapeList:
	#On met le boolean à true, pour signaler un modele couple dans le tableau des enfants.
		if isinstance(s, ContainerBlock):
			bool = True
		# Si bool = True , alors on rappelle la fonction coupledStruct sur le fils couple.
		if bool:
			coupledStruct(s)
		# Sinon on modifie les valeurs de ses positions : x et y, puis ses dimensions.
		elif not bool:
			pass
		# On réinitialise le tout.
		bool = False
'''
def posDimDefine(lenComp,dim_m_width):
	if (lenComp <= 9):
		tmp = 0
	elif (lenComp > 9 and lenComp < 15):
		dim_m_width = dim_m_width + 30
		tmp = 30
	elif (lenComp >= 15 and lenComp < 22):
		dim_m_width = dim_m_width + 70
		tmp = 70
	else:
		dim_m_width = dim_m_width + 110
		tmp = 110
	return [tmp, dim_m_width]

def typeDefine(comp):
	if isinstance(comp, Container.ContainerBlock):
		type = "atom"
	elif isinstance(comp, Container.CodeBlock):
		type = "coupled"
	elif isinstance(comp, Container.iPort):
		type = "iport"
	elif isinstance(comp, Container.oPort):
		type = "oport"
	else:
		type = "undefined"
	return type

def exist(dico,label):
	if label in list(dico.keys()):
		return True
	else:
		return False

def constructModel(type, name, x, y, dim_width, dim_height, iPorts, oPorts):
	if (type == "atom"):
		color = "orange"
	elif (type == "coupled"):
		color = "blue"
	elif (type == "oport"):
		color = "#DD6868"
	elif (type == "iport"):
		color = "#CCDD68"
	elif (type =="undefined"):
		color = "gray"

	if iPorts:
		str_iPorts = "\n\tiPorts: ["
		for i in iPorts:
			if i == iPorts[0]:
				str_iPorts = str_iPorts +  '"'+i+'"'
			else:
				str_iPorts = str_iPorts +  ',"'+i+'"'
	else:
		str_iPorts = ""

	if oPorts == []:
		if str_iPorts != "":
			str_iPorts = str_iPorts + ']'
	else:
		if str_iPorts != "":
			str_iPorts = str_iPorts + '],'

	if oPorts:
		str_oPorts = "\n\toPorts: ["
		for o in oPorts:
			if o == oPorts[0]:
				str_oPorts = str_oPorts +  '"'+o+'"'
			else:
				str_oPorts = str_oPorts +  ',"'+o+'"'
		str_oPorts = str_oPorts + ']\n'
	else:
		str_oPorts = "\n"

	if isinstance(x, int):
		tmp_x = x
		tmp_y = y
	elif isinstance(x, list):
		lenX = len(x) -1
		tmp_x = x[lenX]

		lenY = len(y) -1
		tmp_y = y[lenY]

	if len(name) > 22:
		label = name[:22] + "..."
	else:
		label = name

	var = 'var '+name+' = devs.Model.create({\n\trect: {x: '+str(tmp_x)+', y: '+str(tmp_y)+', width: '+str(dim_width)+', height: '+str(dim_height)+'},\n\tlabel: "'+label+'",\n\tlabelAttrs: { \'font-weight\': \'bold\', fill: \'white\', \'font-size\': \'12px\' },\n\tattrs: { fill: "'+color+'" },\n\tshadow: true,'+str_iPorts+str_oPorts+'});\n'

	return var

def addModel(model, component, label, x, y, dim_m_width, dim_m_height):
	if label is not None:
		label1 = label.replace(' ', '_')
	else:
		label1 = component.label.replace(' ', '_')
	lenComp = len(label1)
	tmp , dim_m_width = posDimDefine(lenComp, dim_m_width)
	if not exist(model, label1):
		iPorts = []
		oPorts = []
		if isinstance(component, Container.Block):
			for i in range(component.input):
				iPorts.append("in"+str(i))
			for i in range(component.output):
				oPorts.append("out"+str(i))
		type = typeDefine(component)
		cm = constructModel(type, label1, x, y, dim_m_width, dim_m_height, iPorts, oPorts)

		if isinstance(x, int):
			tmp_x = x
			tmp_y = y
		elif isinstance(x, list):
			lenX = len(x) -1
			tmp_x = x[lenX]

			lenY = len(y) -1
			tmp_y = y[lenY]

		model.update({label1: [cm, tmp_x, tmp_y, iPorts, oPorts, dim_m_width, dim_m_height]})
		x, y = xyPositionDefine(x, y, tmp, dim_m_height)

	return [model, x, y]

def makeDEVSConf(model, liaison, addInner, filename):
	""" Make conf file from D graph of the diagram for visualization on web site
	"""

	sys.stdout.write("Setting file...\n")
	text = ""

	forme_model = {"var":0,"x":1,"y":2,"in":3,"out":4,"dim_width":5,"dim_height":6}

	# Calcul de la hauteur du plus grand diagramme
	# Recuperation du plus grand diagramme, pour modifier sa hauteur
	m_x = 0
	m_y = 0
	labelDiagramme = ""
	for m in model:
		if model[m][forme_model["x"]] > m_x:
			m_x = model[m][forme_model["x"]]
		if model[m][forme_model["y"]] > m_y:
			m_y = model[m][forme_model["y"]]
		if model[m][forme_model["y"]] == 20 and model[m][forme_model["x"]] == 20:
			labelDiagramme = m
			var = model[m][forme_model["var"]]
	m_y = m_y + 120
	m_x = m_x + 150
	lenComp = len(labelDiagramme)
	tmp = posDimDefine(lenComp, 0)[:1][0]
	model[labelDiagramme][forme_model["dim_height"]] = m_y
	model[labelDiagramme][forme_model["dim_width"]] = m_x
	oldWidth = 1300 + tmp
	newWidth = m_x + tmp
	# oldHeight = 300
	# newHeight =
	# print "newWidth : ", newWidth , " - m_x : " , m_x , " - tmp : " , tmp
	var = var.replace(", width: " + str(oldWidth) + ", ", ", width: " + str(newWidth) + ", ")
	var = var.replace(", height: 300},", ", height: " + str(m_y) + "},")
	model[labelDiagramme][forme_model["var"]] = var

	# Config du diagramme
	title = "Discrete Event System Specification"
	description = 'Description du diagramme.'
	dimension = 'dimension(1200,560)'
	#Total des largeurs et hauteurs du "canvas"
	if newWidth < 1200:
		dim_width = 1200
	elif newWidth >= 1200:
		dim_width = newWidth + 40

	if newWidth < 1200:
		dim_height = 1200
	elif newWidth >= 1200:
		dim_height = m_y + 40


	devs = '\nvar devs = Joint.dia.devs;\nJoint.paper("world", ' + str(dim_width) + ', ' + str(dim_height) + ');'
	arrow = '\nvar arrow = devs.arrow;'
	text = text + 'title(\''+title+'\');' + '\n' +'description(\''+ description+'\');' + '\n' +dimension+ ';\n' + devs

	str_model = "\n\n"
	for m in model:
		str_model = str_model + model[m][forme_model["var"]]
		# print model[m]
		# print "Next :"
	text = text + str_model

	str_addInner = "\n\n"
	for i in addInner:
		str_addInner = str_addInner + i + "\n"
	text = text + str_addInner

	text = text + arrow

	str_liaison = "\n\n"
	for l in liaison:
		str_liaison = str_liaison + l
	text = text + str_liaison

	### js file is stored in out directory
	fn = os.path.join(getOutDir(), filename)

	### file exist ?
	update = os.path.exists(fn)

	try:
		with open(fn, "wb") as f:
			f.write(text)
	except:
		sys.stdout.write("%s file not %s.\n"%(fn, 'updated' if update else 'completed'))
	else:
		sys.stdout.write("%s file %s.\n"%(fn, 'updated' if update else 'completed'))
