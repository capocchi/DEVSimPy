# DEVSimPy Class Naming Convention

## CRITICAL RULE FOR AI CODE GENERATION

### 1. Core Rule

When generating or modifying code for a **DEVSimPy DEVS model**, the Python class name **MUST exactly match the name of the corresponding graphical DEVS model element**.

This rule is **case-sensitive**.

It applies **ONLY** to classes representing DEVS models:

* `DomainBehavior` → atomic DEVS model
* `DomainStructure` → coupled DEVS model

**The AI MUST NOT rename, normalize, prefix, suffix, or otherwise modify the graphical model name.**

For example:

```python
# Graphical model: "Generator"
class Generator(DomainBehavior):
    ...
```

```python
# Graphical model: "CoupledSystem"
class CoupledSystem(DomainStructure):
    ...
```

---

## 2. Scope

### Applies to DEVS model classes

This rule applies to every class inheriting directly or indirectly from:

```python
DomainBehavior
```

or

```python
DomainStructure
```

These classes represent models that participate in the DEVS simulation.

| DEVS model    | Required inheritance | Example                                 |
| ------------- | -------------------- | --------------------------------------- |
| Atomic model  | `DomainBehavior`     | `class Generator(DomainBehavior)`       |
| Atomic model  | `DomainBehavior`     | `class RandomGenerator(DomainBehavior)` |
| Atomic model  | `DomainBehavior`     | `class PlotlyStream(DomainBehavior)`    |
| Coupled model | `DomainStructure`    | `class CoupledSystem(DomainStructure)`  |
| Coupled model | `DomainStructure`    | `class MasterModel(DomainStructure)`    |

### Does NOT apply to non-DEVS classes

This naming rule does **NOT** apply to:

* wxPython widgets (`wx.Frame`, `wx.Panel`, etc.)
* GUI classes
* controllers
* managers
* services
* utilities
* helper classes
* adapters
* test classes

For example:

```python
class SimulationGUI(wx.Frame):
    ...
```

```python
class SimulationController:
    ...
```

These classes may use normal Python naming conventions.

---

# 3. Mandatory Naming Rules

When the graphical DEVS model is named `X`:

### Atomic model

The implementation MUST be:

```python
class X(DomainBehavior):
    ...
```

### Coupled model

The implementation MUST be:

```python
class X(DomainStructure):
    ...
```

The AI MUST preserve the name **exactly**.

This includes:

* capitalization
* CamelCase
* underscores
* abbreviations
* prefixes already present in the name
* suffixes already present in the name

### Example

If the graphical model is:

```text
RandomGenerator
```

the class MUST be:

```python
class RandomGenerator(DomainBehavior):
```

It MUST NOT become:

```python
class Generator(DomainBehavior):
class MyRandomGenerator(DomainBehavior):
class AIRandomGenerator(DomainBehavior):
class RandomGeneratorModel(DomainBehavior):
class randomGenerator(DomainBehavior):
```

---

# 4. NEVER Invent or "Improve" a DEVS Model Name

The AI MUST NOT change a DEVS model class name because it considers another name:

* clearer
* more Pythonic
* more descriptive
* more consistent
* more readable
* more professional
* more explicit
* easier to understand

In particular, the AI MUST NOT automatically add:

```text
My_
New_
AI_
Generated_
Model_
DEVS_
Base_
Main_
```

or equivalent prefixes/suffixes.

### Example

Graphical model:

```text
Generator
```

Correct:

```python
class Generator(DomainBehavior):
```

Incorrect:

```python
class DEVSGenerator(DomainBehavior):
class MyGenerator(DomainBehavior):
class GeneratedGenerator(DomainBehavior):
class GeneratorModel(DomainBehavior):
```

---

# 5. The Graphical Model Name Has Priority

When there is a conflict between:

1. normal Python naming conventions,
2. the filename,
3. an existing variable name,
4. an AI-generated name,
5. the graphical DEVS model name,

**the graphical DEVS model name has priority.**

The graphical model name is the authoritative source for the DEVS model class name.

For example:

```text
Graphical model name: PlotlyStream
File name: MyPlotlyStream.py
```

The class MUST still be:

```python
class PlotlyStream(DomainBehavior):
```

The AI MUST NOT infer the class name from the filename if the graphical model name is available.

---

# 6. Do Not Confuse File Names and Class Names

A DEVSimPy model may be stored in a Python file whose name does not necessarily determine the required class name.

Therefore:

> **The Python filename is NOT the authoritative source for the DEVS model class name.**

The authoritative source is the graphical DEVS model label/name.

Example:

```text
Graphical model:
    Generator

Python file:
    CustomGenerator.py
```

The class must remain:

```python
class Generator(DomainBehavior):
```

---

# 7. Inheritance Must Match the DEVS Model Type

The AI MUST also preserve the correct DEVS inheritance.

### Atomic model

```python
class Generator(DomainBehavior):
    ...
```

### Coupled model

```python
class CoupledSystem(DomainStructure):
    ...
```

The AI MUST NOT replace the appropriate base class with another class simply to make the generated code appear more conventional.

