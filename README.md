<p align="center">
<img width="460" height="300" src="https://github.com/capocchi/DEVSimPy/blob/version-4.0/splash/splash.png" alt='DEVSimPy'>
</p>

[![Build Status](https://travis-ci.org/capocchi/DEVSimPy.svg?branch=master)](https://travis-ci.org/capocchi/DEVSimPy)


# What is DEVSimPy
<p align="justify">
DEVSimPy is an open Source project (under GPL V.3 license) supported by the [SPE](http://http://spe.univ-corse.fr/) (Sciences pour l'Environnement) team of the UMR CNRS 6134 Lab. of the [University of Corsica "Pasquale Paoli"](http://univ-corse.fr). This aim is to provide a GUI for the Modeling & Simulation of PyDEVS and [PyPDEVS](http://msdl.cs.mcgill.ca/projects/DEVS/PythonPDEVS) models. PyDEVS is an API allowing the implementation of the DEVS formalism in Python language. PyPDEVS is the parallel version of PyDEVS based on Parallel DEVS formalism which is an extension of the DEVS formalism. 
 The DEVSimPy environment has been developed in Python with the [wxPython](http://www.wxpython.org) graphical library without 
strong dependencies other than the [Scipy](http://www.scipy.org) and the [Numpy](http://www.numpy.org) scientific python libraries. The basic idea behind DEVSimPy is to wrap the PyDEVS API with a GUI allowing 
significant simplification of handling PyDEVS/PyPDEVS models (like the coupling between models or their storage into libraries).
</p>

# Requirements
The use of DEVSimPy requires:

- [Python](http://www.python.org) version 3.7+
- [wxPython](http://www.wxpython.org) version 4.0+
- [Scipy](http://www.scipy.org) and [Numpy](http://www.numpy.org) (optional, for spectrum analysis)
- DEVSimPy should be used like a normal Python file, i.e., double-clicking on the devsimpy.py file which is located in the root directory or writing python devismpy.py into a python console.

Users which don't want to install python with all dependency can use [Portable Python](http://portablepython.com) (version 2.x). Then, just extract DEVSimPy archive and edit the devsimpy.py file with [PyScripter](https://sourceforge.net/projects/pyscripter/) to execute it. Users can also execute DEVSimPy through the conda env file loaded using the [conda_devsimpy_env.yml](https://github.com/capocchi/DEVSimPy-site/raw/gh-pages/conda_devsimpy_env.yml) file (available from the [DEVSimPy-site](https://github.com/capocchi/DEVSimPy-site) repository).

# Features
With DEVSimPy you can:

- Model a DEVS system and save or export it into a library
- Edit the code of DEVS model to modify behavior's also during the simulation
- Import existing library of models (python code or DEVSimPy specific models) which allows the specific domain modeling (Power system, continuous, etc)
- Automatically simulate the system and perform its analysis during the simulation (with the suspend option)
- Load plug-ins to extend DEVSimPy in order to perform activity tracking, trace the simulation with visual tools, etc.
- Generate YAML models for the DEVSimPy-mob mobile application.
- and more.

# Installation

To get DEVSimPy V4.0 package with all Git submodule: 
```sh
$ git clone --recurse-submodules -b version-4.0 --depth=1 https://github.com/capocchi/DEVSimPy.git .
$ git fetch --unshallow 
```

DEVSimPy depends on PyPubSub version 3.3.0 (or 3.3.1), pyyaml, ruamel.yaml and modules. 
All dependencies can be installed using requirements.txt file:
```sh
$ pip install -r requirements.txt
```

DEVSimPy don't require installation and works on all platforms (). To execute DEVSimPy:
```sh
$ python devsimpy.py
```

# Documentations
 - DEVSimPy User Guide v2.8 [[pdf]](http://lcapocchi.free.fr/devsimpy/Guide_utilisateur_v2.8.pdf) (French)
 - S. Toma Ph.D, Thesis [[pdf]](https://hal.archives-ouvertes.fr/tel-01141844/document) (English), winner of the 2014 DEVS PhD Dissertation Award.
 - S. Cezary, "Design and implementation of application for instruction exercises with DEVSimPy", Technical report, Faculty of Electrical Engineering, AUTOMATION AND INFORMATION TECHNOLOGY, Kielce University of Technology [[pdf]](http://lcapocchi.free.fr/files/report_Cezary.pdf) (Polish)

# Citing
 If you use DEVSimPy in your research, you can cite it with using the following bibtex references:
 ```
@misc{capocchi2019devsimpy,
    author = {Laurent Capocchi},
    title = {DEVSimPy},
    year = {2019},
    publisher = {GitHub},
    journal = {GitHub repository},
    howpublished = {\url{https://github.com/capocchi/DEVSimPy}},
}

@INPROCEEDINGS{5990023,
author={L. {Capocchi} and J. F. {Santucci} and B. {Poggi} and C. {Nicolai}},
booktitle={2011 IEEE 20th International Workshops on Enabling Technologies: Infrastructure for Collaborative Enterprises},
title={DEVSimPy: A Collaborative Python Software for Modeling and Simulation of DEVS Systems},
year={2011},
volume={},
number={},
pages={170-175},
keywords={discrete event simulation;large-scale systems;modelling;simulation;collaborative python software;DEVS systems;complex systems;collaborative M&S software;hydraulic network management;modeling and simulation;Object oriented modeling;Mathematical model;Libraries;Computational modeling;Collaboration;Data models;Predictive models;Modeling;Simulation;Collaborative software;Discrete event systems;Hydraulic systems;Software libraries},
doi={10.1109/WETICE.2011.31},
ISSN={},
month={June},}
```

# Videos
- [Youtube] (https://www.youtube.com/results?search_query=devsimpy)
