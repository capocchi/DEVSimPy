# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository overview

DEVSimPy is a wxPython-based GUI environment for modeling and simulating DEVS (Discrete Event System Specification) models. The codebase provides:

- A desktop GUI application for interactive DEVS modeling and simulation.
- A non-GUI/batch mode for running simulations from `.dsp` model files.
- Multiple DEVS simulation kernels (PyDEVS, PyPDEVS, KafkaDEVS) and domain-specific model libraries.
- A plugin and AI-assisted system for extending the environment and interacting with models.

Key user-facing entrypoints (from the repo):

- GUI: `python devsimpy/devsimpy.py`
- No-GUI: `python devsimpy/devsimpy-nogui.py`
- Installed CLI (from PyPI): `devsimpy` (configurable to run with or without GUI).

## Setup & installation

From the README:

- Install from PyPI (system-wide or in a virtualenv):
  - `pip install devsimpy`
  - Then launch: `devsimpy`
- Develop from this repo (typical workflow):
  - `git clone --recurse-submodules -b version-5.1 --depth=1 https://github.com/capocchi/DEVSimPy.git`
  - `git fetch --unshallow` (optional, for full history)
  - `pip install -r requirements.txt`
  - Run the GUI from the repo root:
    - `python devsimpy/devsimpy.py`
    - On macOS, wxPython may require: `pythonw devsimpy/devsimpy.py`

The project targets Python 3.9+ (with CI and README focusing on Python 3.10+ and wxPython ≥ 4.2.2).

## Common commands

### Run the GUI application

From the repository root:

- Launch the main GUI (dev mode):
  - `python devsimpy/devsimpy.py`
- Launch the main GUI using the installed console script (after `pip install devsimpy`):
  - `devsimpy`

The GUI can also be started with model and runtime arguments (used in CI on Linux):

- `xvfb-run -a python devsimpy/devsimpy.py examples/model0/model0.dsp 10 autostart autoclose`

### Run simulations without GUI (batch mode)

From the README and `SimulationNoGUI`:

- Use the no-GUI entrypoint script:
  - `python devsimpy/devsimpy-nogui.py path/to/model.dsp -sim 10 -kernel pdevs`
- Using the GUI script with `--nogui` (equivalent behavior):
  - `python devsimpy/devsimpy.py --nogui path/to/model.dsp -sim 10 -kernel pdevs`
- For PyDEVS kernel:
  - `python devsimpy/devsimpy-nogui.py path/to/model.dsp -kernel PyDEVS 10`
- Inspect CLI options:
  - `python devsimpy/devsimpy-nogui.py -h`

On Windows CI, the installed CLI is exercised in no-GUI mode as:

- `devsimpy --nogui examples/model0/model0.dsp 10`

### Tests

Tests are GUI-heavy and live in `tests/`. They are designed to be run as plain Python scripts (often with `--autoclose` to avoid hanging windows), and CI runs them under a virtual X server on Linux and directly on Windows.

#### Run the full test suite from the helper script

From the repo root:

- `python tests/all.py`

This script:

- Discovers all `tests/test_*.py` files.
- Invokes each test file as `python test_*.py --autoclose` by default (you can pass your own extra args).

#### Run a single test file

From the repo root:

- `cd tests`
- Example (Linux/macOS, with a real display):
  - `python test_checkergui.py --autoclose`
- Example (Linux without a display, following CI style):
  - `xvfb-run -a python test_checkergui.py --autoclose`
- Example (Windows, similar to CI):
  - `python test_checkergui.py --autoclose --nogui`

Most tests exercise wxPython dialogs/frames; they require wxPython and related GUI dependencies installed (see `requirements.txt` and CI workflows).

### Linting and type checking

From `.github/workflows/lint.yml`:

- Install tools:
  - `python -m pip install --upgrade pip`
  - `pip install flake8 mypy`
- Run Flake8 on the whole repo:
  - `flake8 .`
- Run mypy static type checking:
  - `mypy .`

These are the commands used in CI and should be preferred for local quality checks.

### Building / packaging

Packaging is configured via `pyproject.toml` with `setuptools` as the build backend and a console script entrypoint:

- Build backend:
  - `[build-system]` uses `setuptools.build_meta` with `setuptools` and `wheel`.
- Console script:
  - `[project.scripts]` declares `devsimpy = "devsimpy.devsimpy:main"`.

