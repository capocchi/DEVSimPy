# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Testable.py ---
#                     --------------------------------
#                          Copyright (c) 2013
#                           Timothee Ville
#                         University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 13/03/2013
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
import os
import zipfile
from tempfile import gettempdir

import wx

import GUI.ZipManager as ZipManager
import GUI.Editor as Editor
# import Container
# import zipfile

###---------------------------------------------------------------------------------------------------------
# NOTE: Testable << object :: Testable mixin is needed to manage tests files and tests executions. It add the OnTestEditor event for the tests files edition
class Testable(object):
	# NOTE: Testable :: OnTestEditor 		=> new event for AMD model. Open tests files in editor
	def OnTestEditor(self, event):
		model_path = os.path.dirname(self.python_path)

		# If selected model is AMD
		if self.isAMD():

			# TODO: Testable :: OnTestEditor => Fix Editor importation
			import Editor
			
			# Create tests files is doesn't exist
			if not ZipManager.Zip.HasTests(model_path):
				self.CreateTestsFiles()

			### list of BDD files
			L = ZipManager.Zip.GetTests(model_path)

			### create Editor with BDD files in tab
			if L:

				mainW = wx.GetApp().GetTopWindow()
				### Editor instanciation and configuration---------------------
				editorFrame = Editor.GetEditor(
					mainW,
					wx.ID_ANY,
					'Features',
					file_type="test"
				)

				for i, s in enumerate(map(lambda l: os.path.join(model_path, l), L)):
					editorFrame.AddEditPage(L[i], s)

				editorFrame.Show()
			### -----------------------------------------------------------

	# NOTE: Testable :: isAMD 				=> Test if the model is an AMD and if it's well-formed
	def isAMD(self):
		cond = False
		if zipfile.is_zipfile(os.path.dirname(self.python_path)):
			cond = True
		return cond

	# NOTE: Testable :: CreateTestsFiles	=> AMD tests files creation
	def CreateTestsFiles(self):
		devsPath = os.path.dirname(self.python_path)
		name = os.path.splitext(os.path.basename(self.python_path))[0]
		zf = ZipManager.Zip(devsPath)

		feat, steps, env = self.CreateFeature(), self.CreateSteps(), Testable.CreateEnv()

		zf.Update([os.path.join('BDD', feat), os.path.join('BDD', steps), os.path.join('BDD', env)])

		if os.path.exists(feat): os.remove(feat)
		if os.path.exists(steps): os.remove(steps)
		if os.path.exists(env): os.remove(env)
		
		#if not zf.HasTests():
			
			#files = zf.GetTests()
			#if not '%s.feature'%name in files:
				#feat = self.CreateFeature()
				#zf.Update([os.path.join('BDD', feat)])
				#os.remove(feat)
			#if not 'steps.py' in files:
				#steps = self.CreateSteps()
				#zf.Update([os.path.join('BDD',steps)])
				#os.remove(steps)
			#if not 'environment.py' in files:
				#env = self.CreateEnv()
				#zf.Update([os.path.join('BDD',env)])
				#os.remove(env)

	# NOTE: Testable :: CreateFeature		=> Feature file creation
	def CreateFeature(self):
		name = os.path.splitext(os.path.basename(self.python_path))[0]
		feature = "%s.feature" % name
		with open(feature, 'w+') as feat:
			feat.write("# -*- coding: utf-8 -*-\n")

		return feature

	# NOTE: Testable :: CreateSteps		=> Steps file creation
	def CreateSteps(self):
		steps = "steps.py"
		with open(steps, 'w+') as step:
			step.write("# -*- coding: utf-8 -*-\n")

		return steps

	# NOTE: Testable :: CreateEnv		=> Environment file creation
	@staticmethod
	def CreateEnv(path=None):
		if path:
			environment = os.path.join(path, 'environment.py')
		else:
			environment = "environment.py"
		with open(environment, 'w+') as env:
			env.write("# -*- coding: utf-8 -*-\n")

		return environment


	# NOTE: Testable :: GetTempTests		=> Create tests on temporary folder for execution
	def GetTempTests(self, global_env=None):
		if not global_env: global_env = False

		### Useful vars definition-----------------------------------------------------------------
		model_path = os.path.dirname(self.python_path)
		basename = os.path.basename(self.python_path)
		name = os.path.splitext(basename)[0]
		tests_files = ZipManager.Zip.GetTests(model_path)
		### ---------------------------------------------------------------------------------------

		### Folder hierarchy construction----------------------------------------------------------
		feat_dir = os.path.join(gettempdir(), "features")
		steps_dir = os.path.join(feat_dir, "steps")
		if not os.path.exists(feat_dir):
			os.mkdir(feat_dir)
		if not os.path.exists(steps_dir):
			os.mkdir(steps_dir)
		### ---------------------------------------------------------------------------------------

		### AMD unzip------------------------------------------------------------------------------
		amd_dir = os.path.join(gettempdir(), "AtomicDEVS")
		if not os.path.exists(amd_dir):
			os.mkdir(amd_dir)
		### ---------------------------------------------------------------------------------------

		### Tests code retriever-------------------------------------------------------------------
		importer = zipfile.ZipFile(model_path)

		feat_name = filter(lambda t: t.endswith('.feature'), tests_files)[0]
		featInfo = importer.getinfo(feat_name)
		feat_code = importer.read(featInfo)

		steps_name = filter(lambda t: t.endswith('steps.py'), tests_files)[0]
		stepsInfo = importer.getinfo(steps_name)
		steps_code = importer.read(stepsInfo)

		if not global_env:
			environment_name = filter(lambda t: t.endswith('environment.py'), tests_files)[0]
			envInfo = importer.getinfo(environment_name)
			env_code = importer.read(envInfo)
		else:
			environment_name = os.path.join(gettempdir(), 'environment.py')
			with open(environment_name, 'r+') as global_env_code:
				env_code = global_env_code.read()

		importer.close()
		### ---------------------------------------------------------------------------------------

		### AMD code retriever---------------------------------------------------------------------
		importer = zipfile.ZipFile(model_path)

		# amd_name = filter(lambda t: t.endswith('%s.py'%name), importer.namelist())[0]
		amd_name = ZipManager.getPythonModelFileName(model_path)
		amd_info = importer.getinfo(amd_name)
		amd_code = importer.read(amd_info)

		### ---------------------------------------------------------------------------------------

		### Tests files creation in temporary directory--------------------------------------------
		tempFeature = os.path.join(feat_dir, "%s.feature" % name)
		tempEnv = os.path.join(feat_dir, "environment.py")
		tempSteps = os.path.join(steps_dir, "%s_steps.py"%name)

		tempAMD = os.path.join(amd_dir, amd_name)

		with open(tempFeature, 'w+') as feat:
			feat.write(feat_code)
		with open(tempSteps, 'w+') as steps:
			steps.write(steps_code)
		with open(tempEnv, 'w+') as env:
			env.write(env_code)

		with open(tempAMD, 'w+') as AMD:
			AMD.write(amd_code)
		### ---------------------------------------------------------------------------------------

		return tempFeature, tempSteps, tempEnv

	# NOTE: Testable :: RemoveTempTests		=> Remove tests on temporary folder
	@staticmethod
	def RemoveTempTests():
		feat_dir = os.path.join(gettempdir(), 'features')

		if os.path.exists(feat_dir):
			for root, dirs, files in os.walk(feat_dir, topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
				for name in dirs:
					os.rmdir(os.path.join(root, name))

			os.rmdir(feat_dir)

		amd_dir = os.path.join(gettempdir(), 'AtomicDEVS')
		if os.path.exists(amd_dir):
			for root, dirs, files in os.walk(amd_dir, topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
        		for name in dirs:
    				os.rmdir(os.path.join(root, name))
		
			os.rmdir(amd_dir)
	