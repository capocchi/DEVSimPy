from ApplicationController import TestApp
from CheckerGUI import CheckerGUI
import time

# Données de test (adaptées à votre structure)
test_data = {
    1: ("Model1", "SyntaxError: invalid syntax", "15", ["author1@univ-corse.fr"], "/path/to/model1.py"),
    2: ("Model2", "NameError: name 'x' is not defined", "23", ["author2@univ-corse.fr"], "/path/to/model2.py"),
    3: ("Model3", "", "", [], "/path/to/model3.py"),
}

# Lancer l'application de test
app = TestApp(0)
frame = CheckerGUI(None, "CheckerGUI Test", test_data)
app.RunTest(frame)