Typical packaging workflow (if you need wheels/sdist from this repo):

- Install the standard PEP 517 build tool:
  - `pip install build`
- Build distributions from the repo root:
  - `python -m build`

This will use the `pyproject.toml` configuration to produce artifacts under `dist/`.

## High-level architecture

### Top-level layout

Relevant top-level elements:

- `devsimpy/` – main application package (GUI, simulation logic, domain libraries, kernels, utilities).
- `tests/` – GUI-focused test suite (individual `test_*.py` scripts and `all.py` aggregator).
- `examples/` – sample models (e.g. `examples/model0/model0.dsp`) used by CI.
- `pyproject.toml` – project metadata, dependencies, and console script configuration.

### Core application (`devsimpy/devsimpy.py`)

The primary entrypoint is `devsimpy/devsimpy.py`, which:

- Initializes wxPython and config/builtins via `config.py` (`UpdateBuiltins`, global DEVS settings, kernel paths, etc.).
- Creates the main wxPython `MainApplication` frame:
  - Manages the overall window layout with `wx.aui.AuiManager`.
  - Hosts:
    - `ControlNotebook` – left-side pane containing the library tree and search tree (`LibraryTree`, `LibPanel`, `PropPanel`).
    - `DiagramNotebook` – central pane managing diagram tabs (each tab hosts a DEVS block diagram via `Container` / `ShapeCanvas`).
    - A simulation panel and an embedded `wx.py` shell for interactive scripting.
- Integrates with many subsystems:
  - `PluginManager` – discovers and loads plugins, exposed through `PluginsGUI`.
  - `PreferencesGUI` – user settings.
  - `YAMLExportGUI` – export diagrams to YAML for external tools (e.g. DEVSimPy-mob).
  - `Reporter` – exception handling (`ExceptionHook`).
  - Utility functions in `Utilities` for updating from git, package installation, notifications, etc.

`pyproject.toml` points the console script `devsimpy` at `devsimpy.devsimpy:main`, so installed usage and direct script usage share the same main entrypoint.

### Simulation kernels and domain abstraction

DEVSimPy separates *domain-independent* DEVS semantics from *domain-specific* models:

- `DEVSKernel/` – DEVS simulation backends:
  - `PyDEVS/DEVS.py` – PyDEVS-based kernel.
  - `PyPDEVS/` – PyPDEVS-based kernel.
  - `KafkaDEVS/` – DEVS-on-Kafka kernel for distributed simulations.
  - `Strategies.py` – strategy objects for different simulation modes.
  - `__init__.py` – exposes available kernels (`PyDEVS`, `PyPDEVS`, `KafkaDEVS`).

- `DomainInterface/` – bridge between the GUI and kernels:
  - `DomainStructure.py` – abstract base for domain structures:
    - Dynamically imports the appropriate `DEVSKernel.*.DEVS` module based on global configuration (`DEFAULT_DEVS_DIRNAME`, `DEVS_DIR_PATH_DICT` in `config.py`).
    - Derives from `BaseDEVS.CoupledDEVS` and standardizes accessors for component sets (`getComponentSet`, `setComponentSet`, `addToComponentSet`, `delToComponentSet`).
  - `DomainBehavior.py`, `MasterModel.py`, `Object.py` – define the behavior and structure interface that domain-specific models implement to be manipulated from the GUI and simulated by the chosen kernel.

- `Domain/` – domain-specific model libraries:
  - `Basic/` – foundational building blocks (`Atomic`, `Coupled`, `IPort`, `OPort`, `Object`).
  - `Generator/` – input generators (file-based, random, XML, etc.).
  - `Collector/` – output sinks (to disk, stdout, plotly, pusher, etc.).
  - `FSM/` – finite state machine models.
  - `Web/` – web-related generators/collectors.

These domain libraries are loaded into the GUI library tree and can be used to build hierarchical DEVS diagrams.

### GUI composition and behaviors

The GUI is built from many composable components:

- Diagram canvas and nodes:
  - `Container` – central diagram canvas and diagram-specific logic.
  - `Components` – block representations on the canvas.
  - `atomic_model_scheme.py` – schematic representation of atomic models.

