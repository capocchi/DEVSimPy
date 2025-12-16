import subprocess
import sys
from pathlib import Path

# Répertoire du script : .../devsimpy/DEVSKernel/KafkaDEVS/tests
here = Path(__file__).resolve().parent
# Racine du projet devsimpy : deux niveaux au-dessus
project_root = here.parents[2]  # .../devsimpy
sys.path.insert(0, str(project_root))

# Adapter l'import au chemin réel de ton package
from DEVSKernel.KafkaDEVS.auto_kafka import ensure_kafka_broker

def main():
    print("=== Test ensure_kafka_broker ===")

    try:
        bootstrap = ensure_kafka_broker()
        print(f"Broker Kafka prêt sur {bootstrap}")
    except Exception as e:
        print("ERREUR : le broker Kafka n'a pas pu être initialisé / atteint.")
        print(f"Type  : {type(e)}")
        print(f"Valeur: {e}")
        sys.exit(1)

    print("=== Lancement de la simulation DEVSimPy (test.dsp, T=10) ===")

    # dossier du script: .../devsimpy/DEVSKernel/KafkaDEVS/tests
    here = Path(__file__).resolve().parent

    # racine devsimpy (qui contient devsimpy-nogui.py)
    devsimpy_root = here.parents[2]

    devsimpy_nogui = devsimpy_root / "devsimpy-nogui.py"
    test_dsp = "test.dsp"

    cmd = [
        sys.executable,
        str(devsimpy_nogui),
        "-with_progress",
        "-kernel", "KafkaDEVS",
        str(test_dsp),
        "10",
    ]

    print("Commande :", " ".join(cmd))
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
