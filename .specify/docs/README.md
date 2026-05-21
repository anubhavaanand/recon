# RECON Specification & Planning Kit

This directory contains comprehensive specification, planning, and evaluation documentation for the RECON patent research TUI project.

## Document Structure

### Core Specifications
- **`../RECON_PRD_v1.0.0.md`** - Canonical product requirements document for UI, UX, behavior, and roadmap
- **`spec.md`** - Feature specification with user stories, requirements, success criteria
- **`constitution.md`** - Core principles governing all design decisions

### Evaluation Framework
- **`evaluation-framework.md`** - Comprehensive testing and quality assurance framework
- **`README.md`** - This file, navigation guide

### Planning & Tasks
- `../tasks/EVALUATION_TASKS.md` - Detailed task breakdown for evaluation framework implementation

---

## Quick Navigation

### For Product/Feature Development
1. Read `../RECON_PRD_v1.0.0.md` - Canonical product requirements, UI, UX, and roadmap
2. Read `spec.md` - Understand requirements and user stories
3. Read `constitution.md` - Align design decisions with core principles
4. Reference `evaluation-framework.md` Section 8-9 for Constitutional compliance testing

### For Quality Assurance & Testing
1. Start with `evaluation-framework.md` - Overview of entire testing strategy
2. Review test scopes in Sections 1-7 for your specific module
3. Check `../tasks/EVALUATION_TASKS.md` for task breakdown and sequencing

### For Team Onboarding
1. **Product Context**: Read `spec.md` (5 min) + `constitution.md` (3 min)
2. **Architecture**: Review `evaluation-framework.md` Section 7-9 (10 min)
3. **Tasks**: Reference `../tasks/EVALUATION_TASKS.md` Task Groups relevant to your role (20 min)

### For CI/Automation
1. Review `evaluation-framework.md` Section 10 - Test Execution Strategy
2. Reference `../tasks/EVALUATION_TASKS.md` Task 6.2 - CI Integration
3. Check `.specify/scripts/bash/validate-evaluation.sh` for implementation

---

## Key Principles (from Constitution)

✅ **Zero-AI Default** - Deterministic, no hidden LLM layers  
✅ **Transparency over Persuasion** - Data presented exactly as retrieved  
✅ **Equal Signal Weights** - No black-box ranking algorithms  
✅ **Descending Sort, Never Removing** - Results ranked, entries never silently dropped  
✅ **Terminal-Native & Keyboard-First** - CLI-only, no GUI fallback  
✅ **Speed over Depth** - Fast initial responses, deep data on demand  
✅ **Uncertainty Flagged** - Missing data marked explicitly, never guessed  
✅ **Dry, Actionable Errors** - Terse, factual, never apologetic  

---

## Test Strategy at a Glance

| Layer | What | File | Coverage Target |
|-------|------|------|-----------------|
| **Unit** | Core modules | `tests/test_*.py` | 85%+ |
| **Widget** | TUI components | `test_tui_components.py` | All widgets |
| **Integration** | Tab lifecycle | `test_tab_integration.py` | Tab loading, preview sync |
| **Performance** | Latency, memory | `test_performance.py` | <3s search, <100ms nav |
| **Compliance** | Constitution audit | `test_error_handling.py` | 100% actionable errors |
| **Health** | Quick check | `health_check.py` | <5s, clear status |

---

## How to Use These Documents

### ✅ YES - These documents are designed to be:
- **Discoverable**: All agents can read `.specify/docs/` files from your workspace
- **Linked**: Cross-references between spec, tasks, and implementation
- **Executable**: Task descriptions contain specific file paths and checklist items
- **Actionable**: Each task has success criteria and related test modules
- **Versioned**: Part of your git repository for history tracking

### ❌ NOT for:
- Session-scoped planning (use `/home/anubhavanand/.copilot/session-state/*/plan.md`)
- Personal notes (these should be outside the repo)
- Temporary debugging (use branch-specific notes)

---

## Agent Reading & Execution

### How Agents Access These Specs

When any agent (explore, task, general-purpose, code-review) runs within this folder, it can:

1. **Read specification documents** from `.specify/docs/`
2. **Access task breakdowns** from `.specify/tasks/`
3. **Reference linked files** (spec.md → evaluation-framework.md → EVALUATION_TASKS.md)
4. **Execute based on context** - e.g., "implement Task 1.1 from EVALUATION_TASKS.md"

### Example Agent Command Patterns

```bash
# Explore agent: Understand test architecture
"Review .specify/docs/evaluation-framework.md and list what tests currently exist in tests/"

# Task agent: Execute a specific task
"Implement Task 1.1 (Import Validation Module) from .specify/tasks/EVALUATION_TASKS.md"

# General-purpose agent: Plan comprehensive work
"Create implementation plan for evaluation framework based on .specify/tasks/EVALUATION_TASKS.md"

# Code-review agent: Audit against specs
"Review core/search.py against spec requirements in .specify/docs/spec.md section 1.4"
"Review tui/screens.py against the mockups in .specify/docs/prd.md section 3"
```

---

## Document Ownership & Maintenance

| Document | Owner | Review Cycle | Update Trigger |
|----------|-------|--------------|-----------------|
| `spec.md` | Product Manager | Quarterly | Feature changes, scope updates |
| `constitution.md` | Architecture | Annually | Principle drift, major design shifts |
| `evaluation-framework.md` | QA Lead | Per-sprint | Test coverage gaps, metric adjustments |
| `EVALUATION_TASKS.md` | Dev Lead | Per-phase | Task completion, dependency changes |

---

## Success Metrics

When evaluation framework is fully implemented, you should see:

✅ Import validation on every startup  
✅ Tab loading works (preview populates)  
✅ Health check runs in <5 seconds  
✅ All core tests pass with 85%+ coverage  
✅ Performance benchmarks <3s search, <100ms navigation  
✅ 100% actionable error messages  
✅ Constitutional compliance audit quarterly  
✅ Regression detection with baseline metrics  

---

## Related Files in Repository

- `../RECON_PRD_v1.0.0.md` - Canonical PRD and feature source of truth
- `.specify/workflows/` - CI/CD automation
- `.specify/scripts/bash/` - Helper scripts
- `tests/` - Test implementations
- `EVALUATION.md` - Generated runbook (created by Task 7.1)
- `pyproject.toml` - Dependencies and test config
- `pytest.ini` - Test framework configuration

---

## Questions?

Refer to the specific document section:
- **"How do I run tests?"** → `evaluation-framework.md` Section 10
- **"What should I test for?"** → `evaluation-framework.md` Sections 1-7 (by module)
- **"What's my next task?"** → `.specify/tasks/EVALUATION_TASKS.md` (by phase)
- **"How does this align with goals?"** → `spec.md` (requirements) or `constitution.md` (principles)

---

**Last Updated**: 2026-05-13  
**Framework Status**: Ready for Implementation  
**Next Phase**: Foundation Tasks (Tasks 1.1-1.2, 8.1-8.2)
