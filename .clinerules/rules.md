# Cline Rules — DEVSimPy

## 1. General principle

Cline is an AI development assistant for the DEVSimPy project.

The goal is to modify, test and improve DEVSimPy while preserving its existing architecture, behavior and DEVS semantics.

Cline MUST understand the existing implementation before making changes.

Do not guess when the repository can provide the answer.

Preferred workflow:

```text
Inspect → Understand → Plan → Modify → Test → Validate
```

---

## 2. Inspect before modifying

Before modifying code, Cline MUST:

1. Inspect the relevant source files.
2. Search for existing implementations.
3. Search for usages of the affected classes/functions.
4. Inspect relevant tests.
5. Identify existing abstractions that can be reused.

Do not generate code based only on the task description when the repository contains relevant implementation details.

---

## 3. Preserve the existing architecture

DEVSimPy is an established project.

Prefer:

* reusing existing classes;
* extending existing functionality;
* following existing patterns;
* making small focused changes.

Avoid:

* unnecessary refactoring;
* introducing parallel abstractions;
* replacing existing mechanisms without justification;
* changing unrelated code;
* introducing new frameworks unnecessarily.

Existing DEVSimPy conventions take precedence over generic AI-generated coding patterns.

---

## 4. DEVS semantics

DEVSimPy implements the DEVS formalism.

When modifying simulation-related code, preserve the existing semantics of:

* atomic models;
* coupled models;
* state transitions;
* internal transitions;
* external transitions;
* confluent transitions;
* output functions;
* time advance;
* event scheduling;
* ports;
* couplings.

Never change simulation semantics merely to simplify an implementation.

If the semantic behavior is unclear, inspect the existing implementation and tests before making a decision.

---

## 5. Atomic and coupled models

Respect the distinction between:

```text
Atomic model
    → DomainBehavior

Coupled model
    → DomainStructure
```

Do not mix responsibilities between these abstractions.

When modifying an atomic model, preserve its behavioral semantics.

When modifying a coupled model, preserve its structural and coupling semantics.

---

## 6. Class naming

### CRITICAL RULE

For generated DEVSimPy model code, the Python class name MUST exactly match the name of the corresponding graphical model element.

For example:

```text
Graphical element:
Generator
```

must produce:

```python
class Generator(DomainBehavior):
    ...
```

And:

```text
Graphical element:
TrafficSource
```

must produce:

```python
class TrafficSource(DomainBehavior):
    ...
```

Cline MUST NOT:

* invent another class name;
* add prefixes or suffixes;
* automatically transform the name;
* rename the Python class independently of the graphical model element.

This rule takes precedence over generic Python naming preferences.

Before generating model code, inspect existing DEVSimPy code and conventions.

---

## 7. Minimal changes

When fixing a bug or implementing a feature:

* modify the smallest number of files possible;
* avoid unrelated changes;
* preserve public APIs;
* preserve backward compatibility when possible;
* do not rename public classes or functions without explicit authorization;
* do not perform opportunistic refactoring.

A task should result in a focused and reviewable change.

---

## 8. Tests

Tests are an integral part of the project.

Before changing code, inspect relevant tests.

After changing code:

1. Run the most relevant targeted tests.
2. Run related integration tests when appropriate.
3. Run UI tests when GUI behavior is affected.
4. Run the complete test suite when appropriate.

The repository contains UI tests under:

```text
tests/
```

Cline MUST use these tests when they are relevant to the change.

Do not declare a change successful solely because the code compiles or imports successfully.

---

## 9. Testing environment

The canonical testing environment is defined separately from these project rules.

Do not assume that the current shell or Python interpreter is the correct one.

Follow the project's environment configuration and use the designated Python environment for testing.

Do not silently switch to another Python installation because it is more convenient.

---

## 10. Dependencies

Before adding a dependency:

1. Search the repository for existing functionality.
2. Check existing dependencies.
3. Determine whether the functionality can be implemented without a new dependency.
4. Consider compatibility with DEVSimPy.

Do not add dependencies without a clear technical reason.

---

## 11. Git safety

Cline MUST preserve the user's existing work.

Never silently discard modifications.

Do not perform destructive operations such as:

```text
git reset --hard
git clean -fd
git checkout -- <user files>
git restore <user files>
```

Do not:

* force push;
* rewrite history;
* delete branches;
* amend commits;
* rebase shared branches;

unless explicitly requested by the user.

Before significant Git operations, inspect the repository status.

---

## 12. Repository cleanliness

Do not create unnecessary files.

In particular, do NOT create temporary files whose only purpose is to describe the work performed or the resolution of a problem.

Examples include:

```text
CONSOLE_FIX.md
*_FIX.md
*_FIXES.md
*_SOLUTION.md
*_DEBUG.md
*_REPORT.md
*_SUMMARY.md
*_NOTES.md
*_ANALYSIS.md
WHAT_I_DID.md
```

Do not create such files unless explicitly requested by the user.

The result of a task should normally be communicated directly in the conversation.

---

## 13. Documentation

Do not automatically create documentation after completing a task.

Create or modify documentation only when:

* explicitly requested;
* required by the project;
* required for a public API;
* required for a permanent architectural decision;
* necessary to maintain existing project documentation.

A bug fix does not automatically require a new Markdown file.

---

## 14. Memory Bank

The `memory_bank/` directory is used for persistent project context.

Cline may read the memory bank when it is available.

Cline may update existing memory-bank files when persistent project context needs to be maintained.

Do not use arbitrary Markdown files in the source tree as a replacement for the memory bank.

Do not create new memory-bank files unless they are consistent with the existing memory-bank structure.

The memory bank describes project context; it is not a substitute for source code or tests.

---

## 15. User remains in control

Cline is an assistant, not an autonomous project owner.

For significant architectural decisions:

* explain the proposed approach;
* identify important consequences;
* avoid making irreversible decisions without user approval.

When several reasonable implementations exist, prefer the least invasive one.

---

## 16. Error handling

When a test fails:

1. Read the complete error.
2. Identify the actual cause.
3. Inspect the relevant implementation.
4. Check whether the failure is related to the current change.
5. Fix the root cause rather than hiding the failure.
6. Re-run the relevant test.

Do not simply modify tests to make them pass unless the test itself is demonstrably incorrect.

Never suppress an error merely to obtain a successful test result.

---

## 17. Generated code

When generating code:

* follow existing DEVSimPy conventions;
* use existing abstractions;
* preserve interfaces;
* avoid unnecessary boilerplate;
* keep the implementation understandable;
* add tests when appropriate.

Generated code must be treated as production code and validated accordingly.

---

## 18. Final validation

Before considering a task complete, verify:

* the requested functionality works;
* relevant tests pass;
* existing functionality has not unnecessarily changed;
* no unnecessary files were created;
* no temporary debugging artifacts remain;
* the Git working tree contains only intentional changes.

Report the result directly to the user.

Do not create a separate report file unless explicitly requested.

---

## 19. When uncertain

When uncertain about an implementation detail:

```text
Search the repository first.
```

When uncertain about expected behavior:

```text
Inspect the existing tests.
```

When uncertain about architecture:

```text
Inspect related classes and their usages.
```

Do not invent project conventions.

DEVSimPy's existing implementation, tests and explicit user instructions are the primary sources of truth.
