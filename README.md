# What is DEVSimPy
DEVSimPy is an open Source project (under GPL V.3 license) supported by the [SPE](http://http://spe.univ-corse.fr/) (Sciences pour l'Environnement) team of the UMR CNRS 6134 Lab. of the [University of Corsica "Pasquale Paoli"](http://univ-corse.fr). This aim is to provide a GUI for the Modeling & Simulation of PyDEVS and [PyPDEVS](http://msdl.cs.mcgill.ca/projects/DEVS/PythonPDEVS) models. PyDEVS is an API allowing the implementation of the DEVS formalism in Python language. PyPDEVS is the parallel version of PyDEVS based on Parallel DEVS formalism which is an extension of the DEVS formalism. 
 The DEVSimPy environment has been developed in Python with the [wxPython](http://www.wxpython.org) graphical library without 
strong dependencies other than the [Scipy](http://www.scipy.org) and the [Numpy](http://www.numpy.org) scientific python libraries. The basic idea behind DEVSimPy is to wrap the PyDEVS API with a GUI allowing 
significant simplification of handling PyDEVS/PyPDEVS models (like the coupling between models or their storage into libraries).

# Requirements
The use of DEVSimPy requires:

- [Python](http://www.python.org) version 2.4+
- [wxPython](http://www.wxpython.org) version 2.6+ ansi/unicode (unicode recommended)
- [Scipy](http://www.scipy.org) and [Numpy](http://www.numpy.org) (optional, for spectrum analysis)
- DEVSimPy should be used like a normal Python file, i.e., double-clicking on the devsimpy.py file which is located in the root directory or writing python devismpy.py into a python console.

Users which don't want to install python with all dependency can use [Portable Python](http://portablepython.com) (version 2.x). Then, just extract DEVSimPy archive and edit the devsimpy.py file with [PyScripter](https://sourceforge.net/projects/pyscripter/) to execute it. Users can also execute DEVSimPy through the conda env file loaded using the [conda_devsimpy_env.yml](https://github.com/capocchi/DEVSimPy-site/raw/gh-pages/conda_devsimpy_env.yml) file (available from the [DEVSimPy-site](https://github.com/capocchi/DEVSimPy-site) repository).

# Features
With DEVSimPy we can:

- Model a DEVS system and save or export it into a library
- Edit the code of DEVS model to modify behavior's also during the simulation
- Import existing library of models (python code or DEVSimPy specific models) which allows the specific domain modeling (Power system, continuous, etc)
- Automatically simulate the system and perform its analysis during the simulation (with the suspend option)
- Load plug-ins to extend DEVSimPy in order to perform activity tracking, trace the simulation with visual tools, etc.
- Generate YAML models for the DEVSimPy-mob mobile application.
- and more.

#Installation
DEVSimPy don't require installation and works on all platforms. To launch DEVSimPy, you need to execute the devsimpy.py file into a Python prompt:
```sh
$ python devsimpy.py
```

# Documentations
 - DEVSimPy User Guide v2.8 [[pdf]](http://lcapocchi.free.fr/devsimpy/Guide_utilisateur_v2.8.pdf) (French)
 - S. Toma Ph.D, Thesis [[pdf]](https://hal.archives-ouvertes.fr/tel-01141844/document) (English), winner of the 2014 DEVS PhD Dissertation Award.
 - S. Cezary, "Design and implementation of application for instruction exercises with DEVSimPy", Technical report, Faculty of Electrical Engineering, AUTOMATION AND INFORMATION TECHNOLOGY, Kielce University of Technology [[pdf]](http://lcapocchi.free.fr/files/report_Cezary.pdf) (Polish)
 - L. Capocchi, J. F. Santucci, B. Poggi, C. Nicolai, "DEVSimPy: A Collaborative Python Software for Modeling and Simulation of DEVS Systems", in Proc. of the 20th IEEE International Conference on Collaboration Technologies and Infrastructures, June 27-29, 2011, Paris (France), ISBN 978-1-4577-0134-4, pp. 170-175

# Videos
- [Youtube] (https://www.youtube.com/results?search_query=devsimpy)