- Mixins and patterns:
  - `Mixins/` – cross-cutting behaviors for diagram objects (e.g. `Connectable`, `Attributable`, `Savable`, `Iconizable`, `Selectable`, `Structurable`).
  - `Patterns/` – implementation of common design patterns (`Factory`, `Strategy`, `Observer`, `Singleton`, `Memoize`) used across simulation and GUI code.

- Supporting GUI modules:
  - Dialogs and frames: `CheckerGUI`, `ConnectDialog`, `DetachedFrame`, `DiagramConstantsDialog`, `FindGUI`, `WizardGUI`, `PluginsGUI`, `PreferencesGUI`, etc.
  - Panels and trees: `LibPanel`, `LibraryTree`, `PropPanel`, `ControlNotebook`, `DiagramNotebook`.
  - Tools: `Editor` (code editor), `PlotGUI`, `SpreadSheet`, `YAMLExportGUI`, `ZipManager`, `StandaloneGUI`, etc.

The `tests/` directory mirrors many of these components with targeted GUI tests (`test_*.py` files) that instantiate dialogs/frames, interact with them, and rely on `--autoclose` flags for unattended runs.

### No-GUI / batch simulation and integration points

For headless workloads and integration with web/remote clients:

- `SimulationNoGUI.py`:
  - Provides `makeSimulation` and `runSimulation` classes for running simulations without a GUI.
  - Accepts a `master` DEVS model and a simulation horizon `T`, manages:
    - Creation of a simulator via `Patterns.simulator_factory` (using kernel strategy and flags such as `NTL`, `DEFAULT_SIM_STRATEGY`, `DYNAMIC_STRUCTURE`, `REAL_TIME`).
    - Optional progress reporting on stdout and (commented) hooks for streaming status/outputs via pusher or sockets.
    - Integration with `InteractionSocket.InteractionManager` for remote control of simulations.
  - Handles logging of simulation reports under `logs/` when `simu_name` is provided.

- `devsimpy/devsimpy-nogui.py` and `devsimpy/devsimpy.py --nogui`:
  - Provide CLI entrypoints that parse command-line arguments (`-sim`, `-kernel`, etc.), instantiate the DEVS model from `.dsp` files, and invoke the no-GUI simulation flow.

- Integration/serialization helpers:
  - `InteractionSocket.py` / `InteractionYAML.py` – communication and YAML-based interaction with simulations.
  - `YAMLExportGUI.py` – export diagrams to YAML for external tools (e.g. mobile or web versions of DEVSimPy).

### Plugins and AI-related components

The codebase contains explicit support for plugins and AI-assisted workflows:

- `PluginManager.py` and `PluginsGUI.py`:
  - Discover, enable/disable, and configure plugins.
  - Integrate plugins into the GUI (menus, panels, actions).

- `AI/` directory and AI modules:
  - `AI/DEVS_Explanation.txt` and prompt templates under `AI/functions_prompt/` define text prompts and explanations for DEVS concepts and model functions.
  - `AIAdapter.py` and `AIPrompterDialog.py` integrate AI/LLM capabilities into the GUI, leveraging these prompts to assist users in understanding or generating DEVS models.

When editing or extending AI-related features, prefer to reuse the existing prompt files under `AI/` and the `AIAdapter`/`AIPrompterDialog` integration points instead of hardcoding new prompts in unrelated modules.

## Tests and CI alignment

CI workflows under `.github/workflows/` are the source of truth for how this project is exercised in automation:

- `ci-build-ubuntu.yml` (Ubuntu):
  - Sets up a conda environment with wxPython, installs Python dependencies via pip.
  - Runs a basic GUI smoke test via `xvfb-run -a python devsimpy/devsimpy.py examples/model0/model0.dsp 10 autostart autoclose`.
  - Iterates over a curated list of GUI tests under `tests/`, running each via `xvfb-run -a python <test_file> --autoclose`.

- `ci-build-windows.yml` (Windows):
  - Creates a venv and installs DEVSimPy from PyPI (`python -m pip install devsimpy`).
  - Runs a no-GUI simulation using the installed CLI (`devsimpy --nogui examples/model0/model0.dsp 10`).
  - Installs GUI dependencies (wxPython, PyPubSub, psutil) and runs the same curated list of GUI tests using `python <test_file> --autoclose --nogui`.

- `lint.yml` (lint job):
  - Runs `flake8 .` and `mypy .` against the repository with Python 3.13.

When modifying test behavior or adding new tests, align with these workflows so they continue to pass without additional CI changes.