# Foundation Corp Dogfooding Workflow

## Overview

Foundation Corp uses AI Corp to build AI Corp. To prevent live code corruption, Foundation agents work in an **isolated git worktree**.

## Directory Structure

```
/home/user/ai-corp/              <- YOUR workspace (main branch)
/home/user/ai-corp-foundation/   <- Foundation Corp's workspace (foundation/* branches)
```

## The Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOGFOODING WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Foundation Corp edits code                             │
│          └─> /home/user/ai-corp-foundation/                     │
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
