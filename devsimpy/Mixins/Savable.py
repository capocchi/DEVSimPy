# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Savable.py --- Class based on pickle module and dedicated to save and load components.
#                     --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  08/11/20
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import os
import sys
import pickle
import zipfile
import zipimport
import gzip
import builtins
import gettext
import importlib
import subprocess
import traceback
import types
import inspect
import json
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
_ = gettext.gettext

required_libs = ['yaml','ruamel']

for lib_name in required_libs:
    try:
        importlib.import_module(lib_name)
    except:
        subprocess.run(f'pip install {lib_name}'.split())

try:
	import yaml
	setattr(builtins,'YAML_IMPORT', True)
except ImportError as info:
	setattr(builtins,'YAML_IMPORT', False)
	sys.stdout.write("yaml module was not found! Install it if you want to save model in yaml format.\n")

try:
	from ruamel.yaml import YAML
	import ruamel.yaml as ruamel
	setattr(builtins,'YAML_IMPORT', True)
except ImportError as info:
	try:
		import ruamel_yaml as ruamel
	except ImportError as info:
		setattr(builtins,'YAML_IMPORT', False)
		sys.stdout.write("ruamel.yaml module was not found! Install it if you want to save model in yaml format.\n")

from tempfile import gettempdir

from Decorators import BuzyCursorNotification, StatusBarNotification, cond_decorator
from Utilities import itersubclasses, getTopLevelWindow, NotificationMessage

from XMLModule import makeDEVSXML
from Join import makeJoin, makeDEVSConf
from .Abstractable import Abstractable

import Components
import ZipManager

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASS DEFIINTION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class PickledCollection(list):
	""" Custom list class for dsp attributes dumping.
	"""

	def __init__(self, obj):
		""" Constructor.
		"""
		self.pickled_obj = [getattr(obj, attr) for attr in obj.dump_attributes]

		#=======================================================================
		### addition of abstraction attributes only if there is not in dump_attributes (after having saved a model, dump_attributes contains abstraction attributes !)
		self.pickled_obj += [getattr(obj, attr) for attr in obj.dump_abstr_attributes if attr not in obj.dump_attributes]
		#=======================================================================

	def __setstate__(self, state):
		""" Restore state from the unpickled state values.
		"""
		self.__dict__.update(state)

	def __iter__(self):
		""" Overwrite iterator protocol.
		"""
		yield from self.pickled_obj

class DumpBase(object):
	""" DumpBase class.
	"""

	### list of available extension
	WhiteList = ('.cmd','.amd', '.dsp', '.js', '.json', '.xml', '.yaml', '.yml', '.tar','.zip','.rar','.7zip','.tar','.gz','.7z','.s7z','.ace','.afa','.alz','.apk','.arc','.arj','.ba','.bh','.cab','.cfs','.cpt','.dra','.dd','.dgc','.dmg','.gca','.ha','hki.','.ice','.j','.kgb','.lzh','.lha','.lzx','.pak','.partimg','.paq6','.paq7','.paq8','.pea','.pim','.pit','.qda','.rk','.sda','.sea','.sen','.sfx','.sit','.sitx','.sqx','.tgz','.Z','.bz2','.tbz2','.lzma','.tlz','.uc','.uc0','.uc2','.ucn','.ur2','.ue2','.uca','.uha','.wim','.xar','.xp3','.yz1','.zipx','.zoo','.zz','.rz','.sfark')

	### Dict of tuples extension/class
	DB = {}

	### extension is in whiteList
	@staticmethod
	def GetExt(fileName:str=""):
		ext = os.path.splitext(fileName)[-1]

		if ext == "":
			return sys.stdout.write(_("\nPlease save the project."))

		if ext in DumpBase.WhiteList:
			return ext
     
		sys.stdout.write(_("\nThis extension is unknown: %s.")%ext)
		return False

	### Return the class in charge of saving or loading from ext of object.
	@staticmethod
	def GetAssociateCls(ext:str=""):
		try:
			return DumpBase.DB[ext]
		except KeyError:
			return False

	### R�cup�re les fils de la classe pass� en param�tre, ici on veut que ce soit DumpBase, on les ajoute a une liste (subclasses),
	### ensuite pour chaque element de la liste on recupere la variable static ext (list),
	### et on ajoute au dictionnaire DumpBase.vars en cl� l'extension ext et en valeur le nom de la classe correspondante
	@staticmethod
	def PopulateDB():
		""" Polpulate.
		"""

		subclasses = itersubclasses(DumpBase)

		for cls in subclasses:
			for elem in cls.ext:
				# Impose un type de fichier par classe et non pas une classe par type de fichier.
				assert(elem not in list(DumpBase.DB.keys()))
				DumpBase.DB[elem] = cls

	def Load(self, filename):
		"""Retrieve data from the file source.
		"""
		pass

	def Save(self, filename):
		"""Save the data object to the file.
		"""
		pass

