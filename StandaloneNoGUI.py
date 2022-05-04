# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# StandaloneNoGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2022
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 03/17/22
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
import zipfile
import configparser
import pathlib
import json

from Utilities import GetUserConfigDir

def retrieve_file_paths(dirName:str):
	""" Function to return all file paths of the particular directory

	Args:
		dirName (str): Name of the directory

	Returns:
		_type_: list of file paths
	"""
	filePaths = []

	# Read all directory, subdirectories and file lists
	for root, directories, files in os.walk(dirName):
		for filename in files:
		# Create the full filepath by using os module.
			filePath = os.path.join(root, filename)
			filePaths.append(filePath)
			
	# return all paths
	return filePaths

def get_domain_path()->str:
    """ Find domain from .devsimpy file	
    """
    
    ### TODO: Domain must be pruned in order to select only the lib used by the model
    
    config_file = os.path.join(GetUserConfigDir(),'.devsimpy')
 
    if os.path.exists(config_file):
        with open(config_file) as f:
            file_content = '[dummy_section]\n' + f.read()

        config_parser = configparser.RawConfigParser()
        config_parser.read_string(file_content)

        built_in = eval(config_parser['dummy_section']['builtin_dict'])

        return built_in['DOMAIN_PATH']
    else:
        return "Domain/"
  
class StandaloneNoGUI:
    
    ### list of files to zip
    FILENAMES = ["Components.py","Container.py","Decorators.py","devsimpy-nogui.py","DSV.py","InteractionSocket.py","InteractionYAML.py",
				"Join.py","NetManager.py","PluginManager.py","SimulationNoGUI.py","SpreadSheet.py","Utilities.py","XMLModule.py","ZipManager.py",
                "StandaloneNoGUI.py"]

    ## list of dir to zip
    DIRNAMES = ["DomainInterface/","Mixins/","Patterns/"]

    def __init__(self, yaml:str="", outfn:str="devsimpy-nogui-pkg.zip", outdir:str=os.getcwd(), add_sim_kernel:bool=True, add_dockerfile:bool=False, sim_time:str="ntl", rt:bool=False, kernel:str='PyDEVS'):
        """ Generates the zip file with all files needed to execute the devsimpy-nogui script.

		Args:
			yaml (str): yaml file to zip (optional)
			outfn (str): zip file to export all files
            outdir (str): directory where zip file is generated
			add_sim_kernel (bool): zip the simlation kernel
			add_dockerfile (bool): zip the DockerFile file
			sim_time (str): simulation time
            rt (str): real time param
            kernel (str): type of simulation kernel (PyDEVS ou PyPDEVS)
	    """

        ### local copy
        self.yaml = yaml
        self.outfn = outfn
        self.outdir = outdir
        self.add_sim_kernel = add_sim_kernel
        self.add_dockerfile = add_dockerfile
        self.sim_time = sim_time
        self.rt = rt
        self.kernel = kernel
        
        ### path of the Domain dir (depending on the .devsimpy config file)
        self.domain_path = get_domain_path()
        ### list of dir to zip
        self.dirnames_abs = map(pathlib.Path,StandaloneNoGUI.DIRNAMES)
        
        ### flags
        self.yaml_exist = self.yaml.endswith('.yaml') and os.path.exists(self.yaml)
        
        ### if simulation kernel need to by zipped
        if self.add_sim_kernel:
            StandaloneNoGUI.DIRNAMES.append("DEVSKernel/")    
        
    def SetYAML(self,yaml):
        self.yaml = yaml
        
    def GetDockerSpec(self):
        """
        """
        return f"""
                    FROM python:3.8-slim-buster

                    WORKDIR /app

                    RUN apt-get update
                    RUN apt-get install -y build-essential
                    
                    RUN pip install pipreqs
                    RUN pipreqs .
        
                    COPY requirements.txt requirements.txt
                    RUN pip install -r requirements.txt

                    COPY . .

                    CMD ["python", "devsimpy-nogui.py", "{os.path.basename(self.yaml)}","ntl"]

                """
                
    def GetConfigSpec(self):
        """
        """
        data = {
            'simulation' : [
                {
                    'ntl' : self.sim_time,
                    'kernel' : self.kernel,
                    'rt': self.rt
                }    
            ]
        }
        
        return json.dumps(data)

    def BuildZipPackage(self) -> None:
        """
        """
 
        if self.yaml == "" and not self.yaml_exist:
            return False
    
        ### create the outfn zip file
        with zipfile.ZipFile(os.path.join(self.outdir,self.outfn), mode="w") as archive:
            
            ### add yaml file 
            path = os.path.abspath(self.yaml)
            archive.write(path, os.path.basename(path))

            ### add all dependencies python files needed to execute devsimpy-nogui
            for fn in StandaloneNoGUI.FILENAMES:
                archive.write(fn)
            
            ### add the Domain libairies according to the DOAMIN_PATH var
            for file in retrieve_file_paths(self.domain_path):
                if file.endswith(('.py', '.amd', '.cmd')):
                    archive.write(file, arcname='Domain'+os.path.join(file.split('Domain')[1], os.path.basename(file)))
    
            ### add all dependancies (directories) needed to execute devsimpy-nogui
            for dirname in self.dirnames_abs:
        
                # Call the function to retrieve all files and folders of the assigned directory
                filePaths = retrieve_file_paths(dirname)
                
                for file in filePaths:
                    archive.write(file)
        
            if self.add_dockerfile:
                archive.writestr("DockerFile", self.GetDockerSpec())
                
            ### write config file
            archive.writestr("config.json", self.GetConfigSpec())
                
            ### add requirements-nogui.txt file
            ### TODO: packages used in models include in the yaml file are not defined in the requirements.txt!
            archive.write('requirements-nogui.txt', 'requirements.txt')
        
        return True 