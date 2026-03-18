# Foundation Corp

**The corp that builds AI Corp.**

Foundation Corp is a special AI Corp instance with privileged access to modify the platform itself. It uses AI Corp's own systems (molecules, gates, beads) to manage platform development.

> **Important:** See [DOGFOODING.md](./DOGFOODING.md) for the safe code editing workflow.

## Workspace

Foundation Corp works in an **isolated git worktree** to prevent live code corruption:

```
/home/user/ai-corp/              <- Human CEO workspace (main)
/home/user/ai-corp-foundation/   <- Foundation Corp workspace (foundation/*)
```

## Current Phase: 2 (Assisted)

- Human CEO approves all changes before release
- Foundation proposes, human approves
- Building trust through successful molecules

## Structure

```
foundation/
├── org/                    # Organizational structure
│   ├── hierarchy.yaml      # Reporting structure
│   ├── departments/        # Engineering, Research, Quality
│   └── roles/              # COO, VPs, Directors, Workers
├── hooks/                  # Work queues for agents
├── molecules/              # Workflows
│   ├── active/             # Currently running
│   ├── completed/          # Finished work
│   └── templates/          # Reusable templates
├── beads/                  # State persistence (git-backed)
├── gates/                  # Quality gates configuration
├── contracts/              # Success contracts
├── channels/               # Inter-agent communication
└── learning/               # Learning system data
```

## Departments

### Engineering
- **Core Engine Team**: Molecule, Hook, Bead, Channel, Gate, Memory
- **Platform Team**: Apex, Personal, Core Services
- **Integrations Team**: Entity Graph, File Storage, Connectors

### Research
- **Architecture Team**: Design, API design, architectural decisions
- **Analysis Team**: Performance, optimization, metrics

### Quality
- **Testing Team**: Test coverage, integration testing
- **Security Team**: Security review, access control, audit

## Gates

| Gate | Stage | Required For | Approvers |
|------|-------|--------------|-----------|
| Design Review | Design | New features, refactors | VP Engineering + CEO |
| QA Review | QA | All changes | Dir Testing |
| Security Review | Security | Auth, data, secrets | Dir Security |
| Release Gate | Release | All changes | VP Quality + CEO |

## Molecule Templates

- `core-feature.yaml` - New Core Engine functionality
- `bug-fix.yaml` - Bug fixes
- `learning-system.yaml` - Learning System components

## Privileges

Foundation Corp has special access that no other corp has:
- Modify Core Engine (`src/core/`)
- Modify Platform Services (`src/platform/`)
- Create and validate presets (`presets/`)
- Access all corps for debugging/support

## Phase Progression

| Phase | Human Role | Foundation Autonomy | Trigger |
|-------|------------|---------------------|---------|
| 1: Bootstrap | Does everything | Structure only | Corp exists |
| **2: Assisted** | Approves all | Proposes changes | Current |
| 3: Supervised | Approves releases | Autonomous dev | 10+ molecules |
| 4: Trusted | Strategic direction | Minor releases | 50+ molecules |
| 5: Autonomous | Board oversight | Full autonomy | Trust earned |

## Getting Started

### Run a molecule

```bash
# COO analyzes task and creates molecule
ai-corp foundation molecule create --template core-feature \
  --name "Async Gate Approvals" \
  --var feature_name="async_approvals" \
  --var target_files="src/core/gate.py"

# View active molecules
ai-corp foundation molecules list

# View molecule status
ai-corp foundation molecule show MOL-XXXXXXXX
```

### Approve a gate

```bash
# List pending approvals
ai-corp foundation gates pending

# Approve a gate submission
ai-corp foundation gate approve GATE-XXXXXXXX --comment "Looks good"
```

## Metrics

Track Foundation Corp performance:
- Molecules completed
- Average cycle time
- Gate pass rate
- Bugs introduced
- Test coverage maintained
