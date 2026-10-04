<p align="center">
  <img width="460" height="300" src="https://github.com/capocchi/DEVSimPy/blob/master/devsimpy/splash/splash.png" alt="DEVSimPy">
</p>

# DEVSimPy: Python-Based GUI for DEVS Simulation

| Category    | Status |
|------------|--------|
| **Builds & Tests**  | [![Linux](https://github.com/capocchi/DEVSimPy/actions/workflows/ci-build-ubuntu.yml/badge.svg)](https://github.com/capocchi/DEVSimPy/actions/workflows/ci-build-ubuntu.yml) [![Windows](https://github.com/capocchi/DEVSimPy/actions/workflows/ci-build-windows.yml/badge.svg)](https://github.com/capocchi/DEVSimPy/actions/workflows/ci-build-windows.yml) |
| **PyPI**   | [![PyPI Version](https://img.shields.io/pypi/v/devsimpy)](https://pypi.org/project/devsimpy/) [![Supported Versions](https://img.shields.io/pypi/pyversions/devsimpy?logo=python&logoColor=white)](https://pypi.org/project/devsimpy/) [![Supported Implementations](https://img.shields.io/pypi/implementation/devsimpy)](https://pypi.org/project/devsimpy/) [![Wheel](https://img.shields.io/pypi/wheel/devsimpy)](https://pypi.org/project/devsimpy/) |
| **Activity** | ![Last Commit](https://img.shields.io/github/last-commit/capocchi/devsimpy) [![Commits Since](https://img.shields.io/github/commits-since/capocchi/devsimpy/v5.1)](https://github.com/capocchi/devsimpy/commits) ![Maintained](https://img.shields.io/maintenance/yes/2025) [![PyPI Downloads](https://img.shields.io/pypi/dm/devsimpy)](https://pypi.org/project/devsimpy/) |
| **QA** | [![CodeFactor](https://img.shields.io/codefactor/grade/github/capocchi/devsimpy?logo=codefactor)](https://www.codefactor.io/repository/github/capocchi/devsimpy) [![Flake8 & mypy](https://github.com/capocchi/DEVSimPy/actions/workflows/lint.yml/badge.svg)](https://github.com/capocchi/DEVSimPy/actions/workflows/lint.yml) |
| **Other**  | [![License](https://img.shields.io/github/license/capocchi/devsimpy)](https://github.com/capocchi/DEVSimPy/blob/master/License) ![Language](https://img.shields.io/github/languages/top/capocchi/devsimpy) [![Requirements Status](https://dependency-dash.repo-helper.uk/github/capocchi/DEVSimPy/badge.svg)](https://dependency-dash.repo-helper.uk/github/capocchi/DEVSimPy) [![DOI](https://zenodo.org/badge/586533.svg)](https://doi.org/10.5281/zenodo.19336231) |


<!-- | **Docs**  | ![Docs](https://img.shields.io/readthedocs/domdf-wxpython-tools/latest?logo=read-the-docs) [![Docs Check](https://github.com/domdfcoding/domdf_wxpython_tools/workflows/Docs%20Check/badge.svg)](https://github.com/domdfcoding/domdf_wxpython_tools/actions?query=workflow%3A%22Docs+Check%22) | -->

## What is DEVSimPy?

> A Python-based GUI framework for designing, simulating, and analyzing **Discrete Event Systems (DEVS)** models.

**DEVSimPy** (Discrete Event System Simulation in Python) is a free, open-source framework (**GPL v3 license**) for **modeling, designing, and simulating discrete event systems (DEVS)** with an intuitive graphical user interface. Built in **Python** using **[wxPython](http://www.wxpython.org)**, DEVSimPy serves as the bridge between human-friendly visual modeling and powerful DEVS simulation engines like **PyDEVS** and **PyPDEVS**.

### What is DEVS?

**DEVS** (Discrete Event System Specification) is a formal framework for modeling complex systems where state changes occur at discrete time points. It's widely used in:

- **Healthcare**: Patient flow, hospital operations
- **Manufacturing**: Production lines, supply chains
- **Transportation**: Traffic networks, logistics
- **Computer Science**: Networks, distributed systems

### Why DEVSimPy Exists

Traditional DEVS tools have a steep learning curve, lack visual feedback, and offer limited accessibility. DEVSimPy changes this by:

- **Visual Modeling**: Transform abstract DEVS notation into intuitive graphical representations
- **Real-Time Analysis**: Monitor system behavior as simulations unfold
- **Interactive Workflow**: See immediate results of modeling choices
- **Python Power**: Leverage Python's simplicity while maintaining rigorous mathematical foundations


### Who Is It For?

- **Researchers** who need to compare multiple parameter configurations
- **Educators** teaching discrete event systems and system dynamics  
- **Engineers** modeling complex systems (healthcare, logistics, manufacturing)
- **Students** learning DEVS concepts through visual tools

### Key Features

| Feature | What It Enables |
|---------|-----------------|
| **Graphical Canvas** | Drag-and-drop design of DEVS models with real-time visualization |
| **Simulation Control** | Start, pause, resume simulations with speed adjustment |
| **Live Metrics Panel** | Watch system states, timers, and events during execution |
| **Model Export** | Generate YAML files for multi-agent extensions (DEVSimPy-mob) |
| **Plugin System** | Extend functionality with custom modules |
| **CLI Execution** | Run simulations via command line (`devsimpy-nogui.py`) |
| **AI Model Generation** | Auto-generate DEVS models from text descriptions |
| **Kafka Integration** | Connect to streaming frameworks for distributed simulation |
| **DEVS Standard Compliant** | Full OMG-DEVS compatibility for tool interoperability |

### Ecosystem & Extensions

DEVSimPy is part of a growing DEVS ecosystem:
- **[DEVSimPy-mob](https://github.com/capocchi/DEVSimPy_mob)** - Multi-agent extensions via YAML export
- **[DEVSimPy-rest](https://github.com/capocchi/DEVSimPy_rest)** - REST API for remote simulation execution
- **[Plugin System](./plugins/)** - Extend functionality with custom modules

### Installation Quick Start

#### From PyPI (Recommended for Users)
```sh
pip install devsimpy
devsimpy
```

#### From Source (For Developers)
```sh
git clone --recurse-submodules -b version-5.1 --depth=1 https://github.com/capocchi/DEVSimPy.git
git fetch --unshallow
pip install -r requirements.txt
python devsimpy.py
```

#### Alternative Installation Methods
- **Conda Environment**: Use the [`conda_devsimpy_env.yml`](https://github.com/capocchi/DEVSimPy-site/raw/gh-pages/conda_devsimpy_env.yml) file.
- **Portable Version**: Use [Portable Python](http://portablepython.com) with [PyScripter](https://sourceforge.net/projects/pyscripter/).
- **Virtual Machine**: Download a preconfigured **XUbuntu 19.10 VM** with DEVSimPy [here](https://mycore.core-cloud.net/index.php/s/2EHfgPwJk6HIEHH) (Login: `devsimpy-user/devsimpy`).

> **Note**: Python 3.10+ and wxPython 4.0+ are required for core functionality. SciPy & NumPy are optional for advanced spectrum analysis features.

### 🔧 Command-Line Usage (No GUI)

Execute DEVSimPy models without the GUI interface:

```sh
# Run with PyDEVS kernel
python devsimpy-nogui.py test.dsp -sim 10 -kernel pdevs

# Or use explicit kernel name
python devsimpy-nogui.py test.dsp -kernel PyDEVS 10

# For Python script entry point
python devsimpy.py --nogui test.dsp -sim 10 -kernel pdevs

# Check all options
python devsimpy-nogui.py -h
```

> **Tip**: Use `.dsp` files as input (DEVS model format). Replace `test.dsp` with your model filename.

## 📖 Documentation
- **[DEVSimPy User Guide v2.8 (French)](http://portailweb.universita.corsica/stockage_public/portail/baaaaaes/files/DEVSimPy_guide_utilisateur.pdf)**
- **[S. Toma Ph.D. Thesis (English)](https://hal.archives-ouvertes.fr/tel-01141844/document)** *(Winner of the 2014 DEVS PhD Dissertation Award)*
- **[Technical Report (Polish)](http://portailweb.universita.corsica/stockage_public/portail/baaaaaes/files/report_Cezary.pdf)**

---

## Citing DEVSimPy
If you use DEVSimPy in your research, cite it using:
```bibtex
@misc{capocchi2019devsimpy,
    author = {Laurent Capocchi},
    title = {DEVSimPy},
    year = {2019},
    publisher = {GitHub},
    journal = {GitHub repository},
    howpublished = {\url{https://github.com/capocchi/DEVSimPy}},
    doi={https://doi.org/10.5281/zenodo.19336231}
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

## Videos & Resources

- **[YouTube](https://www.youtube.com/results?search_query=devsimpy)** - Tutorials and demonstrations
- **[Personal Website](https://capocchi-l.universita.corsica/)** - Project information and news

**Extensions & Related Projects:**
- **[DEVSimPy-mob](https://github.com/capocchi/DEVSimPy_mob)** - Multi-agent extensions
- **[DEVSimPy-rest](https://github.com/capocchi/DEVSimPy_rest)** - REST API server
- **[Legacy Extensions](https://github.com/jscott-thompson/DEVSimPy)** - Community contributions

---

## Contributions & Feedback

We welcome **contributions and feedback**! Feel free to submit issues, pull requests, or join discussions to help improve DEVSimPy. 🚀

---

*Welcome to the DEVSimPy community!*

