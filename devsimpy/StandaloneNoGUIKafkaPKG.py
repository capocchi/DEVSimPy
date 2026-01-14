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
import logging

import gettext
_ = gettext.gettext

from StandaloneNoGUI import retrieve_file_paths, add_library_to_archive

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
                 output_topic:str="",
                 enable_log:bool=False):
        """ Generates the zip file with all files needed to execute the kafka-based worker od aDEVS model.
	    """

        ### local copy
        self.model_instance = model_instance
        self.model_label = label
        self.outfn = outfn
        self.outdir = outdir
        self.kernel = 'BrokerDEVS'
        self.kafka_contianer_name = kafka_container_name
        self.kafka_boostrap = kafka_boostrap
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.enable_log = enable_log

        self.kafka_port = self.kafka_boostrap.split(':')[-1] or "9092"
        
        ### Setup logging
        self.logger = logging.getLogger(__name__)
        # Clear any existing handlers to prevent duplicates
        self.logger.handlers.clear()
        if self.enable_log:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            self.logger.propagate = False
        else:
            self.logger.setLevel(logging.CRITICAL)
        
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
      python DEVSKernel/BrokerDEVS/DEVSStreaming/run_worker.py
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
        self.logger.info(f"Starting BuildZipPackage process for Kafka worker")
        self.logger.info(f"Output file: {os.path.join(self.outdir, self.outfn)}")
        self.logger.info(f"Model: {self.model_label}, Kernel: {self.kernel}")
     
        ### create the outfn zip file
        with zipfile.ZipFile(os.path.join(self.outdir,self.outfn), mode="w") as archive:
            
            ###################################################################
            ###
            ### devsimpy-nogui dependencies files
            ###
            ###################################################################

            self.logger.info(f"Adding {len(StandaloneNoGUIKafkaPKG.FILENAMES)} Python dependency files")
            ### add all dependencies python files needed to execute devsimpy-nogui
            for fn in StandaloneNoGUIKafkaPKG.FILENAMES:
                # Use current directory to find the files
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(current_dir, fn)
                self.logger.info(f"Adding Python file: {fn}")
                archive.write(file_path, arcname=fn)
            self.logger.info(f"Python dependency files added successfully")
            
            ###################################################################
            ###
            ### Domain libraries files
            ###
            ###################################################################

            self.logger.info(f"Adding Domain library files")
            # Get the absolute directory path where the model Python file is located
            domain_path = os.path.dirname(self.model_instance.python_path)
            self.logger.info(f"Domain path: {domain_path}")
            
            # Use add_library_to_archive which properly handles the path
            files_added = add_library_to_archive(archive, domain_path)
            self.logger.info(f"Added {files_added} files from {domain_path}")
            self.logger.info(f"Domain library files added successfully")

            ###################################################################
            ###
            ### devsimpy-nogui lib directories
            ###
            ###################################################################

            ### Re-create the iterator for directories to ensure it's fresh
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.dirnames_abs = map(pathlib.Path, StandaloneNoGUIKafkaPKG.DIRNAMES)
            dirnames_list = list(self.dirnames_abs)
            self.logger.info(f"Adding {len(dirnames_list)} dependency directories")
            
            ### add all dependancies (directories) needed to execute devsimpy-nogui
            for dirname in dirnames_list:
        
                # Make the path absolute by joining with current directory
                dirname_abs = os.path.join(current_dir, str(dirname))
                dirname_name = os.path.basename(dirname_abs.rstrip('/\\'))
                self.logger.info(f"Processing directory: {dirname_abs}")

                # Call the function to retrieve all files and folders of the assigned directory
                filePaths = retrieve_file_paths(dirname_abs)
                self.logger.info(f"Found {len(filePaths)} files in {dirname_abs}")

                ### select only the selected simulation kernel
                if 'DEVSKernel' in os.path.abspath(dirname_abs):
                    self.logger.info(f"Using kernel: {self.kernel}")
                    new_dirname = os.path.join(dirname_abs, self.kernel)
                    filePaths = retrieve_file_paths(new_dirname)
                    ### add __init__.py of Kernel dir only if it exists
                    init_file = os.path.join(dirname_abs, '__init__.py')
                    if os.path.exists(init_file):
                        filePaths.append(init_file)
                    self.logger.info(f"Kernel files added: {len(filePaths)} files")

                for file in filePaths:
                    if '__pycache__' not in file and os.path.exists(file):
                        # Extract relative path from directory name onwards
                        try:
                            file_suffix = file.split(dirname_name, 1)[1].lstrip(os.sep)
                            relative_path = os.path.join(dirname_name, file_suffix).replace(os.sep, '/')
                            self.logger.info(f"Adding file: {file} as {relative_path}")
                            archive.write(file, arcname=relative_path)
                        except IndexError:
                            self.logger.warning(f"Cannot parse path for {file}")
                            continue

            ###################################################################
            ###
            ### Docker files
            ###
            ###################################################################

            self.logger.info(f"Adding Docker files")
            archive.writestr('Dockerfile', self.GetDockerSpec())
            archive.writestr('docker-compose-kafka.yml', self.GetDockerComposeKafkaSpec())
            archive.writestr('docker-compose-worker.yml', self.GetDockerComposeWorkerSpec())
            self.logger.info(f"Docker files added successfully")

            ###################################################################
            ###
            ### Config files
            ###
            ###################################################################

            self.logger.info(f"Adding configuration file (.env)")
            ### write config file
            archive.writestr('.env', self.GetConfigSpec())
            self.logger.info(f"Configuration file added successfully")
            
            ###################################################################
            ###
            ### Requierements files
            ###
            ###################################################################

            self.logger.info(f"Adding requirements file")
            try:
                ### Create a basic requirements file if none exists
                basic_requirements = "confluent-kafka>=2.3.0"
                archive.writestr('requirements.txt', basic_requirements)
                self.logger.info(f"Requirements file added successfully")
            except Exception as e:
                self.logger.error(f"Error handling requirements file: {e}")
                sys.stdout.write(f"Error handling requirements file: {e}\n")
                return False
        
        self.logger.info(f"BuildZipPackage completed successfully: {os.path.join(self.outdir, self.outfn)}")
        return True 