###-----------------------------------------------------------
class DumpZipFile(DumpBase):
	""" For save .amd or cmd file
	"""

	ext = [".amd", ".cmd"]

	def Save(self, obj_dumped, fileName=None) -> bool:
		""" 
		Function that saves the codeblock on the disk.
		"""
		if not fileName or not fileName.endswith(tuple(DumpZipFile.ext)):
			raise ValueError(f"Invalid filename '{fileName}'. It must end with one of {DumpZipFile.ext}.")
		
		# # Convert absolute paths to relative paths if necessary
		# if hasattr(obj_dumped, 'python_path') and os.path.isabs(obj_dumped.python_path):
		# 	obj_dumped.python_path = os.path.join(fileName, os.path.basename(obj_dumped.python_path))
		
		# if hasattr(obj_dumped, 'image_path') and os.path.isabs(obj_dumped.image_path):
		# 	obj_dumped.image_path = os.path.join(fileName, os.path.basename(obj_dumped.image_path))
		
		# Update obj_dumped args if applicable
		if hasattr(obj_dumped, 'args'):
			try:
				obj_dumped.args = Components.GetArgs(Components.GetClass(obj_dumped.python_path))
			except Exception as error:
				sys.stderr.write(f"Problem updating args for '{fileName}': {error}\n")
				return False

		try:
			dump_filename = 'DEVSimPyModel.dat'
			
			with open(dump_filename, 'wb') as file:
				pickle.dump(obj=PickledCollection(obj_dumped), file=file, protocol=pickle.HIGHEST_PROTOCOL)
		
		except (OSError, pickle.PickleError) as error:
			tb = traceback.format_exc()
			sys.stderr.write(f"Problem saving '{fileName}': {error}\n{tb}")
			return False
		
		except Exception as error:
			tb = traceback.format_exc()
			sys.stderr.write(f"Unexpected error while saving '{fileName}': {error}\n{tb}")
			return False
		
		else:

			try:
				 
				zf = ZipManager.Zip(fileName)

				# Local copy of paths
				python_path = getattr(obj_dumped, 'python_path', None)
				image_path = getattr(obj_dumped, 'image_path', None)
				
				# Vérifie si les chemins sont valides avant de les utiliser
				files_to_add = [path for path in [python_path, image_path] if path]

				# Create or update the zip file
				if os.path.exists(fileName):
					zf.Update(replace_files=[*files_to_add, dump_filename])
				else:
					zf.Create(add_files=[*files_to_add, dump_filename])
				
				# Supprimer le fichier temporaire de dump
				if os.path.exists(dump_filename):
					os.remove(dump_filename)
				
				# Chemin absolu du répertoire parent
				newExportPath = os.path.abspath(os.path.dirname(fileName))
				
				mainW = getTopLevelWindow()
				
				# Si le chemin d'exportation n'est pas un sous-dossier de DOMAIN_PATH
				if not os.path.commonpath([newExportPath, DOMAIN_PATH]).startswith(DOMAIN_PATH):
					
					# Charger et mettre à jour la liste des chemins d'export
					try:
						mainW.exportPathsList = json.loads(mainW.cfg.Read("exportPathsList"))
					except json.JSONDecodeError:
						mainW.exportPathsList = []
					
					if newExportPath not in mainW.exportPathsList:
						mainW.exportPathsList.append(newExportPath)
					
					mainW.cfg.Write("exportPathsList", json.dumps(mainW.exportPathsList))

				# Mise à jour de l'arbre de la bibliothèque
				mainW.tree.UpdateDomain(newExportPath)
				mainW.tree.SortChildren(mainW.tree.root)

			except (OSError, FileNotFoundError, json.JSONDecodeError) as error:
				tb = traceback.format_exc()
				NotificationMessage(_('Error'), 
									_("Problem saving (during the zip handling): %s -- %s\n") % (fileName, error), 
									parent=getTopLevelWindow(), timeout=5)
				sys.stderr.write(_("Problem saving (during the zip handling): %s -- %s\n") % (fileName, tb))
				return False
			
			except Exception as error:
				tb = traceback.format_exc()
				NotificationMessage(_('Unexpected Error'), 
									_("Unexpected problem saving (during the zip handling): %s -- %s\n") % (fileName, error), 
									parent=getTopLevelWindow(), timeout=5)
				sys.stderr.write(_("Unexpected problem saving (during the zip handling): %s -- %s\n") % (fileName, tb))
				return False

			else:
				return True

	def Load(self, obj_loaded, fileName = None):
		""" Load codeblock (obj_loaded) from fileName.
		"""

		# get zip file object
		zf = zipfile.ZipFile(fileName, 'r')

		try:
			data_file = 'DEVSimPyModel.dat'
			path = zf.extract(data_file, os.path.realpath(gettempdir()))
		except KeyError as info:
			tb = traceback.format_exc()
			sys.stderr.write(_("ERROR: Did not %s find in zip file %s --\n%s \n")%(data_file, str(fileName), str(tb)))
			return info
		except Exception as info:
			tb = traceback.format_exc()
			sys.stderr.write(_("Problem extracting: %s -- %s \n")%(str(fileName),str(tb)))
			return info
		finally:
			zf.close()

		### cPickle need importation (mostly when the instanciation is extrernal of DEVSimPy library)
		#module = BlockFactory.GetModule(fileName)

		#if isinstance(module, Exception):
			#return module

		# try to load file
		try:
			with open(path,'rb') as f:
				L = pickle.load(f)
		except Exception as info:
			tb = traceback.format_exc()
			sys.stderr.write(_("Problem loading: %s -- %s \n")%(str(fileName), str(tb)))
			return info
	
		### Check comparison between serialized attribut (L) and normal attribut (dump_attributes)

		### old model that contains path of model and python files - we remove this
		if not isinstance(L[0],dict) and isinstance(L[0],str) and isinstance(L[1],str):
			L = L[2:]

		if len(obj_loaded.dump_attributes) != len(L):
			L = [{},{}]+L
		#=======================================================================

		### abstraction hierarchy checking
		if abs(len(obj_loaded.dump_attributes)-len(L)) == len(Abstractable.DUMP_ATTR):
			obj_loaded.dump_attributes += Abstractable.DUMP_ATTR

		#=======================================================================

		### for amd and cmd build after the implementation of the rename method of model in librarie
		### This may present an opportunity for the delete of the model_path and python_path of the .amd or .cmd compressed file.
		if abs(len(L)-len(obj_loaded.dump_attributes))==2:
			L=L[2:]
			assert(len(L)==len(obj_loaded.dump_attributes))
		
		### for position_label checking (for very old version of .amd or .cmd model)
		elif abs(len(obj_loaded.dump_attributes)-len(L)) == 1:

			### 'label_pos' attribut is on rank 6 and its defautl value is "middle"
			j = 6 if fileName.endswith(DumpZipFile.ext[-1]) else 4
			L.insert(j, 'middle')

		try:
			### assign dumped attributs
			for i, attr in enumerate(obj_loaded.dump_attributes):
				### update behavioral attribute for model saved with bad args (amd or cmd have been changed in librairie but not in dsp)
				if attr == 'args':
					if obj_loaded.args != {}:
						for key in [a for a in list(obj_loaded.args.keys()) if a in list(L[i].keys())]:
							obj_loaded.args[key] = L[i][key]
					else:
						setattr(obj_loaded, attr, L[i])
				else:
					setattr(obj_loaded, attr, L[i])
				
		except (IndexError,AttributeError) as info:
			tb = traceback.format_exc()
			sys.stderr.write(_("Problem loading (old model): %s -- %s \n")%(str(fileName), str(tb)))
			return info
		
		obj_loaded.model_path = fileName
		obj_loaded.python_path = os.path.join(fileName, os.path.basename(fileName).replace('.cmd','.py').replace('.amd','.py'))

		### if the model was made from another pc
		#if not os.path.exists(obj_loaded.model_path):
		#	obj_loaded.model_path = fileName
	
		#with zipfile.ZipFile(fileName) as zf:
		#	### find all python files
		#	for file in zf.namelist():
		#		r = repr(zf.read(file))
		#		if file.endswith(".py") and ('DomainBehavior' in r or 'DomainStructure' in r):
		#			obj_loaded.python_path = os.path.join(obj_loaded.model_path, re.findall(".*(?:.[a|c]md)+[/|\\\](.*.py)*", obj_loaded.python_path)[-1])

		### if python file is wrong
		#if not os.path.exists(os.path.dirname(obj_loaded.python_path)):
			### ?: for exclude or non-capturing rule
			#obj_loaded.python_path = os.path.join(obj_loaded.model_path, re.findall(".*(?:.[a|c]md)+[/|\\\](.*.py)*", obj_loaded.python_path)[-1])

		#obj_loaded.python_path = os.path.join(fileName,os.path.basename(fileName).replace('.cmd','.py').replace('.amd','.py'))

		return True

	@BuzyCursorNotification
	def LoadPlugins(self, obj, fileName):
		""" Method which load plugins from zip.
			Used for define or redefine method of amd. and .cmd model.
			The name of plugin file must be "plugins.py".
		"""
		### if list of activated plugins is not empty
		if obj.plugins:
			### import zipfile model
			if zipfile.is_zipfile(fileName):
				importer = zipimport.zipimporter(fileName)
				if importer.find_module('plugins'):

					try:
						module = importer.load_module('plugins')
					except ImportError as info:
						tb = traceback.format_exc()
						sys.stdout.write("%s\n"%str(tb))
						return info

					for m in [e for e in [module.__dict__.get(a) for a in dir(module)] if not inspect.ismodule(e) and inspect.getmodule(e) is module]:
						name = m.__name__
						### import only plugins in plugins list (dynamic attribute)
						if name in obj.plugins:
							try:
								### new object to assaign
								new = eval("module.%s"%name)
								if inspect.isfunction(new):
									setattr(obj, name, types.MethodType(new, obj))
								elif inspect.isclass(new):
									### TODO: monkey patchin !!! (most simple is to change python file for override class)
									pass

							except Exception as info:
								tb = traceback.format_exc()
								sys.stdout.write(_('plugins %s not loaded : %s\n'%(name,str(tb))))
								return info

		### restor method which was assigned to None before being pickled
		else:
			### for all method in the class of model
			for method in [value for value in list(obj.__class__.__dict__.values()) if isinstance(value, types.FunctionType)]:
				name = method.__name__
				### if method was assigned to None by getstate berfore being pickled
				if getattr(obj, name) is None:
					### assign to default class method
					setattr(obj, name, types.MethodType(method, obj))

		return True

