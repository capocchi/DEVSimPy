# -*- coding: utf-8 -*-

import json
import os
import traceback
from datetime import datetime

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
    return val

class YAMLHandler:
    """ class providing methods for YAML file handling.
    """
    def __init__ (self, filename):
        """ Constructor.
        """
        from Container import Diagram

        self.filename = filename
        self.modelname = os.path.basename(self.filename)

        self.report = {'model_name' : self.modelname}

        self.json_obj = None

        # Create diagram object
        self.diagram  = Diagram()
        try :
            self.filename_is_valid = self.diagram.LoadFile(self.filename)
            if self.filename_is_valid != True :
                self.report['success'] = False
                self.report['info'] = 'YAML file load failed'
                print((json.dumps(self.report)))
        except:
            self.report['success'] = False
            self.report['info'] = traceback.format_exc()
            print((json.dumps(self.report)))
            raise


    def getYAMLBlockModelsList(self):
        """ Writes to standard output
            the labels of the blocks (= Atomic Models)
            composing the model described in the file
        """

        if self.filename_is_valid != True: return False

        block_list = self.diagram.GetFlatCodeBlockShapeList()
        return [str(a.label) for a in block_list]


    def getYAMLBlockModelArgs(self, label):
        """ Returns the parameters (name and value) of the block identified by the label
            composing the model described in the file.
        """

        if self.filename_is_valid != True: return False

        block = self.diagram.GetShapeByLabel(label)
        return block.args


    def setYAMLBlockModelArgs(self, label, new_args):
        """ Saves in YAML file the new values of the parameters
            of the block identified by the label.
            Returns the updated block parameters.
        """

        if self.filename_is_valid != True: return False

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

    def getJSON(self, diagram=None):
        """ Make JSON representation of the model from YAML file.
        """
        from Container import ConnectionShape, CodeBlock, ContainerBlock

        if self.filename_is_valid != True: return False

        # Initialize JSON object if it does not exist (makeJSON is called recursively)
        if not diagram:
            self.json_obj = {"cells":[],"description": "No description"}
            diagram = self.diagram
        
        for c in diagram.GetShapeList():
            ### if c is coupled model            
            if isinstance(c, ContainerBlock):
                D = {"type":"devs.Coupled",
                     "angle":0,
                     "id":c.label,
                     "z":1,
                     "size":{"width":c.w,"height":c.h},
                     "position":{"x":c.x[0],"y":c.y[0]},
                     "inPorts":["in%d"%i for i in range(c.input)],
                     "outPorts":["out%d"%i for i in range(c.output)],
                     "attrs":{"text": {"text":c.label}}
                     }

                ### embeds key
                shapes = c.GetFlatBlockShapeList()
                D["embeds"] = [s.label for s in shapes]

                self.json_obj['cells'].append(D)

                # add JSON description of coupled model components
                self.getJSON(c)

            else:
                ### if c is a connection
                if isinstance(c, ConnectionShape):
                    D = {"type":"devs.Link",
                         "id":str(id(c)),
                         "z":0,"attrs":{},
                         'source':{"selector":".outPorts>g:nth-child(1)>circle"},
                         'target':{"selector":".inPorts>g:nth-child(1)>circle"}}
                    model1, portNumber1 = c.input
                    model2, portNumber2 = c.output

                    D['source']['id'] = model1.label
                    D['target']['id'] = model2.label
                
                ### if c is an atomic model
                elif isinstance(c, CodeBlock): 
                    D = {"type":"devs.Atomic",
                         "angle":0,
                         "id":c.label,
                         "z":1,
                         "size":{"width":c.w,"height":c.h},
                         "position":{"x":c.x[0],"y":c.y[0]},
                         "inPorts":["in%d"%i for i in range(c.input)],
                         "outPorts":["out%d"%i for i in range(c.output)],
                         "attrs":{"text": {"text":c.label}},
                         "prop" :{"data" : c.args}
                         }

                    for i in range(c.input):
                        D["attrs"].update( {".inPorts>.port%d>.port-label"%i:{"text":"in%d"%i},
                                            ".inPorts>.port%d>.port-body"%i:{ "port":{"id":"in%d"%i,
                                                                                      "type":"in"}},
                                            ".inPorts>.port%d"%i:{ "ref":".body",
                                                                  "ref-y":float(i+1)/(c.input+1)}
                                            })
                    for j in range(c.output):
                        D["attrs"].update( {".outPorts>.port%d>.port-label"%j:{"text":"out%d"%j},
                                            ".outPorts>.port%d>.port-body"%j:{ "port":{"id":"out%d"%j,
                                                                                       "type":"out"}},
                                            ".outPorts>.port%d"%j:{ "ref":".body",
                                                                   "ref-y":float(j+1)/(c.output+1)}
                                                                   })

                else: #Input or Output port
                    D = None
                    
                if (D!= None):
                     self.json_obj['cells'].append(D)

        return self.json_obj

    def getDevsInstance(self):
        """ Returns the DEVS instance built from YAML file.
        """
        from Container import Diagram

        if self.filename_is_valid != True: return False

        try :
            return Diagram.makeDEVSInstance(self.diagram)
        except:
            self.report['devs_instance'] = None
            self.report['success'] = False
            self.report['info'] = traceback.format_exc()
            print((json.dumps(self.report)))
            return False

    def getJS(self):
        """ 
        """

        from Join import makeDEVSConf, makeJoin

        if self.filename_is_valid != True : return False

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
        makeDEVSConf(model, liaison, addInner, "%s.js"%labelEnCours)
