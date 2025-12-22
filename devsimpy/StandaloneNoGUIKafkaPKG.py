# -*- coding: utf-8 -*-

'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# StandaloneNoGUIKafkaPKG.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/01/25
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
import pathlib
import zipfile
import sys

import gettext
_ = gettext.gettext

from StandaloneNoGUI import retrieve_file_paths

class StandaloneNoGUIKafkaPKG:
    
    ### list of files to zip
    FILENAMES = []

    ## list of dir to zip
    DIRNAMES = ['DomainInterface/','Patterns/', 'DEVSKernel/']

    def __init__(self, model_instance:None,
                 label:str="",
                 outfn:str="devsimpy-nogui-pkg.zip", 
                 outdir:str=os.getcwd(), 
                 kafka_container_name:str="broker", 
                 kafka_boostrap:str="localhost:9092",
                 input_topic:str="",
                 output_topic:str=""):
        """ Generates the zip file with all files needed to execute the kafka-based worker od aDEVS model.
	    """

        ### local copy
        self.model_instance = model_instance
        self.model_label = label
        self.outfn = outfn
        self.outdir = outdir
        self.kernel = 'KafkaDEVS'
        self.kafka_contianer_name = kafka_container_name
        self.kafka_boostrap = kafka_boostrap
        self.input_topic = input_topic
        self.output_topic = output_topic

        self.kafka_port = self.kafka_boostrap.split(':')[-1] or "9092"
        
        if self.model_instance:
          if self.model_instance.isPY():

            assert os.path.exists(self.model_instance.python_path), _("Python model file must exist!")
            assert self.model_instance.python_path.endswith('.py'), _("Python model file name must end with '.py'!")        

            # Nom du fichier sans extension
            self.model_class = os.path.splitext(os.path.basename(self.model_instance.python_path))[0]

            # Chemin relatif à partir de 'Domain'
            rel_path = "Domain" + self.model_instance.python_path.split("Domain", 1)[1]
            # Convertir en Path et forcer les séparateurs "/"
            self.model_path = pathlib.PurePath(rel_path).as_posix()
          else:
              sys.stdout.write("Not implemented!")
        else:
            sys.stdout.write("Model instance param must be valid")


        ### list of dir to zip
        self.dirnames_abs = map(pathlib.Path, StandaloneNoGUIKafkaPKG.DIRNAMES)
        
    def GetDockerSpec(self):
        """
        """
        return r"""
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
"""
    
    def GetDockerComposeKafkaSpec(self):
        """
        """
        return """
services:
  broker:
    image: apache/kafka:latest
    container_name: ${KAFKA_CONTAINER_NAME}
    ports:
      - "${KAFKA_PORT}:${KAFKA_PORT}"
      - "9094:9094"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: ${KAFKA_CONTAINER_NAME},controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:${KAFKA_PORT},PLAINTEXT_HOST://0.0.0.0:9094,CONTROLLER://localhost:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://${KAFKA_CONTAINER_NAME}:${KAFKA_PORT},PLAINTEXT_HOST://localhost:9094
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@localhost:9093
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_NUM_PARTITIONS: 3
    networks:
      - kafka-network

kafdrop:
    image: obsidiandynamics/kafdrop:latest
    container_name: kafdrop
    ports:
      - "9000:9000"
    environment:
      KAFKA_BROKERCONNECT: "${KAFKA_CONTAINER_NAME}:${KAFKA_PORT}"
      SERVER_SERVLET_CONTEXTPATH: "/"
    depends_on:
      - ${KAFKA_CONTAINER_NAME}
    networks:
      - kafka-network

networks:
  kafka-network:
    name: kafka-network
"""

    def GetDockerComposeWorkerSpec(self):
      return f"""
services:
  worker:
    build: .
    container_name: worker-{self.model_label}
    env_file:
      - .env
    environment:
      PYTHONPATH: ${{PYTHONPATH:-/app}}
    volumes:
      - ./output:/app/output
    networks:
      - kafka-network
    command: >
      python DEVSKernel/KafkaDEVS/MS4Me/run_worker.py
      --model-path ${{MODEL_PATH}}
      --class-name ${{MODEL_CLASS}}
      --label {self.model_label}
      --in-topic ${{INPUT_TOPIC}}
      --out-topic ${{OUTPUT_TOPIC}}
      --bootstrap ${{KAFKA_CONTAINER_NAME}}:${{KAFKA_PORT}}

networks:
  kafka-network:
    name: kafka-network
    external: true
"""
     
    def GetConfigSpec(self):
        """
        """
        data = f"""
# ========================================
# Kafka DEVS Worker Configuration
# ========================================

KAFKA_CONTAINER_NAME={self.kafka_contianer_name}
KAFKA_PORT={self.kafka_port}

# --- Class Model Configuration ---
MODEL_PATH={self.model_path}
MODEL_CLASS={self.model_class}

# --- Worker Model Configuration ---
MODEL_LABEL={self.model_label}
INPUT_TOPIC={self.input_topic}
OUTPUT_TOPIC={self.output_topic}

# --- Python Configuration ---
PYTHONPATH=/app
"""
        return data

    def BuildZipPackage(self) -> None:
        """
        """
     
        ### create the outfn zip file
        with zipfile.ZipFile(os.path.join(self.outdir,self.outfn), mode="w") as archive:
            
            ###################################################################
            ###
            ### devsimpy-nogui dependencies files
            ###
            ###################################################################

           
            ### add all dependencies python files needed to execute devsimpy-nogui
            for fn in StandaloneNoGUIKafkaPKG.FILENAMES:
                # Use current directory to find the files
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(current_dir, fn)
                archive.write(file_path, arcname=fn)
            
            ###################################################################
            ###
            ### Domain libraries files
            ###
            ###################################################################

            domain_path = os.path.dirname(self.model_path)
            for file in retrieve_file_paths(domain_path):
                if file.endswith(('.py', '.amd', '.cmd')) and '__pycache__' not in file:
                    print(file,domain_path)
                    # Créer un arcname correct avec séparateurs "/" pour l'archive
                    rel_path = pathlib.PurePath(file).relative_to('Domain')
                    archive.write(file, arcname=f"Domain/{rel_path.as_posix()}")

            ###################################################################
            ###
            ### devsimpy-nogui lib directories
            ###
            ###################################################################

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

            archive.writestr('Dockerfile', self.GetDockerSpec())
            archive.writestr('docker-compose-kafka.yml', self.GetDockerComposeKafkaSpec())
            archive.writestr('docker-compose-worker.yml', self.GetDockerComposeWorkerSpec())

            ###################################################################
            ###
            ### Config files
            ###
            ###################################################################

            ### write config file
            archive.writestr('.env', self.GetConfigSpec())
            
            ###################################################################
            ###
            ### Requierements files
            ###
            ###################################################################

            try:
                ### Create a basic requirements file if none exists
                basic_requirements = "confluent-kafka>=2.3.0"
                archive.writestr('requirements.txt', basic_requirements)
            except Exception as e:
                sys.stdout.write(f"Error handling requirements file: {e}\n")
                return False
                    
        return True 