###-----------------------------------------------------------
class DumpGZipFile(DumpBase):
	""" For save .dsp file.
	"""
	ext = [".dsp"]

	def Save(self, obj_dumped, fileName=None):
		""" 
    	Function that saves the dump on the disk under the given filename.
    	"""
		if not fileName or not fileName.endswith(tuple(DumpGZipFile.ext)):
			raise ValueError(f"Invalid filename '{fileName}'. It must end with one of {DumpGZipFile.ext}.")
		
		try:
			# Utilisation d'un gestionnaire de contexte pour garantir la fermeture du fichier
			with gzip.GzipFile(filename=fileName, mode='wb', compresslevel=9) as file:
				pickle.dump(obj=PickledCollection(obj_dumped), file=file, protocol=pickle.HIGHEST_PROTOCOL)
		
		except (OSError, pickle.PickleError) as error:
			tb = traceback.format_exc()
			sys.stderr.write(f"\nProblem saving '{fileName}': {error}\n{tb}")
			return False
		
		except Exception as error:
			tb = traceback.format_exc()
			sys.stderr.write(f"\nUnexpected error while saving '{fileName}': {error}\n{tb}")
			return False
		
		else:
			return True

	def Load(self, obj_loaded, fileName=None) -> bool:
		""" 
		Function that loads a diagram from its filename.
		"""
		if not fileName:
			raise ValueError("Filename must be provided to load the diagram.")
		
		try:
			# Ouvre le fichier GZIP (gestion de contexte) et vérifie s'il est bien compressé
			with gzip.GzipFile(filename=fileName, mode='rb') as f:
				try:
					f.read(1)  # Teste si le fichier est compressé
					f.seek(0)  # Remet le curseur au début
					dsp = pickle.load(f)  # Charge l'objet sérialisé
				except Exception as error:
					tb = traceback.format_exc()
					sys.stderr.write(f"Problem loading: {fileName} -- {tb}\n")
					return error
		
		except (OSError, IOError, gzip.BadGzipFile) as error:
			tb = traceback.format_exc()
			sys.stderr.write(f"Problem opening file '{fileName}': {tb}\n")
			return error
		
		# Vérifie la correspondance entre les attributs de l'objet et les données chargées
		if abs(len(obj_loaded.dump_attributes) - len(dsp)) == len(Abstractable.DUMP_ATTR):
			obj_loaded.dump_attributes += Abstractable.DUMP_ATTR

		if len(obj_loaded.dump_attributes) != len(dsp):
			raise ValueError(f"Mismatch between attributes and dumped data: {len(obj_loaded.dump_attributes)} != {len(dsp)}")

		# Attribue les valeurs chargées aux attributs de l'objet
		for attr, value in zip(obj_loaded.dump_attributes, dsp):
			setattr(obj_loaded, attr, value)

		# Mémorise le nom du fichier chargé
		obj_loaded.last_name_saved = fileName

		return True

