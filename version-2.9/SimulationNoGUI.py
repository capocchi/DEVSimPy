# -*- coding: utf-8 -*-

"""
Name: SimulationNoGUI.py
Brief description: Overwrite some methods to implement the no gui version of DEVSimPy and make simulation from dsp file
in batch mode
Author(s): A-T. Luciani <atluciani@univ-corse.fr>, capocchi <capocchi@univ-corse.fr>
Version:  1.0
Last modified: 2015.01.11 by L. Capocchi
GENERAL NOTES AND REMARKS:

GLOBAL VARIABLES AND FUNCTIONS:
"""

import os
import sys
import time

import __builtin__
from cStringIO import StringIO
from io import TextIOWrapper, BytesIO
import traceback

import gettext
_ = gettext.gettext

sys.path.append(os.path.join('Domain', 'Phidgets'))

def makeYAMLUpdate(filename, label, json_str):
	import json
	from Container import Diagram

	### data = "{ 'a':'A', 'b':(2, 4), 'c':3.0 }"
	### data_string = json.dumps(json_str)

	### new args (dict object)
	new_args = eval(json.loads(repr(json_str)))

	### load diagram from yaml and update args
	a = Diagram()

	if a.LoadFile(filename):
		model=a.GetShapeByLabel(label)
		print "avant", model.args
		for arg in model.args:
			new_val =  new_args[arg]
			old_val = model.args[arg]
			if old_val != new_val:
				model.args[arg] = new_val
		print "apres", model.args

		### write new yaml file
		if a.SaveFile(a.last_name_saved):
			return True
		else:
			return False

		return True
	else:
		return False

	### print eval(new_info['a'])

def makeJSON(filename, json=None, diagram=None):
	""" Make JSON file from D graph of the diagram
	"""
	from Container import Diagram, ConnectionShape, CodeBlock, ContainerBlock, iPort, oPort

	if not json:
		### add filename in json
		json = {os.path.basename(filename):[{"cells":[]},{"description": ""}]}
	else:
		json = json

	if not diagram:
		dia = Diagram()

		if not dia.LoadFile(filename):
			json['success'] = False
			return json
	else:
		dia = diagram

	for c in dia.GetShapeList():

		### if c is coupled model
		if isinstance(c, ContainerBlock):
			D = {"type":"devs.Coupled",
					"angle":0,
	                "id":c.label,
	                "z":1,
	                "size":{"width":c.w,"height":c.h},
					"position":{"x":c.x[0],"y":c.y[0]},
					"inPorts":map(lambda i: "in%d"%i, range(c.input)),
					"outPorts":map(lambda i: "out%d"%i, range(c.output)),
					"attrs":{"text": {"text":c.label}}
					}

			### embeds key
			shapes = c.GetFlatBlockShapeList()
			D["embeds"] = [s.label for s in shapes]

			json[os.path.basename(filename)][0]['cells'].append(D)

			return makeJSON(filename, json, c)

		### if c is connexion
		else:
			if isinstance(c, ConnectionShape):
				D = {	"type":"devs.Link",
						"id":str(id(c)),
						"z":0,"attrs":{},
						'source':{"selector":".outPorts>g:nth-child(1)>circle"},
						'target':{"selector":".inPorts>g:nth-child(1)>circle"}}
				model1, portNumber1 = c.input
				model2, portNumber2 = c.output

				D['source']['id'] = model1.label.encode("utf-8")
				D['target']['id'] = model2.label.encode("utf-8")

			### if c is atomic model
			elif isinstance(c, CodeBlock):

				D = {"type":"devs.Atomic",
					"angle":0,
	                "id":c.label,
	                "z":1,
	                "size":{"width":c.w,"height":c.h},
					"position":{"x":c.x[0],"y":c.y[0]},
					"inPorts":map(lambda i: "in%d"%i, range(c.input)),
					"outPorts":map(lambda i: "out%d"%i, range(c.output)),
					"attrs":{"text": {"text":c.label}},
					"prop" :{"data" : c.args}
					}

				for i in xrange(c.input):
					D["attrs"].update( {".inPorts>.port%d>.port-label"%i:{"text":"in%d"%i},
										".inPorts>.port%d>.port-body"%i:{ "port":{ "id":"in%d"%i,
	                        			 		 	     							"type":"in"}},
										".inPorts>.port%d"%i:{ "ref":".body",
	                    		  	     						"ref-y":float(i+1)/(c.input+1)}
											})
				for j in xrange(c.output):
					D["attrs"].update( {".outPorts>.port%d>.port-label"%j:{"text":"out%d"%j},
										".outPorts>.port%d>.port-body"%j:{ "port":{ "id":"out%d"%j,
	                        			 		 	     							"type":"out"}},
										".outPorts>.port%d"%j:{ "ref":".body",
	                    		  	     						"ref-y":float(j+1)/(c.output+1)}
											})


			json[os.path.basename(filename)][0]['cells'].append(D)

	return json

