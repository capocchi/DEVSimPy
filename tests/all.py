""" Launch tests of all test_ files.
    Usage: python all.py
""" 

import subprocess
import sys
import os
import glob

# Déterminer le chemin du dossier "tests"
script_dir = os.path.dirname(os.path.abspath(__file__))  # Répertoire du script en cours
tests_dir = os.path.join(os.path.dirname(script_dir), 'tests')  # Dossier tests/

# Trouver tous les fichiers Python commençant par "test_"
test_files = glob.glob(os.path.join(tests_dir, 'test_*.py'))

# Arguments à passer aux tests (ou '--autoclose' par défaut)
args = sys.argv[1:] or ['--autoclose']

# Exécuter chaque fichier de test
for test_file in test_files:
    print(f"{test_file} testing...")
    subprocess.call(['python', test_file] + args)

print("All tests executed")