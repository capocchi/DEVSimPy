# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# StandaloneNoGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2022
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified:  12/11/23
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

import os, sys
import subprocess
import zipfile
import zipfile
import configparser
import pathlib
import json

from Utilities import GetUserConfigDir
from InteractionYAML import YAMLHandler

def retrieve_file_paths(dirName:str):
    """ Function to return all file paths of the particular directory

    Args:
        dirName (str): Name of the directory

    Returns:
        list: list of file paths
    """
    filePaths = []

    # Read all directory, subdirectories and file lists
    for root, _, files in os.walk(r'{}'.format(dirName).encode('latin').decode('utf-8')):
        ### TODO: filter depending on the necessary lib
        for filename in files:
            if '__pycache__' not in filename:
                #Create the full filepath by using os module.
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

        return os.path.abspath(built_in['DOMAIN_PATH'])
    else:
        return "Domain/"

def execute_script(yaml):
    # Execute the script using subprocess.Popen
    process = subprocess.Popen(["python", "devsimpy-nogui.py", f"{os.path.abspath(yaml)}","10"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = process.communicate()

    # Check if the execution was successful
    if process.returncode == 0:
        # Get the used packages from sys.modules
        used_packages = {mod.split('.')[0] for mod in sys.modules.keys() if '.' in mod}
        return True, used_packages
    else:
        # Print error message and return empty set
        print(f"Error executing script: {stderr.decode()}")
        return False, set()

class StandaloneNoGUI:
    
    ### list of files to zip
    FILENAMES = ["Components.py","Container.py","Decorators.py","devsimpy-nogui.py","DSV.py","InteractionSocket.py","InteractionYAML.py",
				"Join.py","NetManager.py","PluginManager.py","SimulationNoGUI.py","SpreadSheet.py","Utilities.py","XMLModule.py","ZipManager.py",
                "StandaloneNoGUI.py"]

    ## list of dir to zip
    DIRNAMES = ["DomainInterface/","Mixins/","Patterns/"]

    def __init__(self, yaml:str="", outfn:str="devsimpy-nogui-pkg.zip", format:str="Minimal", outdir:str=os.getcwd(), add_sim_kernel:bool=True, add_dockerfile:bool=False, sim_time:str="ntl", rt:bool=False, kernel:str='PyDEVS'):
        """ Generates the zip file with all files needed to execute the devsimpy-nogui script.

		Args:
			yaml (str): yaml file to zip (optional)
			outfn (str): zip file to export all files
            format (str): Minimal export only necessary dependancies while Full export all dependancies (less optimal but more secure)
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
        self.format = format
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
                    FROM python:3.10-slim-buster

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

            ###################################################################
            ###
            ### devsimpy-nogui dependencies files
            ###
            ###################################################################

            ### add all dependencies python files needed to execute devsimpy-nogui
            for fn in StandaloneNoGUI.FILENAMES:
                archive.write(fn)
            
            ###################################################################
            ###
            ### Domain libraries files
            ###
            ###################################################################

            if self.format == "Minimal":
                ### add the Domain libairies according to the DOAMIN_PATH var
                yaml = YAMLHandler(path)
            
                ### to not insert two times the same file
                added_files = set()
                ### lib_path is the directory of the library involved in the yaml model
                for path in yaml.extractPythonPaths():
                    lib_path = os.path.dirname(path)
                    if lib_path.endswith(('.amd','.cmd')):
                        lib_path = os.path.dirname(lib_path)
            
                    ### format the path of the library to include in the archive
                    lib_name = os.path.basename(os.path.dirname(lib_path))
                    for file in retrieve_file_paths(lib_path):
                        if file.endswith(('.py', '.amd', '.cmd')) and '__pycache__' not in file:
                            relative_path = 'Domain'+file.split(lib_name)[1]
                            if relative_path not in added_files:
                                archive.write(file, arcname=relative_path)
                                added_files.add(relative_path)
            else:
                ## To include all Domain dir
                for file in retrieve_file_paths(self.domain_path):
                    if file.endswith(('.py', '.amd', '.cmd')) and \
                                    '__pycache__' not in file:
                        archive.write(file, arcname='Domain'+os.path.join(file.split('Domain')[1], os.path.basename(file)))
    
            ###################################################################
            ###
            ### devsimpy-nogui lib directories
            ###
            ###################################################################

            ### add all dependancies (directories) needed to execute devsimpy-nogui
            for dirname in self.dirnames_abs:
        
                # Call the function to retrieve all files and folders of the assigned directory
                filePaths = retrieve_file_paths(dirname)

                ### select only the selected simulation kernel
                if "DEVSKernel" in os.path.abspath(dirname):
                    new_dirname = os.path.join(dirname,self.kernel)
                    filePaths = retrieve_file_paths(new_dirname)
                    ### add __init__.py of Kernel dir
                    if not os.path.exists(os.path.join(dirname, '__init__.py')):
                        filePaths.append(os.path.join(dirname, '__init__.py'))

                for file in filePaths:
                    if '__pycache__' not in file:
                        archive.write(file)
        
            ###################################################################
            ###
            ### Docker files
            ###
            ###################################################################

            if self.add_dockerfile:
                archive.writestr("DockerFile", self.GetDockerSpec())
                
            ###################################################################
            ###
            ### Config files
            ###
            ###################################################################

            ### write config file
            archive.writestr("config.json", self.GetConfigSpec())
            

            ###################################################################
            ###
            ### Requierements files
            ###
            ###################################################################

            ### TODO: include the self.format condition to choose if you want a minimal or full dependencies

            # Example: Execute a script and get the used packages
            success, packages = execute_script(self.yaml)

            if success:
                print("Used packages:")
                for package in packages:
                    print(package)
            else:
                print("Script execution failed.")


            ### add requirements-nogui.txt file
            ### TODO: packages used in models include in the yaml file are not defined in the requirements.txt!
            archive.write('requirements-nogui.txt', 'requirements.txt')
        
        return True 