<p align="center">
<img width="460" height="300" src="https://github.com/capocchi/DEVSimPy/blob/version-4.0/splash/splash.png" alt='DEVSimPy'>
</p>

[![Build Status](https://travis-ci.org/capocchi/DEVSimPy.svg?branch=master)](https://travis-ci.org/capocchi/DEVSimPy)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Coverage Status](https://coveralls.io/repos/github/capocchi/DEVSimPy/badge.svg?branch=master)](https://coveralls.io/github/capocchi/DEVSimPy?branch=master)
<a href="https://codeclimate.com/github/capocchi/DEVSimPy/maintainability"><img src="https://api.codeclimate.com/v1/badges/f5c94ecbfb6a3c8986be/maintainability" /></a>
<a href="https://codeclimate.com/github/capocchi/DEVSimPy/test_coverage"><img src="https://api.codeclimate.com/v1/badges/f5c94ecbfb6a3c8986be/test_coverage" /></a>

![Anurag's github stats](https://github-readme-stats.vercel.app/api?username=anuraghazra)

# What is DEVSimPy
DEVSimPy is an open Source project (under GPL V.3 license) supported by the [SPE](http://http://spe.univ-corse.fr/) (Sciences pour l'Environnement) team of the UMR CNRS 6134 Lab. of the [University of Corsica "Pasquale Paoli"](http://univ-corse.fr). This aim is to provide a GUI for the Modeling & Simulation of PyDEVS and [PyPDEVS](http://msdl.cs.mcgill.ca/projects/DEVS/PythonPDEVS) models. PyDEVS is an API allowing the implementation of the DEVS formalism in Python language. PyPDEVS is the parallel version of PyDEVS based on Parallel DEVS formalism which is an extension of the DEVS formalism. 
 The DEVSimPy environment has been developed in Python with the [wxPython](http://www.wxpython.org) graphical library without 
strong dependencies other than the [Scipy](http://www.scipy.org) and the [Numpy](http://www.numpy.org) scientific python libraries. The basic idea behind DEVSimPy is to wrap the PyDEVS API with a GUI allowing significant simplification of handling PyDEVS/PyPDEVS models (like the coupling between models or their storage into libraries).

# Requirements
The use of DEVSimPy requires:

- [Python](http://www.python.org) version 3.7+
- [wxPython](http://www.wxpython.org) version 4.0+
- [Scipy](http://www.scipy.org) and [Numpy](http://www.numpy.org) (optional, for spectrum analysis)
- DEVSimPy should be used like a normal Python file, i.e., double-clicking on the devsimpy.py file which is located in the root directory or writing python devismpy.py into a python console.

Users which don't want to install python with all dependencies can use [Portable Python](http://portablepython.com) (version 2.x). Then, just extract DEVSimPy archive and edit the devsimpy.py file with [PyScripter](https://sourceforge.net/projects/pyscripter/) to execute it. Users can also execute DEVSimPy through the conda env file loaded using the [conda_devsimpy_env.yml](https://github.com/capocchi/DEVSimPy-site/raw/gh-pages/conda_devsimpy_env.yml) file (available from the [DEVSimPy-site](https://github.com/capocchi/DEVSimPy-site) repository).

An XUbuntu 19.10 virtual machine including DEVSimPy can be donwloaded from [DEVSimPy-on-XUbuntu19.10.ova](https://mycore.core-cloud.net/index.php/s/o8T8mAzmuuHDokh). The login and password of the distribution (root) are: devsimpy-user/devsimpy. If you want to have the latest version of DEVSimPy, please execute 'git pull' in the DEVSimPy directory before starting or start DEVSimPy by double clicking on the desktop icon and go to Help->Update->From Git Repository (pull).

An archive of a conda environment which includes all the binaries of the packages needed for the DEVSimPy environment is available here: [py38.tar.gz](https://mycore.core-cloud.net/index.php/s/5nNgyvwps6O2kUy). This is useful when you want to reproduce a compatible environment for DEVSimPy and avoid all installation and dependencies requirement. 

# Features
With DEVSimPy you can:

- Model a DEVS system and save or export it into a library
- Edit the code of a DEVS model to modify behavior's (also during the simulation)
- Import existing library of models (python code or DEVSimPy specific models) which allows the specific domain modeling (Power system, continuous, etc)
- Automatically simulate the system and perform its analysis during the simulation (using the suspend option)
- Load plug-ins to extend DEVSimPy in order to perform activity tracking, trace the simulation with visual tools, etc.
- Generate YAML models for the [DEVSimPy-mob](https://github.com/capocchi/DEVSimPy_mob) mobile application.
- and more.

# Installation

To get DEVSimPy v4.0 package with all Git submodules: 
```sh
$ git clone --recurse-submodules -b version-4.0 --depth=1 https://github.com/capocchi/DEVSimPy.git
$ git fetch --unshallow 
```

DEVSimPy depends on PyPubSub, pyyaml, ruamel.yaml and other packages included in the requirements.txt file. 
All dependencies can be installed using pip with the requirements.txt file:
```sh
$ pip install -r requirements.txt
```
# Usage
To execute DEVSimPy:
```sh
$ python devsimpy.py
```

For os X users, python.app is required in order to use pythonw instead of python to execute the devismpy.py file:
```sh
$ pythonw devsimpy.py
```
# Documentations
 - DEVSimPy User Guide v2.8 [[pdf]](http://portailweb.universita.corsica/stockage_public/portail/baaaaaes/files/DEVSimPy_guide_utilisateur.pdf) (French)
 - S. Toma Ph.D, Thesis [[pdf]](https://hal.archives-ouvertes.fr/tel-01141844/document) (English), winner of the 2014 DEVS PhD Dissertation Award.
 - S. Cezary, "Design and implementation of application for instruction exercises with DEVSimPy", Technical report, Faculty of Electrical Engineering, AUTOMATION AND INFORMATION TECHNOLOGY, Kielce University of Technology [[pdf]](http://portailweb.universita.corsica/stockage_public/portail/baaaaaes/files/report_Cezary.pdf) (Polish)

# Citing

Some papers concerning DEVSimPy:
- L. Capocchi, J.F. Santucci, B.P. Zeigler, MS4Me and DEVSimPy, demo à JDF 2016 - Les Journées DEVS Francophones - Théorie et Applications, 11-15 Avril, 2016, ISBN 9782364935396, Cargese, France.
- L. Capocchi, J.F. Santucci, DEVSimPy : Interface graphique développée en langage Python et la librairie wxPython, Jounrées Développement Logiciel de l'Enseignement Supérieur et de la Recherche (JDEVS 2015), 30 juin -3 juillet, 2015, Bordeaux INP - ENSEIRB-MATMECA.
- S. Sehili, L. Capocchi, J.F. Santucci, S. Lavirotte, J.Y. Tigli, "Discrete Event Modeling and Simulation for IoT Efficient Design Combining WComp and DEVSimPy Framework", in Proc. of 5th International Conference on Simulation and Modeling Methodologies, Technologies and Applications (SIMULTECH), July 21-23, 2015, ISBN 978-989-758-120-5, Colmar, Alsace, France, pp. 44-52.
- T. Ville, L. Capocchi, J. F. Santucci, "DEVS models design and test using AGILE-based methods with DEVSimPy", in Proc. of the 26th European Modeling and Simulation Symposium (Simulation in Industry) (EMSS), Sept. 10-12, 2014, Agora Multi-Purpose Complex, University of Bordeaux, Bordeaux (France), ISBN 978-88-979999-44-7, pp. 563-569.
- L. Capocchi, J. F. Santucci, T. Ville, "Software test automation using DEVSimPy environment", in Proc. of the ACM SIGSIM conference on Principles of advanced discrete simulation (PADS), May 5-8, 2013, Montreal (Canada), ISBN 978-1-4503-1920-1, pp. 343-348.
- L. Capocchi, J. F. Santucci, "Discrete Optimization via Simulation of Catchment Basin Management Within the DEVSimPy Framework", in Proc. of the IEEE/ACM Wintersim Conference (WSC) , Dec. 7-10, 2013, Marriot Hotel, Washington DC, ISBN 978-1-4799-2077-8, pp. 205-216. (CORE B)
- J. F. Santucci, L. Capocchi, "Implementation and Analysis of DEVS Activity-Tracking with DEVSimPy", in Proc. of ACTIMS ITM Web of Conferences , 2013, DOI: 10.1051/itmconf/20130101001, ISBN 978-2-7598-1108-3, 9 pages.
- J. F. Santucci, L. Capocchi, "Catchment Basin Optimized Management using a Simulation Approach within DEVSimPy Framework", in Proc. of the Summer Simulation Multiconference , June 8-11, 2012, Genova (Italie), ISBN 978-1-61839-984-7, pp. 28-36. (CORE B)
- J.F. Santucci, L. Capocchi, A Proposed Evolution of DEVSimPy Environment Towards Activity Tracking, Cargese Activity-based Modeling and Simulation (Cargese - ACTIMS'2012), 5 pages, Cargese (Corse), May 28 - 1 June 2012.
- L. Capocchi, J.F. Santucci DEVSimPy : un environnement Python de simulation des systèmes à événements discrets, PHPSolutions, Decembre 2011.
- L. Capocchi, J. F. Santucci, B. Poggi, C. Nicolai, "DEVSimPy: A Collaborative Python Software for Modeling and Simulation of DEVS Systems", in Proc. of the 20th IEEE International Conference on Collaboration Technologies and Infrastructures, June 27-29, 2011, Paris (France), ISBN 978-1-4577-0134-4, pp. 170-175. (CORE B)

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
- You can watch some DEVSimPy features videos on [Youtube](https://www.youtube.com/results?search_query=devsimpy)