###-----------------------------------------------------------
class DumpYAMLFile(DumpBase):
	""" For save .yaml file.
	"""
	ext = [".yaml", '.yml']

	def Save(self, obj_dumped, fileName=None) -> bool:
		""" 
		Function that saves the dump to disk as a YAML file.
		"""
		# Vérification de la validité du nom de fichier
		if not fileName or not fileName.endswith(tuple(DumpYAMLFile.ext)):
			raise ValueError(f"Invalid filename '{fileName}'. It must end with one of {DumpYAMLFile.ext}.")
		
		try:
			# Première tentative avec le mode "sûr"
			yaml = YAML()
			yaml.register_class(PickledCollection)

			with open(fileName, 'w') as yf:
				yaml.dump(PickledCollection(obj_dumped), stream=yf, default_flow_style=False)
		
		except (AttributeError, Exception) as error:
			sys.stderr.write(f"Warning: First attempt to save YAML failed, retrying in 'unsafe' mode: {error}\n")
			
			try:
				# Deuxième tentative avec le mode "unsafe" (moins sécurisé, mais plus permissif)
				yaml = YAML(typ='unsafe', pure=True)

				with open(fileName, 'w') as yf:
					yaml.dump(PickledCollection(obj_dumped), stream=yf)
			
			except (OSError, Exception) as error:
				tb = traceback.format_exc()
				sys.stderr.write(f"Problem saving YAML file '{fileName}': {error}\n{tb}")
				return False

		except (OSError, Exception) as error:
			tb = traceback.format_exc()
			sys.stderr.write(f"Problem saving YAML file '{fileName}': {error}\n{tb}")
			return False

		return True

	@staticmethod
	def Open(fileName:str):
		""" Open the YAML filename and return the coresponding object.

		Args:
			fileName (str): YAML filename
		"""

		## try to open f with compressed mode
		try:
			yaml = YAML()
			yaml.register_class(PickledCollection)
			with open(fileName, 'r') as yf:
				return ruamel.load(yf, Loader=ruamel.Loader)
		except AttributeError as info:
			try:
				yaml = ruamel.YAML(typ='unsafe', pure=True)
				with open(fileName, 'r') as yf:
					return yaml.load(yf)
			except Exception as info:
				tb = traceback.format_exc()
				sys.stderr.write(_("\nProblem loading: %s -- %s\n")%(str(fileName),str(tb)))
				return False
		except Exception as info:
			exc_type, _, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			sys.stderr.write(_("Problem opening: %s -- description: %s / type: %s / name: %s / line: %s\n")%(str(fileName), info, exc_type, fname, exc_tb.tb_lineno))
			sys.stderr.write(traceback.format_exc())
			return info
		
	def Load(self, obj_loaded, fileName=None) -> bool:
		""" 
		Function that loads the dump from a filename and assigns it to obj_loaded.

		Args:
			obj_loaded: The object to which the attributes will be assigned.
			fileName (str): The path to the file to load.

		Returns:
			bool: True if the load was successful, False otherwise.
		"""
		# Vérification du nom de fichier
		if not fileName or not isinstance(fileName, str):
			raise ValueError("Filename must be a non-empty string.")

		try:
			# Ouvre et lit le fichier YAML
			dsp = DumpYAMLFile.Open(fileName)

		except Exception:
			tb = traceback.format_exc()
			sys.stderr.write(f"Problem loading file '{fileName}': {tb}\n")
			return False

		# Vérification de la correspondance des longueurs
		if len(dsp) != len(obj_loaded.dump_attributes):
			raise ValueError(f"Mismatch between attributes and dumped data: {len(obj_loaded.dump_attributes)} != {len(dsp)}")

		# Assignation des attributs en utilisant zip
		for attr, value in zip(obj_loaded.dump_attributes, dsp):
			setattr(obj_loaded, attr, value)

		# Enregistrement du dernier nom de fichier chargé
		obj_loaded.last_name_saved = fileName

		return True