For example:

```python
class Generator(BaseModel):
```

is incorrect if `Generator` is an atomic DEVSimPy model.

---

# 8. Existing Model Modification

When modifying an existing DEVSimPy model, the AI MUST first identify:

1. the graphical model name;
2. whether the model is atomic or coupled;
3. the existing class;
4. references to that class;
5. tests associated with the model.

The AI MUST preserve the existing DEVS model class name unless the user explicitly requests a rename.

### Default behavior

If an existing model contains:

```python
class Generator(DomainBehavior):
```

the AI MUST continue using:

```python
class Generator(DomainBehavior):
```

even if it believes another name would be better.

---

# 9. Renaming Is an Explicit Operation

A DEVS model class may be renamed ONLY when:

* the user explicitly requests the rename;
* a deliberate refactoring requires the rename and all references are migrated;
* a confirmed typo must be corrected;
* a new independent model is being created.

If the user says:

> Rename `Generator` to `RandomGenerator`.

then the AI may perform the rename.

Otherwise:

> **DO NOT rename the class.**

A suspected typo MUST NOT be silently corrected.

---

# 10. Code Generation Procedure

Before generating a DEVS model, the AI MUST perform the following checks.

### Before generation

* [ ] Identify the graphical model name.
* [ ] Preserve its spelling exactly.
* [ ] Preserve its capitalization exactly.
* [ ] Determine whether the model is atomic or coupled.
* [ ] Select `DomainBehavior` or `DomainStructure` accordingly.
* [ ] Inspect existing DEVSimPy code when necessary.

### During generation

* [ ] Use the exact graphical model name as the Python class name.
* [ ] Do not add prefixes.
* [ ] Do not add suffixes.
* [ ] Do not change capitalization.
* [ ] Do not "clean up" the name.
* [ ] Do not derive a different name from the filename.

### After generation

The AI MUST verify:

```text
Graphical name == Python class name
```

and, for an atomic model:

```text
class <GraphicalName>(DomainBehavior)
```

or, for a coupled model:

```text
class <GraphicalName>(DomainStructure)
```

If the names do not match, the generated code MUST be corrected before being considered complete.

---

# 11. Examples

### Atomic model

Graphical label:

```text
Generator
```

Correct:

```python
class Generator(DomainBehavior):
    """Atomic DEVS generator."""
    ...
```

---

### Atomic model with CamelCase

Graphical label:

```text
RandomGenerator
```

Correct:

```python
class RandomGenerator(DomainBehavior):
    ...
```

Incorrect:

```python
class Randomgenerator(DomainBehavior):
class Random_Generator(DomainBehavior):
class MyRandomGenerator(DomainBehavior):
```

---

### Atomic model containing an underscore

Graphical label:

```text
To_Stdout
```

Correct:

```python
class To_Stdout(DomainBehavior):
    ...
```

The underscore MUST be preserved.

---

### Coupled model

Graphical label:

```text
CoupledSystem
```

Correct:

```python
class CoupledSystem(DomainStructure):
    ...
```

Incorrect:

```python
class MainCoupledSystem(DomainStructure):
class ModelCoupledSystem(DomainStructure):
class Coupled_System(DomainStructure):
```

---

# 12. GUI Classes Follow Different Rules

The DEVS naming constraint must NOT be applied to GUI or application classes.

For example:

```python
class SimulationGUI(wx.Frame):
    ...
```

```python
class SimulationPanel(wx.Panel):
    ...
```

```python
class SimulationController:
    ...
```

These names can follow conventional Python/application naming practices.

The critical distinction is:

```text
DEVS graphical model
        ↓
exact class-name preservation
        ↓
DomainBehavior / DomainStructure
```

versus:

```text
GUI / Controller / Service / Utility
        ↓
normal Python naming conventions
```

---

# 13. DEVSimPy Validation Context

This convention is required because DEVSimPy uses model class names as part of its model loading, validation, generation, and integration mechanisms.

Relevant implementation areas include:

* `devsimpy/Components.py`
* `devsimpy/WizardGUI.py`
* `devsimpy/ZipManager.py`

In particular, the DEVSimPy infrastructure distinguishes DEVS model classes through `DomainBehavior` and `DomainStructure` inheritance and performs class-name-related processing.

Therefore, changing a DEVS model class name can break:

* model loading;
* graphical/model correspondence;
* model wiring;
* references;
* generated models;
* validation;
* tests;
* packaging/import mechanisms.

---

# 14. Critical Rule for AI Agents

When working on DEVSimPy code, apply this rule by default:

> **IF a class represents a graphical DEVS model AND it inherits from `DomainBehavior` or `DomainStructure`, THEN its class name MUST exactly match the corresponding graphical model name.**

The AI MUST NOT modify that name unless the user explicitly requests a rename.

### Final validation rule

Before finishing a task involving a DEVS model, verify:

```text
DEVS graphical name
        ==
Python class name
```

and:

```text
Atomic model  → DomainBehavior
Coupled model → DomainStructure
```

If either condition is false, the implementation is not compliant with this convention.
