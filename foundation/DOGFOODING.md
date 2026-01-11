# Foundation Corp Dogfooding Workflow

## Overview

Foundation Corp uses AI Corp to build AI Corp. To prevent live code corruption, Foundation agents work in an **isolated git worktree**.

## Directory Structure

```
/home/user/ai-corp/              <- YOUR workspace (main branch)
/home/user/ai-corp-foundation/   <- Foundation Corp's workspace (foundation/* branches)
```

## Running Foundation Corp

### Option 1: Full Hierarchy Execution (Recommended)

Run the full agent chain via CLI:

```bash
cd /home/user/ai-corp-foundation
ai-corp ceo "Add timeout handling to gates" --discover --execute
```

This runs:
1. **Discovery conversation** - COO asks clarifying questions
2. **Contract + Molecule creation** - Structured success criteria
3. **Delegation** - COO → VP → Director → Worker
4. **Execution** - Workers execute with Claude CLI

For complex tasks, run multiple cycles:
```bash
ai-corp ceo "Refactor memory system" --discover --execute --cycles 3
```

### Option 2: Single Agent Mode

For simpler tasks, use Claude Code directly:

```bash
cd /home/user/ai-corp-foundation
claude
# Then give your task in the conversation
```

## The Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOGFOODING WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Foundation Corp executes task                          │
│          └─> ai-corp ceo "task" --discover --execute            │
│                                                                 │
│  Step 2: Foundation commits and pushes                          │
│          └─> git push origin foundation/feature-xyz             │
│                                                                 │
│  Step 3: Human CEO reviews PR on GitHub                         │
│          └─> Review changes, run tests                          │
│                                                                 │
│  Step 4: Merge to main (on GitHub)                              │
│          └─> Click "Merge" on PR                                │
│                                                                 │
│  Step 5: Human pulls to local                                   │
│          └─> cd /home/user/ai-corp && git pull                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Safety Guarantees

| Location | Who edits | Branch | Safe? |
|----------|-----------|--------|-------|
| `/home/user/ai-corp/` | Human CEO | main | ✅ Live, protected |
| `/home/user/ai-corp-foundation/` | Foundation Corp | foundation/* | ✅ Isolated |

Foundation's changes **never touch live code** until you explicitly pull after merging.

## For Foundation Corp Agents

When working on a task:

```bash
# 1. Start in the foundation worktree
cd /home/user/ai-corp-foundation

# 2. Create feature branch
git checkout -b foundation/fix-xyz

# 3. Make changes
# ... edit files ...

# 4. Commit
git add -A
git commit -m "fix: description of change"

# 5. Push
git push origin foundation/fix-xyz

# 6. Create PR
gh pr create --title "Fix XYZ" --body "Description of changes"
```

## For Human CEO

After Foundation creates a PR:

```bash
# 1. Review PR on GitHub
# 2. Merge when satisfied
# 3. Pull to your local:
cd /home/user/ai-corp
git pull origin main
```

## Configuration

Foundation Corp agents should have their working directory set to:
```
/home/user/ai-corp-foundation/
```

This is configured in the agent's `corp_path` or via environment variable:
```bash
export FOUNDATION_WORKSPACE=/home/user/ai-corp-foundation
```

## Worktree Management

```bash
# List worktrees
git worktree list

# Remove worktree (if needed)
git worktree remove /home/user/ai-corp-foundation

# Recreate worktree
git worktree add /home/user/ai-corp-foundation foundation/main
```