###-----------------------------------------------------------
class DumpJSONFile(DumpBase):
	""" For save/load .json file.
	"""
	ext = [".json"]

	def Save(self, obj_dumped, fileName = None):
		""" Save method.
		"""
		assert(fileName.endswith(tuple(DumpJSONFile.ext)))

		j = obj_dumped.toJSON()
		with open(fileName, 'w') as outfile:
			outfile.write(json.dumps(j, indent=4))

		return True
	
	def Load(self, obj_loaded, fileName=None):
		""" Load method.
		"""

		assert(fileName.endswith(tuple(DumpJSONFile.ext)))

		with open(fileName, 'r') as f:
			json_data = json.load(f)

		DumpJSONFile.Open(json_data, obj_loaded)

		# Enregistrement du dernier nom de fichier chargé
		obj_loaded.last_name_saved = fileName

		return True

	@staticmethod 
	def Open(json_data, diagram=None, processed_blocks=None):
		"""Open the JSON data and convert it into a Diagram instance."""
		from Container import Diagram, ConnectionShape, CodeBlock, ContainerBlock, iPort, oPort

		# Initialize diagram and tracking sets
		if not diagram:
			diagram = Diagram()
		if processed_blocks is None:
			processed_blocks = set()
		
		blocks = {}  # Map block IDs/labels to instances
		connections = []  # Store connection data for second pass

		# First pass: Create all blocks
		for cell in json_data.get('cells', []):
			cell_type = cell.get('type')
			
			if cell_type in ('devs.Atomic', 'devs.Coupled'):
				label = cell.get('label')
				if label in processed_blocks:
					continue
				
				processed_blocks.add(label)
				
				# Create appropriate block type
				if cell_type == 'devs.Atomic':
					block = CodeBlock()
				else:  # devs.Coupled
					block = ContainerBlock()
					
					# Create input/output ports for coupled model
					in_ports = cell.get('inPorts', [])
					out_ports = cell.get('outPorts', [])
					
					# Add input ports
					for i, port_name in enumerate(in_ports):
						iport = iPort()
						iport.label = port_name
						iport.id = f"in{i}"
						block.AddShape(iport)
						blocks[f"{label}_{port_name}"] = iport
					
					# Add output ports  
					for i, port_name in enumerate(out_ports):
						oport = oPort()
						oport.label = port_name
						oport.id = f"out{i}"
						block.AddShape(oport)
						blocks[f"{label}_{port_name}"] = oport
				
				# Set basic properties
				block.id = cell.get('id')
				block.label = label
				block.input = len(cell.get('inPorts', []))
				block.output = len(cell.get('outPorts', []))
				
				# Handle behavior properties
				behavior = cell.get('behavior', {})
				block.python_path = behavior.get('python_path', '')
				block.model_path = behavior.get('model_path', '')
				block.args = behavior.get('prop', {}).get('data', {})
				
				# Handle nested models in coupled blocks
				if cell_type == 'devs.Coupled' and 'embeds' in cell:
					embedded_cells = [
						c for c in json_data['cells'] 
						if c.get('label') in cell['embeds'] and 
						c.get('label') not in processed_blocks
					]
					
					if embedded_cells:
						nested_data = {'cells': embedded_cells}
						nested_diagram = Diagram()
						block.diagram = nested_diagram
						nested_diagram.parent = block
						DumpJSONFile.Open(nested_data, nested_diagram, processed_blocks)
				
				# Store block references
				blocks[str(block.id)] = block
				blocks[block.label] = block
				diagram.shapes.append(block)
				
			elif cell_type == 'devs.Link':
				connections.append(cell)

		# Second pass: Create all connections
		for conn_data in connections:
			source = conn_data.get('source', {})
			target = conn_data.get('target', {})
			
			source_block = blocks.get(str(source.get('id'))) or blocks.get(source.get('id'))
			target_block = blocks.get(str(target.get('id'))) or blocks.get(target.get('id'))
			
			if source_block and target_block:
				conn = ConnectionShape()
				conn.setInput(source_block, source.get('port'))
				conn.setOutput(target_block, target.get('port'))
				diagram.shapes.append(conn)

		return diagram

