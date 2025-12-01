# -*- coding: utf-8 -*-

'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# StandaloneNoGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified:  11/17/25
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
'''

import os
import zipfile
import zipfile
import configparser
import pathlib
import json
import sys

try:
    from importlib.metadata import distributions
except ImportError:
    # Fallback pour Python < 3.8
    from importlib_metadata import distributions

from Utilities import GetUserConfigDir
from InteractionYAML import YAMLHandler
from ZipManager import get_imported_modules

def get_pip_packages()->list:
    """Get the installed pip package.

    Returns:
        list: list of names of installed pip package
    """
    try:
        installed_packages = [dist.name for dist in distributions()]
        return installed_packages
    except Exception as e:
        sys.stdout.write(f"Error retrieving pip packages: {e}")
        return []

def retrieve_file_paths(dirName:str)->list:
    """ Function to return all file paths of the particular directory

    Args:
        dirName (str): Name of the directory

    Returns:
        list: list of file paths
    """
    ### Read all directory, subdirectories and file lists
    ### Create the full filepath by using os module.
    return [ os.path.join(root, filename) 
                 for root, _, files in os.walk(r'{}'.format(dirName).encode('latin').decode('utf-8')) \
                 for filename in files \
                 if '__pycache__' not in filename]

def get_domain_path()->str:
    """ Find domain from .devsimpy file.
    """
     
    config_file = os.path.join(GetUserConfigDir(),'.devsimpy')
 
    if os.path.exists(config_file):
        with open(config_file) as f:
            file_content = '[dummy_section]\n' + f.read()

        config_parser = configparser.RawConfigParser()
        config_parser.read_string(file_content)

        built_in = eval(config_parser['dummy_section']['settings'])

        return os.path.abspath(built_in['DOMAIN_PATH'])
    else:
        return 'Domain/'

def add_library_to_archive(archive, lib_path):
    """
    Add library files to archive with proper path formatting.
    
    Args:
        archive: Archive object (ZipFile/TarFile)
        lib_path: Path to the library
        added_files: Set tracking added files to prevent duplicates
        
    Returns:
        int: Number of files successfully added
    """
    if not os.path.exists(lib_path):
        sys.stderr.write(_(f"\nWarning: Library path does not exist: {lib_path}\n"))
        return 0
    
    ### to not insert two times the same file
    added_files = set()
        
    is_domain_lib = "Domain" in lib_path
    lib_name = os.path.basename(os.path.dirname(lib_path) if is_domain_lib else lib_path)
    files_added = 0
    
    try:
        for file_path in retrieve_file_paths(lib_path):
            # Skip cache and hidden directories
            if any(skip in file_path for skip in ['__pycache__', '.git', '.svn']):
                continue
            
            # Calculate relative archive path
            try:
                file_suffix = file_path.split(lib_name, 1)[1].lstrip(os.sep)
            except IndexError:
                sys.stderr.write(_(f"\nWarning: Cannot parse path for {file_path}\n"))
                continue
            
            # Build target path in archive
            if is_domain_lib:
                relative_path = os.path.join('Domain', file_suffix)
            else:
                relative_path = os.path.join('Domain', lib_name, file_suffix)
            
            # Normalize path separators
            relative_path = relative_path.replace(os.sep, '/')
            
            # Add to archive if unique
            if relative_path not in added_files:
                try:
                    archive.write(file_path, arcname=relative_path)
                    added_files.add(relative_path)
                    files_added += 1
                except Exception as e:
                    sys.stderr.write(_(
                        f"\nError adding {file_path} to archive: {e}\n"
                    ))
    
    except Exception as e:
        sys.stderr.write(_(f"\nError processing library {lib_path}: {e}\n"))
    
    return files_added

class StandaloneNoGUI:
    
    ### list of files to zip
    FILENAMES = ['Components.py','Container.py','Decorators.py','devsimpy-nogui.py','DSV.py','InteractionSocket.py','InteractionYAML.py',
				'Join.py','NetManager.py','PluginManager.py','SimulationNoGUI.py','SpreadSheet.py','Utilities.py','XMLModule.py','ZipManager.py',
                'StandaloneNoGUI.py', 'config.py']

    ## list of dir to zip
    DIRNAMES = ['DomainInterface/','Mixins/','Patterns/']

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

        assert self.yaml.endswith('.yaml'), _("YAML file name must end with '.yaml'!")
        assert os.path.exists(self.yaml), _("YAML file must exist!")

        ### list of dir to zip
        self.dirnames_abs = map(pathlib.Path, StandaloneNoGUI.DIRNAMES)
        
        ### if simulation kernel need to by zipped
        if self.add_sim_kernel:
            StandaloneNoGUI.DIRNAMES.append('DEVSKernel/')
        
    def GetDockerSpec(self):
        """
        """
        return f"""
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update
RUN apt-get install -y build-essential

RUN pip install pipreqs
RUN pipreqs .

COPY requirements-devsimpy-nogui.txt requirements-devsimpy-nogui.txt
RUN pip install -r requirements-devsimpy-nogui.txt

COPY . .

CMD ["python", "devsimpy-nogui.py", "-kernel {self.kernel}", "{os.path.basename(self.yaml)}", "ntl"]

                """

    def GetDockerComposeSpec(self):
        """
        """
        return f"""
version: '3.8'

services:
  {os.path.basename(self.yaml).split('.')[0].lower()}:
    container_name: {os.path.basename(self.yaml).split('.')[0].lower()}-app
    build: .
    image: {os.path.basename(self.yaml).split('.')[0].lower()}:latest
    # Ajoutez d'autres configurations si nécessaire :
    # volumes:
    #   - ./data:/app/data
    # ports:
    #   - "8080:8080"
    restart: unless-stopped
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

            if self.add_sim_kernel:
                ### add all dependencies python files needed to execute devsimpy-nogui
                for fn in StandaloneNoGUI.FILENAMES:
                    # Use current directory to find the files
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    file_path = os.path.join(current_dir, fn)
                    archive.write(file_path, arcname=fn)
            
            ###################################################################
            ###
            ### Domain libraries files
            ###
            ###################################################################

            ### name of domain librairies used in the simulation model
            # domain_lib = set()
            domain_module_lib = set()

            if self.format == 'Minimal':
                ### add the Domain libairies according to the DOAMIN_PATH var
                yaml = YAMLHandler(path)
            
                ### lib_path is the directory of the library involved in the yaml model
                for path in yaml.extractPythonPaths():
                    a = os.path.basename(path).split('.')[0]
                    domain_module_lib.add(a)
                    lib_path = os.path.dirname(path)
                    if lib_path.endswith(('.amd','.cmd')):
                        domain_module_lib.remove(a)
                        domain_module_lib.add(os.path.basename(lib_path).split('.')[0])
                        lib_path = os.path.dirname(lib_path)
                    
                    ### Add lib dir to the archive
                    add_library_to_archive(archive, lib_path)
            else:
                ### path of the Domain dir (depending on the .devsimpy config file)
                domain_path = get_domain_path()
       
                ## To include all Domain dir
                for file in retrieve_file_paths(domain_path):
                    if file.endswith(('.py', '.amd', '.cmd')) and \
                                    '__pycache__' not in file:
                        archive.write(file, arcname='Domain'+os.path.join(file.split('Domain')[1], os.path.basename(file)))

            ###################################################################
            ###
            ### devsimpy-nogui lib directories
            ###
            ###################################################################

            if self.add_sim_kernel:
                ### add all dependancies (directories) needed to execute devsimpy-nogui
                for dirname in self.dirnames_abs:
            
                    dirname = os.path.join(dirname)

                    # Call the function to retrieve all files and folders of the assigned directory
                    filePaths = retrieve_file_paths(dirname)

                    ### select only the selected simulation kernel
                    if 'DEVSKernel' in os.path.abspath(dirname):
                        new_dirname = os.path.join(dirname, self.kernel)
                        filePaths = retrieve_file_paths(new_dirname)
                        ### add __init__.py of Kernel dir only if it exists
                        init_file = os.path.join(dirname, '__init__.py')
                        if os.path.exists(init_file):
                            filePaths.append(init_file)

                    for file in filePaths:
                        if '__pycache__' not in file and os.path.exists(file):
                            archive.write(file)

                ###################################################################
                ###
                ### Docker files
                ###
                ###################################################################

                if self.add_dockerfile:
                    archive.writestr('Dockerfile', self.GetDockerSpec())
                    archive.writestr('docker-compose.yml', self.GetDockerComposeSpec())

                ###################################################################
                ###
                ### Config files
                ###
                ###################################################################

                ### write config file
                archive.writestr('config.json', self.GetConfigSpec())
                
                ###################################################################
                ###
                ### Requierements files
                ###
                ###################################################################

                pip_packages_used_to_add_in_requirements = set()

                # Get the list of available pip packages
                installed_pip_packages = get_pip_packages()

                for mod in domain_module_lib:
                    imported_modules = get_imported_modules(mod)
                    for name in imported_modules:
                        if not 'DomainInterface' in name and name in installed_pip_packages:
                            pip_packages_used_to_add_in_requirements.add(name)

                ### Get the requirements file path
                current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                print(os.path.join(current_dir, 'requirements-nogui.txt'))
                requirements_file = os.path.join(current_dir, 'requirements-nogui.txt')
                
                ### if additionnal pip package are used in devs atomic model, we need to add them in the requirements.txt file
                if pip_packages_used_to_add_in_requirements:
                    try:
                        # Read the existing content of the txt file if it exists
                        if os.path.exists(requirements_file):
                            with open(requirements_file, 'r') as file:
                                to_write_in_requirements = file.read()
                        else:
                            to_write_in_requirements = "# DEVSimPy requirements\n"

                        ### Add the pip_packages_to_add_in_requirements
                        to_write_in_requirements += '\n' + '\n### Additionnal requirements for model librairies\n' + '\n'.join(pip_packages_used_to_add_in_requirements)

                        archive.writestr('requirements-devsimpy-nogui.txt', to_write_in_requirements)
                    except Exception as e:
                        sys.stdout.write(f"Error handling requirements file: {e}\n")
                        return False
                else:
                    try:
                        ### add requirements.txt file in the archive from the requirements-nogui.txt file
                        if os.path.exists(requirements_file):
                            archive.write(requirements_file, 'requirements-devsimpy-nogui.txt')
                        else:
                            ### Create a basic requirements file if none exists
                            basic_requirements = "# DEVSimPy requirements\n"
                            archive.writestr('requirements-devsimpy-nogui.txt', basic_requirements)
                    except Exception as e:
                        sys.stdout.write(f"Error handling requirements file: {e}\n")
                        return False
        return True 