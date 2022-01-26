<p align="center">
<img width="460" height="300" src="https://github.com/capocchi/DEVSimPy/blob/version-4.0/splash/splash.png" alt='DEVSimPy'>
</p>

[![Build Status](https://travis-ci.org/capocchi/DEVSimPy.svg?branch=master)](https://travis-ci.org/capocchi/DEVSimPy)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Coverage Status](https://coveralls.io/repos/github/capocchi/DEVSimPy/badge.svg?branch=master)](https://coveralls.io/github/capocchi/DEVSimPy?branch=master)
<a href="https://codeclimate.com/github/capocchi/DEVSimPy/maintainability"><img src="https://api.codeclimate.com/v1/badges/f5c94ecbfb6a3c8986be/maintainability" /></a>
<a href="https://codeclimate.com/github/capocchi/DEVSimPy/test_coverage"><img src="https://api.codeclimate.com/v1/badges/f5c94ecbfb6a3c8986be/test_coverage" /></a>

# What is DEVSimPy
DEVSimPy is an open Source project (under GPL V.3 license) supported by the [SPE](http://http://spe.univ-corse.fr/) (Sciences pour l'Environnement) team of the UMR CNRS 6134 Lab. of the [University of Corsica "Pasquale Paoli"](http://univ-corse.fr). This aim is to provide a GUI for the Modeling & Simulation of PyDEVS and [PyPDEVS](http://msdl.cs.mcgill.ca/projects/DEVS/PythonPDEVS) models. PyDEVS is an API allowing the implementation of the DEVS formalism in Python language. PyPDEVS is the parallel version of PyDEVS based on Parallel DEVS formalism which is an extension of the DEVS formalism.
 The DEVSimPy environment has been developed in Python with the [wxPython](http://www.wxpython.org) graphical library without
strong dependencies other than the [Scipy](http://www.scipy.org) and the [Numpy](http://www.numpy.org) scientific python libraries. The basic idea behind DEVSimPy is to wrap the PyDEVS API with a GUI allowing significant simplification of handling PyDEVS/PyPDEVS models (like the coupling between models or their storage into libraries).

# Requirements
The use of DEVSimPy requires:

- [Docker](https://www.docker.com/) version 4.3.2+
- [Xquartz](https://www.xquartz.org/) version 2.8.1+

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

Download, install and run Xquartz
 1. Go to https://www.xquartz.org/
 2. Download and run the DMG
 3. You may be asked to logout or reboot
 4. Open XQuartz
 5. Launch XQuartz. Under the XQuartz menu, select Preferences
 6. Go to the security tab and ensure "Allow connections from network clients" is checked.
 7. Restart XQuartz.
 8. To verify XQuartz is running correctly, run
    ```netstat -an | grep -F 6000```

    You should see output that looks like this
    ```
    tcp4       0      0  *.6000                 *.*                    LISTEN
    tcp6       0      0  *.6000                 *.*                    LISTEN
    ```

To get DEVSimPy with all Git submodules:
```sh
git clone --recurse-submodules https://github.com/luminositylab/DEVSimPy.git

# This can take up to 20 minutes
docker-compose build --pull --no-cache
```
Next we're going to allow X11 (powered by Xquartz) to talk to docker and docker to talk to our host

```sh
xhost +localhost
```

Now that we've allowed local communication, lets verify xhost allows you to connect

```sh
xauth list
```

Your output should look something like this
```
localhost:0  MIT-MAGIC-COOKIE-1 someSha
```

# Usage
To execute DEVSimPy:
```sh
docker-compose up
```

# Documentations
 - DEVSimPy User Guide v2.8 [[pdf]](http://portailweb.universita.corsica/stockage_public/portail/baaaaaes/files/DEVSimPy_guide_utilisateur.pdf) (French)
 - S. Toma Ph.D, Thesis [[pdf]](https://hal.archives-ouvertes.fr/tel-01141844/document) (English), winner of the 2014 DEVS PhD Dissertation Award.
 - S. Cezary, "Design and implementation of application for instruction exercises with DEVSimPy", Technical report, Faculty of Electrical Engineering, AUTOMATION AND INFORMATION TECHNOLOGY, Kielce University of Technology [[pdf]](http://portailweb.universita.corsica/stockage_public/portail/baaaaaes/files/report_Cezary.pdf) (Polish)

# Videos
You can watch some DEVSimPy features videos on
- [Youtube](https://www.youtube.com/results?search_query=devsimpy)
- [Personnal site](https://capocchi-l.universita.corsica/article.php?id_art=3261&id_rub=647&id_menu=0&id_cat=0&id_site=58&lang=en)
