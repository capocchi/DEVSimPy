# DEVSimPy Project Brief

**Project Type**: DEVS Simulation Framework with wxPython GUI  
**License**: GPL v3 (Open Source)  
**Version**: 5.1+  

---

## Executive Summary

DEVSimPy is a Python-based open-source framework for modeling and simulating **Discrete Event Systems (DEVS)** with a comprehensive graphical user interface built on wxPython. The project simplifies interaction with PyDEVS and PyPDEVS models, enabling researchers and engineers to design, simulate, analyze, and modify DEVS systems interactively.

---

## Core Problem Statement

Traditional discrete event simulation requires:
- Complex mathematical modeling
- Command-line-only workflows
- Limited visualization capabilities
- No real-time analysis tools

DEVSimPy solves these by providing:
1. **Visual model design** through intuitive GUI interface
2. **Real-time simulation control** with start/pause/resume capabilities
3. **Interactive code editing** for on-the-fly model modifications
4. **Comprehensive analysis tools** integrated into the workflow
5. **Plugin architecture** for extensibility

---

## Primary Goals

### Immediate Objectives
- [x] Build robust wxPython GUI for DEVS modeling
- [x] Support PyDEVS and PyPDEVS kernels
- [x] Implement real-time simulation visualization
- [x] Enable model editing during execution
- [ ] Enhance performance for large-scale models

### User Experience Goals
- Intuitive drag-and-drop model design interface
- Clear, readable simulation timelines and state displays
- Seamless transition between modeling and analysis
- Minimal learning curve for DEVS practitioners

---

## Key Stakeholders

1. **Researchers**: Modeling complex systems (manufacturing, traffic, biological)
2. **Engineers**: Validating system designs before implementation
3. **Educators**: Teaching discrete event simulation concepts
4. **Extension Developers**: Building plugins and integrations

---

## Success Metrics

- Model compilation success rate (>95%)
- Simulation runtime performance (<1s for simple models)
- User satisfaction with GUI (subjective >4/5 rating)
- Plugin ecosystem growth (target: 10+ quality extensions)

---

## Document References

- `productContext.md`: Problem context and user journey
- `systemPatterns.md`: Architecture and technical decisions
- `techContext.md`: Stack, dependencies, and tooling
- `activeContext.md`: Current work in progress
- `progress.md`: Status tracking and evolution log