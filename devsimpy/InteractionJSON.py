# -*- coding: utf-8 -*-

import json
import os
import traceback
import sys

class JSONHandler:
    """ class providing methods for JSON file handling.
    """
    def __init__ (self, filename=None):
        """ Constructor.
        """
        from Container import Diagram
        
        ### local copy
        self.filename = filename

        self.json_obj = {"cells":[], "description": "No description"}

        if self.filename:
            self.modelname = os.path.basename(self.filename)
            self.report = {'model_name' : self.modelname}

            # Create diagram object
            self.diagram  = Diagram()
            try :
                self.filename_is_valid = self.diagram.LoadFile(self.filename)
                if not self.filename_is_valid:
                    self.report['success'] = False
                    self.report['info'] = "JSON file load failed"
                    sys.stdout.write((json.dumps(self.report)))
            except:
                self.report['success'] = False
                self.report['info'] = traceback.format_exc()
                sys.stdout.write((json.dumps(self.report)))
                raise

    def getJSON(self, diagram=None, with_graph_data=False):
        """ Make JSON representation of the model from the diagram.
        """
        from Container import ConnectionShape, CodeBlock, ContainerBlock

        # Initialize JSON object if it does not exist (makeJSON is called recursively)
        if not diagram:
            diagram = self.diagram
        
        for c in diagram.GetShapeList():
            ### if c is coupled model
            if isinstance(c, ContainerBlock):
                D = {"type": "devs.Coupled",
                     "id": c.id,
                     "label": c.label,
                     "inPorts":[f"in{i}" for i in range(c.input)],
                     "outPorts":[f"out{i}" for i in range(c.output)],
                     "behavior": {
                        "python_path": c.python_path,
                        "model_path": c.model_path,
                        "attrs":{"text": {"text": c.label}}
                     },
                     "embeds": [s.label for s in c.GetFlatBlockShapeList()]
                     }
                
                if with_graph_data:
                    D.update({
                     "size":{"width": c.w, "height": c.h},
                     "position":{"x": c.x[0], "y": c.y[0]},
                     })

                self.json_obj['cells'].append(D)

                # recursion
                self.getJSON(c)

            else:
                ### if c is a connection
                if isinstance(c, ConnectionShape):
                    D = {"type": "devs.Link",
                         "id": str(id(c)),
                         "z":0,
                         "attrs":{},
                         'source':{"selector": ".outPorts>g:nth-child(1)>circle"},
                         'target':{"selector": ".inPorts>g:nth-child(1)>circle"}}
                    
                    model1, portNumber1 = c.input
                    model2, portNumber2 = c.output

                    D['source']['id'] = model1.label
                    D['target']['id'] = model2.label
                
                ### if c is an atomic model
                elif isinstance(c, CodeBlock): 
                    D = {"type": "devs.Atomic",
                         "id": c.id,
                         "label": c.label,
                         "inPorts":[f"in{i}" for i in range(c.input)],
                         "outPorts":[f"out{i}" for i in range(c.output)],
                         "behavior": {
                            "python_path": c.python_path,
                            "model_path": c.model_path,
                            "attrs":{"text": {"text": c.label}},
                            "prop" :{"data": c.args}}
                         }

                    if with_graph_data:
                        D.update({
                        "size":{"width": c.w, "height": c.h},
                        "position":{"x": c.x[0], "y": c.y[0]},
                        })
                    
                        for i in range(c.input):
                            D["behavior"]["attrs"].update( {f".inPorts>.port{i}>.port-label":{"text":f"in{i}"},
                                            f".inPorts>.port{i}>.port-body":{ "port":{"id":f"in{i}",
                                                                                      "type":"in"}},
                                            f".inPorts>.port{i}":{ "ref":".body",
                                                                  "ref-y": float(i+1)/(c.input+1)}
                                            })
                        for j in range(c.output):
                            D["behavior"]["attrs"].update( {f".outPorts>.port{j}>.port-label":{"text":f"out{j}"},
                                            f".outPorts>.port{j}>.port-body":{ "port":{"id":f"out{j}",
                                                                                       "type":"out"}},
                                            f".outPorts>.port{j}":{ "ref":".body",
                                                                   "ref-y": float(j+1)/(c.output+1)}
                                                                   })

                else: #Input or Output port
                    D = None
                    
                if D:
                    self.json_obj['cells'].append(D)

        return self.json_obj
