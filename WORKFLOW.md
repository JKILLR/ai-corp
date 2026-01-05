# AI Corp Development Workflow

## Overview

This document defines the rules and processes for working on the AI Corp project. All contributors (human or AI) must follow these guidelines.

---

## Core Principles

### 1. Modularity First
- Every component must be swappable
- Use interfaces/abstract classes for extensibility
- No tight coupling between modules
- Factory patterns for object creation

### 2. Full Integration
- New code must integrate with existing systems
- Don't just "stack on top" - connect properly
- Update `__init__.py` exports when adding modules
- Run integration tests after changes

### 3. Documentation Always
- Update `AI_CORP_ARCHITECTURE.md` for any architectural changes
- Update `STATE.md` after every major update
- Add docstrings to all classes and public methods
- Keep this `WORKFLOW.md` current

### 4. Code Quality Standards (TCMO)

All code must meet the **TCMO standard** before being considered complete:

| Dimension | Requirement | How to Verify |
|-----------|-------------|---------------|
| **T**ested | Unit tests + integration tests | `pytest tests/` passes |
| **C**lean | No dead code, clear naming, DRY | Code review checklist |
| **M**odularized | Swappable, loosely coupled | Can replace any component |
| **O**ptimized | No obvious inefficiencies | Profile critical paths |

#### Tested
- Every module has corresponding tests in `tests/`
- Unit tests for individual functions/classes
- Integration tests for component interactions
- End-to-end tests for full workflows
- Target: 80%+ code coverage

#### Clean
- No dead code (unused functions, imports, variables)
- Clear, descriptive naming (no single-letter vars except loops)
- DRY - Don't Repeat Yourself (extract common patterns)
- Consistent formatting (follow existing style)
- No commented-out code in commits
- Proper error messages (not just "Error occurred")

#### Modularized
- Every component has an interface/protocol
- Use dependency injection, not hard-coded dependencies
- Factory patterns for object creation
- No circular imports
- Clear module boundaries (core, agents, cli, utils)

