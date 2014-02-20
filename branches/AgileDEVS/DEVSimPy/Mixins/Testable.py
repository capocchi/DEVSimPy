# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Testable.py ---
#                     --------------------------------
#                        Copyright (c) 2013
#                       Timothee Ville
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 18/02/14
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##-

import zipfile
import ZipManager
import wx
import os
from tempfile import gettempdir

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
			if L != []:

				mainW = wx.GetApp().GetTopWindow()
				### Editor instanciation and configuration---------------------
				editorFrame = Editor.GetEditor(
						mainW,
						wx.ID_ANY,
						'Features',
						file_type="test"
				)

				for i,s in enumerate(map(lambda l: os.path.join(model_path, l), L)):
					editorFrame.AddEditPage(L[i], s)

				editorFrame.Show()
				### -----------------------------------------------------------

	# NOTE: Testable :: isAMD 				=> Test if the model is an AMD and if it's well-formed
	def isAMD(self):
		cond = False
		if zipfile.is_zipfile(os.path.dirname(self.python_path)):
			cond = True
		return cond

	# NOTE: Testable :: HasTests			=> Return true if AMD model has tests files
	def hasTests(self):
		model_path = os.path.dirname(self.python_path)
		return ZipManager.Zip.HasTests(model_path)

	# NOTE: Testable :: CreateTestsFiles	=> AMD tests files creation
	def CreateTestsFiles(self):
		devsPath = os.path.dirname(self.python_path)
		name = os.path.splitext(os.path.basename(self.python_path))[0]
		zf = ZipManager.Zip(devsPath)

		self.tests_files_list = self.CreateSpec(), self.CreateBehavior()

		zf.Update([os.path.join("BDD", elem) for elem in self.tests_files_list])

		[os.remove(elem) for elem in self.tests_files_list if os.path.exists(elem)]

	# NOTE: Testable :: CreateFeature		=> Feature file creation
	def CreateSpec(self):
		name = os.path.splitext(os.path.basename(self.python_path))[0]
		specif = "%s.spec"%name
		with open(specif, 'w+') as spec:
			spec.write("# -*- coding: utf-8 -*-\n")

		return specif

	# NOTE: Testable :: CreateSteps		=> Steps file creation
	def CreateBehavior(self):
		behavior = "behavior.py"
		with open(behavior, 'w+') as behave:
			behave.write("# -*- coding: utf-8 -*-\n")

		return behavior

	# NOTE: Testable :: GetTempTests		=> Create tests on temporary folder for execution
	def GetTempTests(self):

		### Useful vars definition-----------------------------------------------------------------
		model_path = os.path.dirname(self.python_path)
		basename = os.path.basename(self.python_path)
		name = os.path.splitext(basename)[0]
		tests_files = ZipManager.Zip.GetTests(model_path)
		### ---------------------------------------------------------------------------------------

		### Folder hierarchy construction----------------------------------------------------------
		spec_dir  = os.path.join(gettempdir(), "specifications")
		if not os.path.exists(spec_dir):
			os.mkdir(spec_dir)
		### ---------------------------------------------------------------------------------------

		### AMD unzip------------------------------------------------------------------------------
		amd_dir = os.path.join(gettempdir(), "AtomicDEVS")
		if not os.path.exists(amd_dir):
			os.mkdir(amd_dir)
		### ---------------------------------------------------------------------------------------

		### Tests code retriever-------------------------------------------------------------------
		importer = zipfile.ZipFile(model_path)

		spec_name = filter(lambda t: t.endswith('.spec'), tests_files)[0]
		specInfo = importer.getinfo(spec_name)
		spec_code = importer.read(specInfo)

		behavior_name = filter(lambda t: t.endswith('behavior.py'), tests_files)[0]
		behaviorInfo = importer.getinfo(behavior_name)
		behavior_code = importer.read(behaviorInfo)


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
		tempSpec = os.path.join(spec_dir, "%s.spec"%name)
		tempBehavior = os.path.join(spec_dir, "%s_behavior.py"%name)

		tempAMD = os.path.join(amd_dir, amd_name)

		with open(tempSpec, 'w+') as spec:
			spec.write(spec_code)
		with open(tempBehavior, 'w+') as behave:
			behave.write(behavior_code)

		with open(tempAMD, 'w+') as AMD:
			AMD.write(amd_code)
		### ---------------------------------------------------------------------------------------

		return tempSpec, tempBehavior

	# NOTE: Testable :: RemoveTempTests		=> Remove tests on temporary folder
	@staticmethod
	def RemoveTempTests():
		spec_dir = os.path.join(gettempdir(), 'specifications')
		if os.path.exists(spec_dir):
			for root, dirs, files in os.walk(spec_dir, topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
        		for name in dirs:
    				os.rmdir(os.path.join(root, name))

			os.rmdir(spec_dir)

		amd_dir = os.path.join(gettempdir(), 'AtomicDEVS')
		if os.path.exists(amd_dir):
			for root, dirs, files in os.walk(amd_dir, topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
        		for name in dirs:
    				os.rmdir(os.path.join(root, name))

			os.rmdir(amd_dir)