<p align="center">
  <img width="460" height="300" src="https://github.com/capocchi/DEVSimPy/blob/version-5.0/devsimpy/splash/splash.png" alt="DEVSimPy">
</p>

# DEVSimPy: Python-Based GUI for DEVS Simulation
## Status

| Category  | Status |
|-----------|--------|
| **Tests** | [![Linux](https://github.com/capocchi/DEVSimPy/actions/workflows/ci-build-ubuntu.yml/badge.svg)](https://github.com/capocchi/DEVSimPy/actions/workflows/ci-build-ubuntu.yml) [![Windows](https://github.com/capocchi/DEVSimPy/actions/workflows/ci-build-windows.yml/badge.svg)](https://github.com/capocchi/DEVSimPy/actions/workflows/ci-build-windows.yml) |
| **PyPI**  | [![PyPI Version](https://img.shields.io/pypi/v/devsimpy)](https://pypi.org/project/devsimpy/) [![Supported Versions](https://img.shields.io/pypi/pyversions/devsimpy?logo=python&logoColor=white)](https://pypi.org/project/devsimpy/) [![Supported Implementations](https://img.shields.io/pypi/implementation/devsimpy)](https://pypi.org/project/devsimpy/) [![Wheel](https://img.shields.io/pypi/wheel/devsimpy)](https://pypi.org/project/devsimpy/) |
| **Activity** | ![Last Commit](https://img.shields.io/github/last-commit/capocchi/devsimpy) [![Commits Since](https://img.shields.io/github/commits-since/capocchi/devsimpy/v5.1)](https://github.com/capocchi/devsimpy/pulse) ![Maintained](https://img.shields.io/maintenance/yes/2025) [![PyPI Downloads](https://img.shields.io/pypi/dm/devsimpy)](https://pypi.org/project/devsimpy/) |
| **QA** | [![CodeFactor](https://img.shields.io/codefactor/grade/github/capocchi/devsimpy?logo=codefactor)](https://www.codefactor.io/repository/github/capocchi/devsimpy) [![Flake8](https://github.com/domdfcoding/domdf_wxpython_tools/workflows/Flake8/badge.svg)](https://github.com/domdfcoding/domdf_wxpython_tools/actions?query=workflow%3A%22Flake8%22) [![mypy](https://github.com/domdfcoding/domdf_wxpython_tools/workflows/mypy/badge.svg)](https://github.com/domdfcoding/domdf_wxpython_tools/actions?query=workflow%3A%22mypy%22) [![codecov](https://codecov.io/gh/capocchi/DEVSimPy/branch/master/graph/badge.svg)](https://codecov.io/gh/capocchi/DEVSimPy) |
| **Other** | [![License](https://img.shields.io/github/license/capocchi/devsimpy)](https://github.com/capocchi/devsimpy/blob/master/LICENSE) ![Language](https://img.shields.io/github/languages/top/capocchi/devsimpy) [![Requirements](https://dependency-dash.repo-helper.uk/github/capocchi/devsimpy/badge.svg)](https://dependency-dash.repo-helper.uk/github/capocchi/devsimpy/) |

<!-- | **Docs**  | ![Docs](https://img.shields.io/readthedocs/domdf-wxpython-tools/latest?logo=read-the-docs) [![Docs Check](https://github.com/domdfcoding/domdf_wxpython_tools/workflows/Docs%20Check/badge.svg)](https://github.com/domdfcoding/domdf_wxpython_tools/actions?query=workflow%3A%22Docs+Check%22) | -->



<!-- [![codecov](https://codecov.io/gh/capocchi/DEVSimPy/branch/master/graph/badge.svg)](https://codecov.io/gh/capocchi/DEVSimPy) -->
<!-- [![Maintainability](https://api.codeclimate.com/v1/badges/f5c94ecbfb6a3c8986be/maintainability)](https://codeclimate.com/github/capocchi/DEVSimPy/maintainability) -->
<!-- [![Coverage Status](https://coveralls.io/repos/github/capocchi/DEVSimPy/badge.svg?branch=master)](https://coveralls.io/github/capocchi/DEVSimPy?branch=master) -->

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

