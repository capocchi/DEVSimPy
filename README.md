<p align="center">
  <img width="460" height="300" src="https://github.com/capocchi/DEVSimPy/blob/version-4.0/splash/splash.png" alt="DEVSimPy">
</p>

# DEVSimPy: Python-Based GUI for DEVS Simulation
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![codecov](https://codecov.io/gh/capocchi/DEVSimPy/branch/master/graph/badge.svg)](https://codecov.io/gh/capocchi/DEVSimPy)
[![Maintainability](https://api.codeclimate.com/v1/badges/f5c94ecbfb6a3c8986be/maintainability)](https://codeclimate.com/github/capocchi/DEVSimPy/maintainability)
[![Coverage Status](https://coveralls.io/repos/github/capocchi/DEVSimPy/badge.svg?branch=master)](https://coveralls.io/github/capocchi/DEVSimPy?branch=master)

## What is DEVSimPy?
DEVSimPy is an open-source framework (GPL v3) designed for **modeling and simulating discrete event systems (DEVS)** with a graphical user interface. Developed in Python with [wxPython](http://www.wxpython.org), it simplifies interaction with **PyDEVS** and **PyPDEVS** models.

### Key Features 🚀
| Feature               | Description |
|----------------------|-------------|
| **Graphical Modeling** | Design, save, and export DEVS models easily. |
| **Simulation & Analysis** | Run, suspend, and analyze simulations in real-time. |
| **Code Editing** | Modify DEVS models on the fly. |
| **Model Libraries** | Import/export libraries for domain-specific applications. |
| **Command-Line Execution** | Run simulations via CLI with `devsimpy-nogui.py`. |
| **Plugin System** | Extend functionality with custom plugins. |
| **YAML Export** | Generate YAML models for [DEVSimPy-mob](https://github.com/capocchi/DEVSimPy_mob). |
| **REST API** | Enable remote simulation execution via [DEVSimPy-REST](https://github.com/capocchi/DEVSimPy_rest). |

---

## Installation
### Requirements
- **Python 3.10+**
- **wxPython 4.0+**
- **SciPy & NumPy** (for spectrum analysis, optional)

### Standard Installation
```sh
$ git clone --recurse-submodules -b version-4.0 --depth=1 https://github.com/capocchi/DEVSimPy.git
$ git fetch --unshallow
$ pip install -r requirements.txt
```

### Running DEVSimPy
```sh
$ python devsimpy.py
```
For macOS users:
```sh
$ pythonw devsimpy.py  # Required due to wxPython dependencies
```

### Alternative Installation Methods
- **Conda Environment**: Use the [`conda_devsimpy_env.yml`](https://github.com/capocchi/DEVSimPy-site/raw/gh-pages/conda_devsimpy_env.yml) file.
- **Portable Version**: Use [Portable Python](http://portablepython.com) with [PyScripter](https://sourceforge.net/projects/pyscripter/).
- **Virtual Machine**: Download a preconfigured **XUbuntu 19.10 VM** with DEVSimPy [here](https://mycore.core-cloud.net/index.php/s/2EHfgPwJk6HIEHH) (Login: `devsimpy-user/devsimpy`).

---

## Command-Line Usage
Execute DEVSimPy models without the GUI:
```sh
$ python devsimpy-nogui.py test.dsp -sim 10 -kernel pdevs
```
For PyDEVS kernel:
```sh
$ python devsimpy-nogui.py test.dsp -kernel PyDEVS 10
```
Check CLI options:
```sh
$ python devsimpy-nogui.py -h
```

---

## Documentation 📖
- **[DEVSimPy User Guide v2.8 (French)](http://portailweb.universita.corsica/stockage_public/portail/baaaaaes/files/DEVSimPy_guide_utilisateur.pdf)**
- **[S. Toma Ph.D. Thesis (English)](https://hal.archives-ouvertes.fr/tel-01141844/document)** *(Winner of the 2014 DEVS PhD Dissertation Award)*
- **[Technical Report (Polish)](http://portailweb.universita.corsica/stockage_public/portail/baaaaaes/files/report_Cezary.pdf)**

---

## Citing DEVSimPy 📌
If you use DEVSimPy in your research, cite it using:
```bibtex
@misc{capocchi2019devsimpy,
    author = {Laurent Capocchi},
    title = {DEVSimPy},
    year = {2019},
    publisher = {GitHub},
    journal = {GitHub repository},
    howpublished = {\url{https://github.com/capocchi/DEVSimPy}},
}
```
```bibtex
@INPROCEEDINGS{5990023,
    author={L. {Capocchi} and J. F. {Santucci} and B. {Poggi} and C. {Nicolai}},
    booktitle={2011 IEEE 20th International Workshops on Enabling Technologies: Infrastructure for Collaborative Enterprises},
    title={DEVSimPy: A Collaborative Python Software for Modeling and Simulation of DEVS Systems},
    year={2011},
    pages={170-175},
    doi={10.1109/WETICE.2011.31},
}
```

---

## Videos & Resources 🎥
- **[YouTube](https://www.youtube.com/results?search_query=devsimpy)**
- **[Personal Website](https://capocchi-l.universita.corsica/)**

For extensions, see **[this repository](https://github.com/jscott-thompson/DEVSimPy)**.

---

## Contributions & Feedback 💡
We welcome **contributions and feedback**! Feel free to submit issues, pull requests, or join discussions to help improve DEVSimPy. 🚀

