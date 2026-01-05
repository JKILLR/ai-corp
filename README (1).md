# AI Corp - Starter Files

This folder contains the initial architecture and research for the AI Corp project.

## Contents

```
ai-corp/
├── README.md                    # This file
├── docs/
│   └── AI_CORP_ARCHITECTURE.md  # Full system architecture design
└── research/
    └── claude-code-skills-research.md  # Claude Code skills research
```

## To Use

Copy this entire folder to your new `ai-corp` repo:

```bash
cp -r ai-corp/* /path/to/ai-corp/
cd /path/to/ai-corp
git add .
git commit -m "Initial architecture and research"
git push
```

## Key Concepts

- **5-level hierarchy**: CEO → COO → VP → Director → Worker
- **5 departments**: Engineering, Research, Product, Quality, Operations
- **Molecules**: Persistent workflows (inspired by Gastown)
- **Hooks**: Work queues for agents
- **Quality Gates**: Pipeline stages with approval checkpoints
- **RACI Model**: Clear accountability for every task

## Reusable from agent-swarm

When building, copy these from agent-swarm:
- `shared/agent_executor_pool.py` - Worker execution
- `shared/workspace_manager.py` - Workspace isolation
- `shared/execution_context.py` - Agent context
- `backend/websocket/connection_manager.py` - WebSocket handling
- `frontend/components/ActivityPanel.tsx` - Activity monitoring UI

## Next Steps

1. Set up project structure per architecture doc
2. Implement org hierarchy (departments, roles)
3. Build molecule engine for persistent workflows
4. Add hook system for work queues
5. Create quality gate enforcement
6. Install Claude Code skills per department
