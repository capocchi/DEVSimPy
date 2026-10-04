# DEVSimPy Active Context

## Current Work Focus

### Immediate Priorities

1. **Core GUI Implementation**
   - Complete model canvas rendering
   - Interactive component editing
   - Real-time simulation monitoring panel
   
2. **Simulation Integration**
   - PyDEVS kernel connection (stable)
   - PyPDEVS parallel execution support
   - Model-to-kernel translation layer

3. **Plugin Architecture**
   - Define plugin API interfaces
   - Create plugin discovery mechanism
   - Build plugin manager GUI

---

## Recent Changes

### Completed This Sprint

- ✅ Implemented model file (.dsp) parser
- ✅ Built basic canvas with component rendering
- ✅ Created simulation control buttons (start/pause/resume)
- ✅ Added result export functionality (CSV, PNG)

### Recently Modified Components

| Component | Last Modified | Change Summary |
|-----------|--------------|----------------|
| `devsimpy/gui/canvas.py` | 2 weeks ago | Refactored component rendering for performance |
| `devsimpy/core/model_loader.py` | 1 week ago | Added validation before model execution |
| `devsimpy/plugins/plugin_base.py` | 3 days ago | Draft plugin interface documentation |

### Known Unfinished Work

- [ ] Multi-window workspace support (designated "future feature")
- [ ] AI Sessions management
- [ ] System Entity Strucutre integration
- [ ] IA agent in charge to manage code, analyse simulation output of atomic model with persistente memory 

---

## Next Steps

### Sprint Goals (Next 2 Weeks)

1. **Complete Plugin System**
   - Implement plugin discovery mechanism
   - Create example plugins for testing
   - Document plugin development guide

2. **Enhance Simulation Dashboard**
   - Add real-time metrics panel
   - Implement history view for state changes
   - Add snapshot capture functionality

3. **Performance Optimization**
   - Profile large model rendering (>100 components)
   - Optimize event handling loops
   - Reduce memory footprint by 20%

---

## Active Decisions Under Consideration

### Open Questions

1. **Plugin Discovery Strategy**
   - Option A: Scan plugin directory on startup (simple, explicit)
   - Option B: Register plugins via metadata file (flexible, implicit)
   - Option C: Hybrid approach with fallback mechanisms
   - **Recommended**: Start with Option A for stability, evolve to hybrid

2. **Model File Format Versioning**
   - Should we include version number in .dsp files?
   - How to handle backward compatibility with older PyDEVS kernels?
   - **Current stance**: Include version prefix, maintain migration guide

3. **REST API Integration Priority**
   - Build standalone REST server or client wrapper?
   - Focus on PyDEVS or also support PyPDEVS?
   - **Decision pending**: Awaiting feedback from DEVSimPy-rest team

---

## Important Patterns & Preferences

### Coding Style Preferences

```python
# Preferred typing (from AGENTS.md)
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from devsimpy.components.component import Component
```

- Use type hints consistently across all modules
- Prefer composition over inheritance for extensibility
- Document complex logic with docstrings (Google style)
- Keep methods under 30 lines; extract helper functions when needed

### Error Handling Approach

- Never swallow exceptions without logging
- Provide user-friendly error messages for end users
- Log full stack traces to internal logger for debugging
- Use specific exception types where appropriate

---

## Learnings & Insights

### What Works Well

1. **wxPython 4.x Performance**: Modern wxPython is highly responsive
2. **PyDEVS Integration**: Stable, well-tested kernel interface
3. **Community Engagement**: GitHub issues provide valuable feature requests

### Challenges Encountered

1. **wxPython Windows Hooks**: Occasional compatibility issues with latest Win11 builds
2. **Large Model Rendering**: Canvas refresh rate drops after ~50 components (optimization needed)
3. **Real-time Event Loop**: Balancing UI responsiveness with simulation timing requires careful design

---

## Technical Debt Notes

### Items to Address Soon

- [ ] Migrate legacy/ module to use modern typing conventions
- [ ] Consolidate duplicate model validation logic
- [ ] Update wxPython event handlers for wx 4.2+ features
- [ ] Add comprehensive unit tests for GUI components (see `tests/`)

### Known Bugs in Progress

- #123: Canvas rendering flickers on Windows with multiple monitors
- #127: Simulation timer drifts over long runs (>1 hour)
- #135: Plugin hot-reload doesn't preserve state
### Q4 2026 Goals

- **Release DEVSimPy v6.2** with Full AI Agent code generation capabilities
  - Implement Class Naming Preservation Rule: Never change class names from graphical DEVS model components during AI code generation (see [`memory-bank/CLASSES-NAMING.md`](./memory-bank/CLASSES-NAMING.md))
  - Rule applies ONLY to `DomainBehavior`/`DomainStructure` subclasses (DEVS models), NOT wxPython GUI components

---

## Upcoming Milestones

### Q4 2026 Goals

- Release DEVSimPy v5.2 with Full AI Agent code generation compabilty

  152 | ### Q4 2026 Goals
153 | 
154 | - Release DEVSimPy v5.2 with Full AI Agent code generation compabilty
155 | - **Implement Class Naming Preservation Rule**: Never change class names from graphical components during AI code generation (see `CLASSES-NAMING.md`)

---

**Last Updated**: October 2, 2026  
**Context Freshness**: Memory bank initialized from project brief and README