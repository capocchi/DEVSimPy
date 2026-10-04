# DEVSimPy Product Context

## Why This Project Exists

### The Challenge

Discrete Event Systems (DEVS) provide a powerful mathematical framework for modeling complex systems, but traditional approaches face significant barriers:

**Barriers in Traditional DEVS Tools:**
- ❌ Steep learning curve with formal notation requirements
- ❌ Command-line-only interfaces limit accessibility
- ❌ No visual feedback during model design
- ❌ Difficult to debug without execution context
- ❌ Limited collaboration capabilities
- ❌ No plateforme with AI Agent capability exist for DEVS

### The Solution

DEVSimPy democratizes discrete event simulation by:

1. **Visual Approach**: Transform abstract DEVS models into intuitive graphical representations
2. **Python Integration**: Leverage Python's simplicity while maintaining rigorous mathematical foundations
3. **Interactive Workflow**: Allow designers to see immediate results of modeling choices
4. **Real-time Analysis**: Monitor system behavior as it unfolds during simulation


## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      DEVSimPy GUI                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Model Design │  │ Simulation   │  │ Analysis Panel   │  │
│  │ (wxPython)   │◄─┤ Control      │►─┤ (Charts/Metrics) │  │
│  └──────────────┘  │              │  └──────────────────┘  │
│                    └──────────────┴───────────────────────┘  │
│                              │                               │
│                      ┌────────▼────────┐                     │
│                      │   DEVS Kernel   │◄─┐                 │
│                      │ (PyDEVS/PyPDEVS)│   │                 │
│                      └─────────────────┘   │ Plugin System  │
└────────────────────────────────────────────┴────────────────┘
```

### User Journey

#### Phase 1: Model Creation
1. User opens DEVSimPy GUI
2. Creates new model or loads existing `.dsp` file
3. Defines components (atomic, coupled, atomic/coupled hybrids)
4. Configures internal states and transition functions
5. Sets interconnections between components
6. Saves model to workspace

#### Phase 2: Simulation Execution
1. User presses "Run" button
2. DEVSimPy compiles `.dsp` to kernel-readable format
3. Sends to PyDEVS/PyPDEVS for simulation engine
4. GUI displays real-time state changes
5. User can pause/resume/speed-adjust simulation

#### Phase 3: Analysis & Refinement
1. View metrics and charts from running simulation
2. Export results to CSV/PDF formats
3. Modify model parameters on-the-fly
4. Re-run with adjusted configurations
5. Compare multiple simulation runs

---

## Problems It Solves

### For Modelers

**Problem**: "I can't visualize what my DEVS model looks like before running."  
**Solution**: Interactive canvas with component placement and connection tools.

**Problem**: "My model is too complex to track in command-line output."  
**Solution**: Integrated visualization panel showing system state, timers, and events.

### For Researchers

**Problem**: "I need to compare multiple parameter configurations."  
**Solution**: Parameter sweep tools and result comparison panels.

**Problem**: "How does changing this component affect overall behavior?"  
**Solution**: Instant feedback loop with hot-reload capability.

### For Educators

**Problem**: "Students struggle with abstract DEVS notation."  
**Solution**: Visual metaphor system mapping formal concepts to intuitive graphics.

**Problem**: "Classroom demonstrations need quick setup."  
**Solution**: Pre-built example models and drag-and-drop classroom demos.

---

## User Experience Goals

### Core Principles

1. **Clarity First**: Every element has a clear purpose; no hidden complexity
2. **Progressive Disclosure**: Show advanced options only when needed
3. **Forgiving Design**: Easy undo/redo, sensible defaults for common tasks
4. **Consistency**: Uniform interaction patterns throughout interface
5. **Performance**: Responsive even with complex models (60+ components)

### Visual Design Guidelines

- Use wxPython's native themes when possible
- Color-coding for model types: blue=atomic, green=coupled, orange=flow
- Monospace fonts for all numerical/time information
- High contrast for accessibility (WCAG AA compliant)
- Keyboard shortcuts documented in help system

### Error Handling Philosophy

- Never show raw stack traces to users
- Provide actionable error messages with suggestions
- Log detailed errors internally for developer debugging
- Recover gracefully from user mistakes (no data loss)


## Success Criteria

### Functional Requirements
- ✅ Load and save DEVS models (.dsp format)
- ✅ Execute simulation via PyDEVS/PyPDEVS kernels
- ✅ Visualize model structure with interactive canvas
- ✅ Monitor real-time simulation state
- ✅ Export results to multiple formats (CSV, PNG, PDF)

### Quality Requirements
- < 100ms response time for GUI actions
- Support Python 3.10+ and wxPython 4.x
- Comprehensive documentation (user guide + API)
- Active community with >5 active contributors

### Business Metrics
- Download count growth (+20% year-over-year)
- GitHub Stars (>500 on PyPI page)
- Citation rate in academic papers
- Plugin marketplace participation

---

## Integration Points

### External Dependencies
- **PyDEVS**: Native Python DEVS simulator
- **PyPDEVS**: Parallel/High-performance DEVS variant
- **wxPython 4.x**: Cross-platform GUI toolkit
- **NumPy/SciPy**: Numerical computations and analysis

### Ecosystem Connections
- DEVSimPy-rest: REST API for remote execution
- PyDEVS repository model format compatibility

---

## Limitations & Trade-offs

### Current Constraints
- wxPython primarily targets Windows/Linux/macOS desktop (no mobile)
- Complex distributed simulations limited to Python interpreter speed
- Requires Python installation on target machines

### Future Considerations
- Potential WebAssembly port for browser-based DEVS tools
- Cloud deployment options via containerization
- Mobile app wrappers (React Native/Flutter)

---

## Competitive Landscape

| Tool | Visual Interface | Real-time Analysis | Plugin System | License |
|------|------------------|-------------------|---------------|---------|
| DEVSimPy | ✅ | ✅ | ✅ | GPL v3 |
| AnyLogic | ✅ | ⚠️ Limited | ⚠️ Closed | Commercial |
| Simio | ⚠️ Partial | ✅ | ✅ | Commercial |
| Arena | ❌ No | ✅ | ⚠️ Hybrid | Commercial |

**DEVSimPy's Edge**: Open source + active community + Python integration