###-----------------------------------------------------------
class DumpJSFile(DumpBase):
	""" For save .js file.
	"""
	ext = [".js"]

	def Save(self, obj_dumped, fileName = None):
		""" Save method.
		"""
		assert(fileName.endswith(tuple(DumpJSFile.ext)))

		diagram = obj_dumped

		addInner = []
		liaison = []
		model = {}
		labelEnCours = str(diagram.label)
		#Position initial du 1er modele
		x = [40]
		y = [40]
		bool = True
		model, liaison, addInner = makeJoin(diagram, addInner, liaison, model, bool, x, y, labelEnCours)
		makeDEVSConf(model, liaison, addInner, fileName)

###-----------------------------------------------------------
class DumpXMLFile(DumpBase):
	""" For save .xml file
	"""
	ext = [".xml"]

	def Save(self, obj_dumped, fileName = None):
		"""
		"""
		assert(fileName.endswith(tuple(DumpXMLFile.ext)))

		diagram = obj_dumped
		D = diagram.__class__.makeDEVSGraph(diagram, {})
		label = diagram.label if isinstance(diagram, Components.GenericComponent) else os.path.splitext(os.path.basename(fileName))[0]

		makeDEVSXML(label, D, fileName)

		return True

###-----------------------------------------------------------
class Savable(object):
	""" Savable class that allows methods to save and load diagram into file.

		cond_decorator is used to enable/diseable the cursor notification depending on the GUI/NO_GUI use of DEVsimPy.
	"""

	### static attribut to store le extention/class available
	DB  = DumpBase.PopulateDB()

	@cond_decorator(getattr(builtins, 'GUI_FLAG', True), BuzyCursorNotification)
	@cond_decorator(getattr(builtins, 'GUI_FLAG', True), StatusBarNotification('Sav'))
	def SaveFile(self, fileName = None):
		""" Save object in fileName.
		"""

		if not fileName:
			return False

		### test if ext is acceptable
		ext = DumpBase.GetExt(fileName)
		if ext:
			### get class managing object with this extension
			cls = DumpBase.GetAssociateCls(ext)
			if cls:
				### call Save method of self to save it in fileName file.
				return cls().Save(self, fileName)
			else:
				sys.stdout.write(_("\nError in Savable class using SaveFile: %s")%fileName)
				return False
		else:
			sys.stdout.write(_("\nUnknown extension: %s")%fileName)
			return False

	@cond_decorator(GUI_FLAG, StatusBarNotification('Load'))
	def LoadFile(self, fileName = None):
		""" Load object from fileName.
		"""

		if fileName is None:
			return False

		### test if ext is acceptable
		ext = DumpBase.GetExt(fileName)
		if ext:
			### get class managing object with this extension
			cls = DumpBase.GetAssociateCls(ext)
			if cls:
				### call Load method of self to load it from fileName file.
				return cls().Load(self, fileName)
			else:
				sys.stdout.write(_("Error in Savable class using LoadFile: %s")%fileName)
				return False
		else:
			sys.stdout.write(_("Unknown extension: %s")%fileName)
			return False