#### Optimized
- No N+1 query patterns (batch operations where possible)
- Lazy loading for expensive resources
- Appropriate data structures (dict for lookups, list for iteration)
- Profile before optimizing (don't guess at bottlenecks)
- Document known performance tradeoffs

### TCMO Checklist

Before marking any feature complete, verify:

```
[ ] TESTED
    [ ] Unit tests written and passing
    [ ] Integration tests cover key flows
    [ ] Edge cases handled (empty inputs, errors)
    [ ] Tests run in CI (when available)

[ ] CLEAN
    [ ] No dead code
    [ ] Names are clear and descriptive
    [ ] No code duplication
    [ ] Proper docstrings on public APIs

[ ] MODULARIZED
    [ ] Uses interfaces/protocols
    [ ] Dependencies are injected
    [ ] Can be tested in isolation
    [ ] Exports updated in __init__.py

[ ] OPTIMIZED
    [ ] No obvious inefficiencies
    [ ] Appropriate algorithms used
    [ ] Resource cleanup handled
    [ ] Performance acceptable for expected load
```

---

## Development Rules

### Before Starting Work

1. **Read `STATE.md`** - Understand current project state
2. **Review `AI_CORP_ARCHITECTURE.md`** - Understand the system
3. **Check existing code** - Don't duplicate functionality
4. **Plan the approach** - Consider integration points

### During Development

1. **Follow existing patterns** - Match the codebase style
2. **Use dataclasses** - All models should be dataclasses
3. **Add type hints** - Full type annotations required
4. **Create checkpoints** - For large changes, commit incrementally
5. **Test as you go** - Verify syntax and imports work

### After Changes

1. **Update `__init__.py`** - Export new classes/functions
2. **Run syntax checks** - `python3 -c "import ast; ast.parse(open('file.py').read())"`
3. **Run import tests** - Verify module can be imported
4. **Update `STATE.md`** - Record what changed
5. **Update `AI_CORP_ARCHITECTURE.md`** - If architecture changed
6. **Commit with descriptive message** - Explain the "why"

---

## File Organization

### Source Code (`src/`)

```
src/
├── core/           # Infrastructure (molecules, hooks, beads, etc.)
├── agents/         # Agent implementations
├── cli/            # Command-line interface
└── utils/          # Shared utilities
```

### State Files (`corp/`)

```
corp/
├── org/            # Organizational structure (YAML)
├── hooks/          # Agent work queues (YAML)
├── molecules/      # Workflows (YAML)
├── beads/          # Git-backed ledger
├── channels/       # Messages (YAML)
├── gates/          # Quality gates (YAML)
├── pools/          # Worker pools (YAML)
└── memory/         # Agent memory (JSON)
```

---

## Commit Guidelines

### Message Format

```
<type>: <brief description>

<detailed explanation of changes>
<list of files changed and why>
```

### Types

| Type | Use Case |
|------|----------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code restructuring |
| `docs` | Documentation only |
| `test` | Adding tests |
| `infra` | Infrastructure changes |

### Examples

```
feat: Add VP agent class with delegation logic

Implement VPAgent for department leadership:
- Handles delegations from COO
- Breaks down work for directors
- Manages quality gates
- Handles escalations

Files: src/agents/vp.py, src/agents/__init__.py
```

---

## Testing Requirements

### Syntax Verification

```bash
python3 -c "
import ast
for f in ['file1.py', 'file2.py']:
    ast.parse(open(f).read())
    print(f'OK: {f}')
"
```

### Import Testing

```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from src.agents import VPAgent, DirectorAgent
from src.core import LLMBackend, MessageProcessor
print('All imports successful')
"
```

### Integration Testing

```bash
python3 -c "
# Create temp corp, instantiate agents, verify they work together
from src.agents import CorporationExecutor
corp = CorporationExecutor(temp_path)
corp.initialize()
# Verify status
"
```

---

## Code Style

### Classes

```python
@dataclass
class ExampleClass:
    """One-line description.

    Longer description if needed.
    """
    required_field: str
    optional_field: Optional[str] = None
    list_field: List[str] = field(default_factory=list)

    def public_method(self, arg: str) -> Dict[str, Any]:
        """Description of what this does."""
        pass

    def _private_method(self) -> None:
        """Internal use only."""
        pass
```

### Modules

```python
"""
Module Name - Brief Description

Longer description of what this module provides.
"""

import logging
from typing import ...
from dataclasses import dataclass

from ..core.dependency import Thing

logger = logging.getLogger(__name__)

# Constants
DEFAULT_VALUE = "value"

# Classes
@dataclass
class MainClass:
    ...

# Factory functions
def create_thing(...) -> MainClass:
    ...
```

### Exports

```python
# __init__.py
from .module import Class1, Class2, function1

__all__ = [
    'Class1', 'Class2', 'function1'
]
```

---

## Agent Development

### Creating New Agent Types

1. Inherit from `BaseAgent`
2. Implement `process_work(work_item) -> Dict`
3. Use `self.llm` for LLM operations
4. Use `self.message_processor` for messages
5. Add to `src/agents/__init__.py`

### Agent Capabilities

| Method | Purpose |
|--------|---------|
| `think(task, context)` | Structured reasoning |
| `execute_with_llm(task)` | Execute with Claude |
| `analyze_work_item(item)` | Analyze before processing |
| `checkpoint(desc, data)` | Crash recovery point |
| `delegate_to(...)` | Assign to subordinate |
| `store_context(...)` | Memory storage |

---

## LLM Backend Development

### Adding New Backends

1. Inherit from `LLMBackend`
2. Implement `execute(request) -> LLMResponse`
3. Implement `is_available() -> bool`
4. Register in `LLMBackendFactory`

### Backend Selection

```python
# Auto-select best available
backend = LLMBackendFactory.get_best_available()

# Explicit selection
backend = LLMBackendFactory.create('claude_code')
backend = LLMBackendFactory.create('claude_api')
backend = LLMBackendFactory.create('mock')
```

---

## State Management

### Always Update STATE.md

After any significant change:
1. Update "Last Updated" timestamp
2. Add entry to "Recent Changes"
3. Update component status if changed
4. Update any relevant metrics

### Always Update Architecture Doc

After architectural changes:
1. Update implementation status table
2. Update project structure if files added
3. Update agent architecture if agents changed
4. Update next steps if priorities shift

---

## Error Handling

### Logging

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Detailed info for debugging")
logger.info("Normal operation info")
logger.warning("Something unexpected but handled")
logger.error("Error occurred, operation failed")
```

### Exceptions

```python
# Catch specific exceptions
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    return {'status': 'failed', 'error': str(e)}

# Never catch bare Exception except at top level
```

---

## Security Considerations

1. **No secrets in code** - Use environment variables
2. **Validate inputs** - Especially from external sources
3. **Sanitize paths** - Prevent directory traversal
4. **Review LLM outputs** - Don't blindly execute

---

## Questions?

- Check `AI_CORP_ARCHITECTURE.md` for system design
- Check `STATE.md` for current status
- Check existing code for patterns
