#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour lancer un worker Kafka DEVS à partir du chemin d'un modèle atomique.
Usage: python run_worker.py --model-path <path> --label <model_name> [options]
Exemple à éxécuter dans une console avant test_worker_messages:
python run_worker.py --model-path ..\..\..\Domain\Collector\MessagesCollector.py --label MessageCollector --class-name MessagesCollector --bootstrap localhost:9092
"""

import sys
import argparse
import time
import signal
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("WorkerLauncher")

# Fonction pour charger dynamiquement un modèle depuis un .amd
def load_model_from_amd(amd_path: str, class_name: str = None):
    """Load atomic modele from its .amd (zip)"""
    import zipfile
    import tempfile
    import shutil
    import importlib.util
    
    amd_path = Path(amd_path).resolve()
    tmp_dir = Path(tempfile.mkdtemp(prefix="devsimpy_worker_"))
    
    try:
        with zipfile.ZipFile(amd_path, "r") as zf:
            zf.extractall(tmp_dir)
        
        py_files = list(tmp_dir.rglob("*.py"))
        if not py_files:
            raise RuntimeError(f"No .py file found in {amd_path}")
        
        main_py = py_files[0]
        spec = importlib.util.spec_from_file_location(main_py.stem, main_py)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if class_name:
            model_cls = getattr(module, class_name)
        else:
            # Prendre la première classe trouvée
            candidates = [obj for obj in module.__dict__.values() if isinstance(obj, type)]
            if not candidates:
                raise RuntimeError(f"No class found in {main_py}")
            model_cls = candidates[0]
        
        return model_cls()
    
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def load_model_from_py(py_path: str, class_name: str):
    """Load atomic model from its .py"""
    import importlib.util
    
    py_path = Path(py_path).resolve()
    
    spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    model_cls = getattr(module, class_name)
    return model_cls()

def load_model(model_path: str, class_name: str = None):
    """Load model from .py or .amd"""
    path = Path(model_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    if path.suffix == ".amd":
        logger.info(f"Loading model from .amd: {model_path}")
        return load_model_from_amd(model_path, class_name)
    elif path.suffix == ".py":
        if not class_name:
            raise ValueError("--class-name is required for .py files")
        logger.info(f"Loading model from .py: {model_path} (class: {class_name})")
        return load_model_from_py(model_path, class_name)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

def main():
    parser = argparse.ArgumentParser(
        description="Execute the runner in charge of execution an atomic model simulator"
    )
    parser.add_argument(
        "--model-path",
        required=True,
        help="Model file path (.py or .amd)"
    )
    parser.add_argument(
        "--class-name",
        help="Classe name (required for .py, optional for .amd)"
    )
    parser.add_argument(
        "--bootstrap",
        default="localhost:9092",
        help="Kafka url (default: localhost:9092)"
    )
    parser.add_argument(
        "--in-topic",
        help="Input Topic (default: generate from the label)"
    )
    parser.add_argument(
        "--out-topic",
        default="ms4meOut",
        help="Output Topic (default: ms4meOut)"
    )
    parser.add_argument(
        "--label",
        required=True,
        help="Lable of the model (default: classe name)"
    )
    
    args = parser.parse_args()
    
    # Import
    try:
        from MS4MeKafkaWorker import MS4MeKafkaWorker
    except ImportError:
        logger.error("Impossible d'importer MS4MeKafkaWorker. Vérifiez votre installation.")
        sys.exit(1)
    
    # Model loading
    try:
        model = load_model(args.model_path, args.class_name)
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle: {e}")
        sys.exit(1)
    
    # label of the model (the class if is not passesd to the args)
    label = args.label or model.__class__.__name__
    
    # input topic definition
    in_topic = args.in_topic or f"ms4me{label}In"
    
    logger.info("=" * 60)
    logger.info(f"Lancement du worker pour {label}")
    logger.info(f"  Bootstrap: {args.bootstrap}")
    logger.info(f"  In topic: {in_topic}")
    logger.info(f"  Out topic: {args.out_topic}")
    logger.info("=" * 60)
    
    # Create and execute the worker
    worker = MS4MeKafkaWorker(
        label,
        aDEVS=model,
        bootstrap_servers=args.bootstrap
    )
    
    # stop in a clean mode
    def signal_handler(sig, frame):
        logger.info("\nArrêt du worker en cours...")
        worker.stop()
        worker.join(timeout=5.0)
        logger.info("Worker arrêté")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the worker
    worker.start()
    logger.info(f"Worker démarré (PID: {worker.ident})")
    
    # wait the work's end
    try:
        while worker.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interruption clavier détectée")
        worker.stop()
        worker.join(timeout=5.0)
    
    logger.info("Worker terminé")

if __name__ == "__main__":
    import builtins
    import os
    from pathlib import Path

    # Ajouter le répertoire racine du projet au PYTHONPATH
    # Le script est dans DEVSKernel/KafkaDEVS/MS4Me/
    # On remonte de 3 niveaux pour atteindre la racine devsimpy/
    script_dir = Path(__file__).parent.resolve()
    devskernel_path = script_dir.parents[1]
    project_root = script_dir.parents[2]  # Remonte de MS4Me -> KafkaDEVS -> DEVSKernel -> devsimpy

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"Added to PYTHONPATH: {project_root}")
    
    setattr(builtins, 'DEFAULT_SIM_STRATEGY', 'ms4Me')
    setattr(builtins, 'DEFAULT_DEVS_DIRNAME', 'KafkaDEVS')
    setattr(builtins, 'DEVS_SIM_KERNEL_PATH', devskernel_path)
    setattr(builtins, 'DEVS_DIR_PATH_DICT', {'KafkaDEVS': os.path.join(devskernel_path, 'KafkaDEVS')})
    main()
