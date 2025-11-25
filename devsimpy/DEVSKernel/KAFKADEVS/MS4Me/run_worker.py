#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour lancer un worker Kafka DEVS à partir du chemin d'un modèle atomique.
Usage: python run_worker.py --model-path <path> --index <int> [options]
Exemple à éxécuter dans une console avant test_worker_messages:
Attention, index ne sert pas à créer le topic mais il est obligatoire dans la classe MS4MeKafkaWorker 
python run_worker.py --model-path ..\..\..\Domain\Collector\MessagesCollector.py --class-name MessagesCollector --index 0 --bootstrap localhost:9092
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
    """Charge un modèle atomique depuis un fichier .amd (zip)"""
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
    """Charge un modèle atomique depuis un fichier .py"""
    import importlib.util
    
    py_path = Path(py_path).resolve()
    
    spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    model_cls = getattr(module, class_name)
    return model_cls()


def load_model(model_path: str, class_name: str = None):
    """Charge un modèle depuis .py ou .amd"""
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


# def create_mock_block_model(label: str):
#     """Crée un objet mock pour getBlockModel()"""
#     class MockBlockModel:
#         def __init__(self, label):
#             self.label = label
#     return MockBlockModel(label)


def main():
    parser = argparse.ArgumentParser(
        description="Lance un worker Kafka DEVS pour un modèle atomique"
    )
    parser.add_argument(
        "--model-path",
        required=True,
        help="Chemin vers le fichier du modèle (.py ou .amd)"
    )
    parser.add_argument(
        "--class-name",
        help="Nom de la classe du modèle (requis pour .py, optionnel pour .amd)"
    )
    parser.add_argument(
        "--index",
        type=int,
        required=True,
        help="Index du modèle atomique dans la simulation"
    )
    parser.add_argument(
        "--bootstrap",
        default="localhost:9092",
        help="Adresse du serveur Kafka (défaut: localhost:9092)"
    )
    parser.add_argument(
        "--in-topic",
        help="Topic d'entrée (par défaut: généré depuis le label)"
    )
    parser.add_argument(
        "--out-topic",
        default="ms4meOut",
        help="Topic de sortie (défaut: ms4meOut)"
    )
    parser.add_argument(
        "--label",
        help="Label du modèle (par défaut: nom de la classe)"
    )
    
    args = parser.parse_args()
    
    # Import des classes nécessaires
    try:
        from MS4MeKafkaWorker import MS4MeKafkaWorker
    except ImportError:
        logger.error("Impossible d'importer MS4MeKafkaWorker. Vérifiez votre installation.")
        sys.exit(1)
    
    # Charger le modèle
    try:
        model = load_model(args.model_path, args.class_name)
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle: {e}")
        sys.exit(1)
    
    # Déterminer le label
    label = args.label or model.__class__.__name__
    
    # Ajouter le mock getBlockModel
    # model.getBlockModel = lambda: create_mock_block_model(label)
    
    # Déterminer le topic d'entrée
    in_topic = args.in_topic or f"ms4me{label}_{args.index}In"
    
    logger.info("=" * 60)
    logger.info(f"Lancement du worker pour {label}")
    logger.info(f"  Index: {args.index}")
    logger.info(f"  Bootstrap: {args.bootstrap}")
    logger.info(f"  In topic: {in_topic}")
    logger.info(f"  Out topic: {args.out_topic}")
    logger.info("=" * 60)
    
    # Créer et lancer le worker
    worker = MS4MeKafkaWorker(
        label,
        aDEVS=model,
        index=args.index,
        bootstrap_servers=args.bootstrap
    )
    
    # Gestion du signal pour arrêt propre
    def signal_handler(sig, frame):
        logger.info("\nArrêt du worker en cours...")
        worker.stop()
        worker.join(timeout=5.0)
        logger.info("Worker arrêté")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Démarrer le worker
    worker.start()
    logger.info(f"Worker démarré (PID: {worker.ident})")
    
    # Attendre que le worker se termine
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
