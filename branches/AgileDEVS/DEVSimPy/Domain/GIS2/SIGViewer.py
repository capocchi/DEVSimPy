# -*- coding: utf-8 -*-

"""
Name: SIGViewer.py
Brief description: SIG plugin viewer 
Author(s): L. Capocchi <capocchi@univ-corse.fr>, J.F. Santucci <santucci@univ-corse.fr>, B. Poggi <poggi@univ-corse.fr>
Version: 0.1
Last modified: 08/07/2012
GENERAL NOTES AND REMARKS: Use the simplekml module.
GLOBAL VARIABLES AND FUNCTIONS:
"""

### just for python 2.5
from __future__ import with_statement
from DomainInterface.DomainBehavior import DomainBehavior 

import os
import Domain.GIS2.simplekml as simplekml
from Domain.GIS2.Point import Point

# ===================================================================   #
class SIGViewer(DomainBehavior):
	"""
	"""

	###
	def __init__(self, fileName = "out"):
		""" Constructor.
		
			@param fileName : output file name
		"""

		DomainBehavior.__init__(self)

		### local copy
		self.fn = ''.join([fileName,'.kml'])

		self.folder_dico = {}
		
		### State variable
		self.state = {'status': 'INACTIF', 'sigma': INFINITY}
		
		self.kml = simplekml.Kml()
		self.kml.document.name = fileName[:-4]
		self.kml.document.open = 1

	###
	def extTransition(self):
		"""
		"""

		activePort = self.myInput.keys()[0]
		msg = self.peek(activePort)
		
		### new obj
		obj_list = msg.value

		### msg must contain list of geographical element to be transformed
		if isinstance(obj_list, list):
		
			### for each element
			for obj in obj_list:
				### if obj is Folder
				
				if obj.__class__.__name__ == 'Folder':
					
					if not obj.name in self.folder_dico.keys():	
						### create an instance of Folder KML object
						self.folder_dico.update({obj.name:self.kml.newfolder(name=obj.name)})

					kml_folder = self.folder_dico[obj.name]
					
					### add childs in folder
					for elem in obj.childs:
						self.AddKMLObj(kml_folder, elem)

				else:
					
					### if elem have 'folder' attribut and is not empty string
					if hasattr(obj, 'folder') and obj.folder != "":
						
						if not obj.folder in self.folder_dico.keys():
							### create an instance of Folder KML object
							self.folder_dico.update({obj.folder:self.kml.newfolder(name=obj.folder)})
						
						### create new layer
						kml_folder = self.folder_dico[obj.folder]
						kml_folder.open = 1
					else:
						kml_folder = self.kml

					self.AddKMLObj(kml_folder, obj)
				
		#### kml tree
		#kml_tree = KML.KML_Tree(self.fn)
		#doc = kml_tree.doc
		
		#### if there is no Folder, we create it with a placemark
		#if doc.findall("{%s}Folder" % (KML.KML_Tree.NS)) == []:
			#kml_tree.add_placemark(kml_tree.add_folder(doc, point), point)
		#### some Folder are present
		#else:
			
			#### if new folder exist
			#folder_list = filter(lambda f:point.folder == f.findtext("{%s}name" % (KML.KML_Tree.NS)) ,doc.findall("{%s}Folder" % (KML.KML_Tree.NS)))
			#if folder_list != []:
				#folder = folder_list[0]
				#place_list = filter(lambda p: point.name == p.findtext("{%s}name" % (KML.KML_Tree.NS)), folder.findall("{%s}Placemark" % (KML.KML_Tree.NS)))
				#### if the name of new placemark already exist, we replace it on the existing Folder
				#if place_list != []:
					#place = place_list[0]
					#kml_tree.add_placemark(folder, point, place)
				#### the new placemark is added on the existing Folder
				#else:
					#kml_tree.add_placemark(folder, point)
			#else:
				#kml_tree.add_placemark(kml_tree.add_folder(doc, point), point)
			
		##print self.kml_tree.tostring(kml)
		
		#### kml writing
		#kml_tree.write(self.fn)

		self.kml.save(self.fn)
		
		self.state['sigma'] = 0

	###
	def AddKMLObj(self, kml_folder, obj):
		""" Add KML obj in kml_folder
		"""
		
		### if Point element
		if obj.__class__.__name__ == 'Point':

			iconstyle = simplekml.IconStyle(icon=simplekml.Icon(href=obj.icon_fn))

			### add point
			point = kml_folder.newpoint()
			point.name = obj.name
			point.coords = [(obj.lon, obj.lat, obj.alt)]
			point.description = obj.desc
			point.iconstyle = iconstyle
			if hasattr(obj, 'extendeddata'):
				for k,v in obj.extendeddata.items():
					point.extendeddata.newdata(name=k, value=v, displayname=k)
					
		### if line element
		elif obj.__class__.__name__ == 'Line':
			linestring = kml_folder.newlinestring(name=obj.name)
			linestring.coords = map(eval, obj.coords)
			linestring.linestyle.color = getattr(simplekml.Color, obj.bgcolor)
			linestring.linestyle.width = obj.width
			if hasattr(obj, 'extendeddata'):
				for k,v in obj.extendeddata.items():
					linestring.extendeddata.newdata(name=k, value=v, displayname=k)

		### if Polygon element
		elif obj.__class__.__name__ == 'Polygon':
			multipolodd = kml_folder.newmultigeometry(name=obj.name)
			multipolodd.newpolygon(outerboundaryis=map(eval,obj.coords))
			multipolodd.style.polystyle.color = simplekml.Color.changealpha(str(obj.alpha), getattr(simplekml.Color,obj.bgcolor))
			if hasattr(obj, 'extendeddata'):
				for k,v in obj.extendeddata.items():
					multipolodd.extendeddata.newdata(name=k, value=v, displayname=k)
			
		else:
			sys.stdout.write('Type unknown in SIGViewer')
			
	###
	def intTransition(self):
		self.state["status"] = 'IDLE'
		self.state["sigma"] = INFINITY
					
	###
	def timeAdvance(self):return self.state['sigma']

	###
	def __str__(self):return "SIGViewer"