def makeJS(filename):
	"""
	"""

	from Container import Diagram
	from Join import makeDEVSConf, makeJoin

	a = Diagram()
	if a.LoadFile(filename):
		sys.stdout.write(_("\nFile loaded\n"))

		addInner = []
		liaison = []
		model = {}
		labelEnCours = str(os.path.basename(a.last_name_saved).split('.')[0])

		# path = os.path.join(os.getcwd(),os.path.basename(a.last_name_saved).split('.')[0] + ".js") # genere le fichier js dans le dossier de devsimpy
		# path = filename.split('.')[0] + ".js" # genere le fichier js dans le dossier du dsp charg�.

		#Position initial du 1er modele
		x = [40]
		y = [40]
		bool = True

		model, liaison, addInner = makeJoin(a, addInner, liaison, model, bool, x, y, labelEnCours)
		makeDEVSConf(model, liaison, addInner, "%s.js"%labelEnCours)
	else:
		return False

class Printer:
	"""
	Print things to stdout on one line dynamically
	"""

	def __init__(self,data):

		sys.stdout.write("\r\x1b[K"+data.__str__())
		sys.stdout.flush()

def yes(prompt = 'Please enter Yes/No: '):
	while True:
	    try:
	        i = raw_input(prompt)
	    except KeyboardInterrupt:
	        return False
	    if i.lower() in ('yes','y'): return True
	    elif i.lower() in ('no','n'): return False

def makeSimulation(filename, T, json_trace=True):
	"""
	"""

	from Container import Diagram

	if not json_trace:
		sys.stdout.write(_("\nSimulation in batch mode with %s\n")%__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'])

	a = Diagram()

	if json_trace:
		json = {'date':time.strftime("%c")}
		json['mode']='no-gui'
	else:
		sys.stdout.write(_("\nLoading %s file...\n")%(os.path.basename(filename)))

	if a.LoadFile(filename):

		if json_trace:
			json['file'] = filename
		else:
			sys.stdout.write(_("%s loaded!\n")%(os.path.basename(filename)))

		try:
			if not json_trace:
				sys.stdout.write(_("\nMaking DEVS instance...\n"))

			master = Diagram.makeDEVSInstance(a)

		except Exception, info:
			### get exception info
			exc_info = traceback.format_exc()
			if json_trace:
				json['devs_instance'] = None
				json['success'] = False
				json['info'] = exc_info
				sys.stdout.write(str(json))
			else:
				sys.stdout.write("\n%s"%exc_info)

			return False

		else:
			if master:

				if json_trace:
					json['devs_instance'] = str(master)
					if isinstance(master, tuple):
						sys.stdout.write(str(json))
						return False
				else:
					if isinstance(master, tuple):
						sys.stdout.write(_("DEVS instance not created: %s\n")%str(master))
						return False
					else:
						sys.stdout.write(_("DEVS instance created!\n"))

				if not json_trace:
					sys.stdout.write(_("\nPerforming DEVS simulation...\n"))

				sim = runSimulation(master, T)
				thread = sim.Run()

				first_time = time.time()
				while(thread.isAlive()):
					new_time = time.time()
					output = new_time - first_time
					if not json_trace: Printer(output)

				if not json_trace:
					sys.stdout.write(_("\nDEVS simulation completed!\n"))

				if json_trace:
					json['time'] = output
					json['output'] = []

				### inform that data file has been generated
				for m in filter(lambda a: hasattr(a, 'fileName'), master.componentSet):
					for i in range(len(m.IPorts)):
						fn ='%s%s.dat'%(m.fileName,str(i))
						if os.path.exists(fn):
							if json_trace:
								json['output'].append({'name':os.path.basename(fn), 'path':fn})
							else:
								sys.stdout.write(_("\nData file %s has been generated!\n")%(fn))
				if json_trace:
					sys.stdout.write(str(json))

				return True

			else:
				return False

	else:
		if json_trace:
			json['file'] = None
        	json['success'] = True
         	sys.stdout.write(str(json))

        return False

class runSimulation:
	"""
	"""

	def __init__(self, master, time):
		""" Constructor.
		"""

		# local copy
		self.master = master
		self.time = time

		### No time limit simulation (defined in the builtin dico from .devsimpy file)
		self.ntl = __builtin__.__dict__['NTL']

		# simulator strategy
		self.selected_strategy = DEFAULT_SIM_STRATEGY

		### profiling simulation with hotshot
		self.prof = False

		self.verbose = False

		# definition du thread, du timer et du compteur pour les % de simulation
		self.thread = None
		self.count = 10.0
		self.stdioWin = None

	###
	def Run(self):
		""" run simulation
		"""

		assert(self.master is not None)
		### pour prendre en compte les simulations multiples sans relancer un SimulationDialog
		### si le thread n'est pas lanc� (pas pendant un suspend)
		# if self.thread is not None and not self.thread.thread_suspend:
		diagram = self.master.getBlockModel()
		# diagram.Clean()
		# print self.master
		################################################################################################################
		######### To Do : refaire l'enregistrement du chemin d'enregistrements des resuts du to_disk ###################
		for m in self.master.componentSet:
			if str(m)=='To_Disk':
				dir_fn = os.path.dirname(diagram.last_name_saved).replace('\t','').replace(' ','')
				label = m.getBlockModel()
				m.fileName = os.path.join(dir_fn,"%s_%s"%(os.path.basename(diagram.last_name_saved).split('.')[0],os.path.basename(m.fileName)))
		################################################################################################################
		################################################################################################################

		if self.master:
			from SimulationGUI import simulator_factory
			if not self.ntl:
				self.master.FINAL_TIME = float(self.time)

			self.thread = simulator_factory(self.master, self.selected_strategy, self.prof, self.ntl, self.verbose)

			return self.thread

