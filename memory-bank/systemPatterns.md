# DEVSimPy System Architecture & Patterns

## Core Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DEVSimPy Application                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐      ┌──────────────────┐                    │
│  │  Main App Frame  │◄─────│     wx.App       │                    │
│  │  (Entry Point)   │      │  (Event Loop)    │                    │
│  └────────┬─────────┘      └────────┬─────────┘                    │
│           │                         │                               │
│  ┌────────▼─────────────────────────▼──────────────┐               │
│  │              Application Controllers             │               │
│  │   - ModelController   |   SimulationController  │               │
│  │   - AnalysisController|   PluginController      │               │
│  └─────────────────────────────────────────────────┘               │
│           │                         │                               │
│  ┌────────▼─────────────────────────────────────────▼─────┐        │
│  │                Service Layer                           │        │
│  │   - ModelLoaderService    |   KernelInvokerService    │        │
│  │   - ExportService         |   PluginDiscoveryService  │        │
│  └─────────────────────────────────────────────────────────┘        │
│           │                         │                               │
│  ┌────────▼─────────────────────┬────────▼───────────────┐          │
│  │    UI Components             │   DEVS Kernel          │          │
│  │   - CanvasView               │   (PyDEVS/PyPDEVS)     │          │
│  │   - PropertyEditor           │   Simulation Engine    │          │
│  │   - MetricsPanel             │   PyDEVS Core          │          │
│  └──────────────────────────────┴   Model Compiler       │          │
│                                                          └────────┐ │
└───────────────────────────                                    ▼───┘
                         ┌─────────────────────────────────────────┐
                         │         External Dependencies            │
                         │  wxPython | PyDEVS | NumPy | SciPy      │
                         └─────────────────────────────────────────┘
```

---

## Key Technical Decisions

### 1. GUI Framework: wxPython 4.x
**Rationale**: Native cross-platform widgets, rich event system for responsive UI  
**Trade-offs**: Requires native C++ dependencies, smaller community than Tkinter/PyQt

### 2. DEVS Kernel Abstraction Layer
```python
class IDevsKernel:
    def compile_model(model_path: str) -> ModelObject: ...
    def start_simulation(sim_time: int, steps: int) -> None: ...
    def step_forward() -> Event: ...
```

**Benefits**: Decouples GUI from simulation engine, enables switching between PyDEVS/PyPDEVS

### 3. Plugin Architecture Design
```python
class DevSimPyPlugin(BasePlugin):
    def __init__(self, app: wx.App) -> None: ...
    def on_model_loaded(self, model: Model) -> None: ...
```

**Discovery Pattern**: Scanning `plugins/` directory for installable packages  
**Isolation**: Each plugin runs in separate namespace to prevent conflicts

### 4. Model File Format (.dsp)
- **Structure**: YAML-based with version prefix
- **Versioning Strategy**: Prefix format enables backward compatibility checks

### 5. Event Loop Integration
**Challenge**: Balancing simulation timing with GUI responsiveness  
**Solution**: Separate thread pools - main wxPython thread for UI events, background worker for simulation steps, results pushed via wx.PostEvent()
### 5. Event Loop Integration
**Challenge**: Balancing simulation timing with GUI responsiveness  
**Solution**: Separate thread pools - main wxPython thread for UI events, background worker for simulation steps, results pushed via wx.PostEvent()

### 6. Class Naming Preservation (AI Code Generation)
**Rule**: When generating DEVS model code from graphical components, class names MUST match the diagram labels EXACTLY for `DomainBehavior` and `DomainStructure` subclasses (case-sensitive). **This rule applies ONLY to DEVS model classes inheriting from `DomainBehavior` (atomic models) or `DomainStructure` (coupled models)**, not to wxPython GUI components or controllers. See [`memory-bank/CLASSES-NAMING.md`](./memory-bank/CLASSES-NAMING.md) for full guidelines.  
**Rationale**: Ensures consistency with tests, imports, IDE features, and user expectations.


---

## Design Patterns Used

1. **MVP (Model-View-Presenter)**: Controllers act as presenters, views implement wxPython widgets
2. **Observer Pattern**: Any component can subscribe to simulation events
3. **Strategy Pattern for Kernels**: Easy switching between PyDEVS and PyPDEVS backends
4. **Factory Pattern for Component Creation**: Map of component types to creation functions
5. **Mixins**: Mixins are used to extends functionnalities of classes

---

## Performance Considerations

- Canvas uses off-screen buffer with dirty region tracking for complex models
- Weak references to observers prevent memory leaks
- Main wxPython thread handles all UI updates; simulation isolated in worker thread

---

**Last Updated**: October 2, 2026