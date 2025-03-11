# -*- coding: utf-8 -*-

import json
import os
import traceback
import re
import sys

import datetime

def to_Python(val):
    if val in ('true', 'True'):
        return True
    elif val in ('false', 'False'):
        return False
    elif type(val) is str:
        # Try to parse the string as a date
        try:
            datetime_object = datetime.strptime(val, "%Y-%m-%d")
            is_valid_date = True
        except ValueError:
            is_valid_date = False

        # Check if it's a valid date using an if statement
        if is_valid_date:
            return val
        elif str(val).replace('.','').replace('-','').isdigit():
            return eval(str(val))
    elif isinstance(eval(val),list) or isinstance(eval(val),tuple):
        return eval(val)

    return val

class YAMLHandler:
    """ class providing methods for YAML file handling.
    """
    def __init__ (self, filename):
        """ Constructor.
        """

        # assert(filename.endswith('.yaml'))
        
        from Container import Diagram

        self.filename = filename
        self.modelname = os.path.basename(self.filename)
        self.report = {'model_name' : self.modelname}

        # Create diagram object
        self.diagram  = Diagram()
        try :
            self.filename_is_valid = self.diagram.LoadFile(self.filename)
            if self.filename_is_valid != True :
                self.report['success'] = False
                self.report['info'] = 'YAML file load failed'
                sys.stdout.write((json.dumps(self.report)))
        except:
            self.report['success'] = False
            self.report['info'] = traceback.format_exc()
            sys.stdout.write((json.dumps(self.report)))
            raise

    def extractPythonPaths(self)->list:
        """Returns the python path of models included in the YAML file.

        Returns:
            list: list of python path in the YAML file
        """
            
        # Read YAML data from the file
        with open(self.filename, 'r') as file:
            yaml_data = file.read()

        # Define a regular expression to match python_path values
        pattern = r'python_path:\s*(.*?)\n'

        # Use re.findall to find all matches in the YAML data
        matches = re.findall(pattern, yaml_data)

        # Print the extracted python_path values
        return [match for match in matches if match !="''"]

    def getYAMLBlockModelsList(self)->list:
        """ Writes to standard output
            the labels of the blocks (= Atomic Models)
            composing the model described in the file
        """

        if not self.filename_is_valid: return False
        block_list = self.diagram.GetFlatCodeBlockShapeList()
        return [str(a.label) for a in block_list]

    def getYAMLBlockModelArgs(self, label:str)->dict:
        """ Returns the parameters (name and value) of the block identified by the label
            composing the model described in the file.
        """

        if not self.filename_is_valid: return False
        block = self.diagram.GetShapeByLabel(label)
        return block.args

    def setYAMLBlockModelArgs(self, label:str, new_args)->dict:
        """ Saves in YAML file the new values of the parameters
            of the block identified by the label.
            Returns the updated block parameters.
        """

        if not self.filename_is_valid: return False

        ### DEVS block
        block = self.diagram.GetShapeByLabel(label)
        old_args = block.args.copy()

        ### update only existing args
        for arg in old_args:
            if arg in new_args:
                block.args[arg] = to_Python(new_args[arg])

        new_args = self.getYAMLBlockModelArgs(label)

        ### if olg args is equal to the news, no need to save in yaml file
        args_diff_flag = new_args == old_args
        success = self.diagram.SaveFile(self.diagram.last_name_saved) if not args_diff_flag else True

        return {'success': success, 
                'updated_model': label, 
                'yaml_file':self.filename, 
                'updated_yaml_file': not args_diff_flag, 
                'old_args':old_args, 
                'new_args':new_args}

    def getDevsInstance(self):
        """ Returns the DEVS instance built from YAML file.
        """
        from Container import Diagram

        if not self.filename_is_valid: return False

        try :
            return Diagram.makeDEVSInstance(self.diagram)
        except:
            self.report['devs_instance'] = None
            self.report['success'] = False
            self.report['info'] = traceback.format_exc()
            sys.stdout.write((json.dumps(self.report)))
            return False

    def getJS(self):
        """ 
        """

        from Join import makeDEVSConf, makeJoin

        if not self.filename_is_valid: return False

        addInner = []
        liaison = []
        model = {}
        labelEnCours = str(os.path.basename(self.diagram.last_name_saved).split('.')[0])

        # path = os.path.join(os.getcwd(),os.path.basename(a.last_name_saved).split('.')[0] + ".js") # genere le fichier js dans le dossier de devsimpy
        # path = filename.split('.')[0] + ".js" # genere le fichier js dans le dossier du dsp charge.

        #Position initial du 1er modele
        x = [40]
        y = [40]
        bool = True

        model, liaison, addInner = makeJoin(self.diagram, addInner, liaison, model, bool, x, y, labelEnCours)
        makeDEVSConf(model, liaison, addInner, f"{labelEnCours}.js")
