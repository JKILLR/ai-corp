# AI Corp CLI Reference

Complete command reference for the AI Corp command-line interface.

## Quick Reference

| Command | Description |
|---------|-------------|
| `ai-corp init <industry>` | Initialize a new AI Corp |
| `ai-corp ceo <task>` | Submit a task as CEO |
| `ai-corp coo` | Start the COO orchestrator |
| `ai-corp status` | View system status |
| `ai-corp org` | View organization structure |
| `ai-corp hire` | Hire new agents |
| `ai-corp templates` | List industry templates |
| `ai-corp molecules` | Manage workflows |
| `ai-corp hooks` | Manage work queues |
| `ai-corp gates` | Manage quality gates |
| `ai-corp contracts` | Manage success contracts |
| `ai-corp knowledge` | Manage knowledge base |

---

## Initialization

### `ai-corp init`

Initialize a new AI Corp from an industry template.

```bash
ai-corp init <industry>
```

**Industries:**
- `software_agency` - Software development agency
- `research_lab` - Research laboratory
- `consulting` - Consulting firm
- `startup` - Tech startup

**Example:**
```bash
ai-corp init software_agency
```

---

## Task Management

### `ai-corp ceo`

Submit a task as CEO. This is the primary way to give work to the corporation.

```bash
ai-corp ceo <title> [options]
```

**Options:**
| Flag | Description |
|------|-------------|
| `-d, --description` | Detailed task description |
| `-p, --priority` | Priority: `P0_CRITICAL`, `P1_HIGH`, `P2_MEDIUM`, `P3_LOW` |
| `-s, --start` | Start the molecule immediately |
| `--discover` | Run discovery conversation to create Success Contract first |

**Examples:**
```bash
# Simple task
ai-corp ceo "Build user authentication"

# With description and priority
ai-corp ceo "Build user authentication" -d "OAuth2 with Google and GitHub" -p P1_HIGH

# Start immediately
ai-corp ceo "Fix login bug" --start

# With discovery conversation (recommended for complex tasks)
ai-corp ceo "Build analytics dashboard" --discover --start
```

### `ai-corp coo`

Start the COO orchestrator to manage ongoing work.

```bash
ai-corp coo [options]
```

**Options:**
| Flag | Description |
|------|-------------|
| `-i, --interactive` | Run in interactive mode |

---

## Status & Monitoring

### `ai-corp status`

View system status and health.

```bash
ai-corp status [options]
```

**Options:**
| Flag | Description |
|------|-------------|
| `-r, --report` | Generate full report |
| `--health` | Show health monitoring with alerts |

**Examples:**
```bash
# Quick status
ai-corp status

# Full report
ai-corp status --report

# Health monitoring (shows agents, alerts, metrics)
ai-corp status --health
```

### `ai-corp org`

View organization structure.

```bash
ai-corp org [options]
```

**Options:**
| Flag | Description |
|------|-------------|
| `-c, --chart` | Show org chart visualization |

---

## Molecules (Workflows)

### `ai-corp molecules`

Manage persistent workflows.

```bash
ai-corp molecules <action> [molecule_id]
```

**Actions:**
| Action | Description |
|--------|-------------|
| `list` | List all molecules |
| `show <id>` | Show details of a molecule |

**Examples:**
```bash
ai-corp molecules list
ai-corp molecules show mol-abc12345
```

---

## Hooks (Work Queues)

### `ai-corp hooks`

Manage agent work queues.

```bash
ai-corp hooks <action> [hook_id]
```

**Actions:**
| Action | Description |
|--------|-------------|
| `list` | List all hooks |
| `show <id>` | Show hook details and work items |

**Examples:**
```bash
ai-corp hooks list
ai-corp hooks show vp-engineering-hook
```

---

## Gates (Quality Checkpoints)

### `ai-corp gates`

Manage quality gates.

```bash
ai-corp gates <action> [gate_id]
```

**Actions:**
| Action | Description |
|--------|-------------|
| `list` | List all gates |
| `show <id>` | Show gate details |

**Examples:**
```bash
ai-corp gates list
ai-corp gates show design-review-gate
```

---

## Success Contracts

### `ai-corp contracts`

Manage success contracts that define measurable outcomes.

```bash
ai-corp contracts <action> [contract_id] [options]
```

**Actions:**
| Action | Description |
|--------|-------------|
| `list` | List all contracts |
| `show <id>` | Show contract details |
| `create` | Create a new contract |
| `check <id>` | Mark a criterion as met |
| `link <id>` | Link contract to a molecule |
| `activate <id>` | Activate a draft contract |

**Options for `list`:**
| Flag | Description |
|------|-------------|
| `--status` | Filter: `draft`, `active`, `completed`, `failed`, `amended` |

**Options for `create`:**
| Flag | Description |
|------|-------------|
| `--title` | Contract title |
| `--objective` | Contract objective |
| `--criteria` | Success criteria (separated by `;`) |
| `--in-scope` | In scope items (separated by `;`) |
| `--out-of-scope` | Out of scope items (separated by `;`) |
| `--constraints` | Constraints (separated by `;`) |
| `--created-by` | Creator ID |

**Options for `check`:**
| Flag | Description |
|------|-------------|
| `--index` | Criterion index to mark as met |
| `--verifier` | Verifier ID |

**Options for `link`:**
| Flag | Description |
|------|-------------|
| `--molecule` | Molecule ID to link |

**Examples:**
```bash
# List active contracts
ai-corp contracts list --status active

# Show contract details
ai-corp contracts show contract-abc123

# Create a contract
ai-corp contracts create \
  --title "User Auth Feature" \
  --objective "Implement secure user authentication" \
  --criteria "OAuth2 login works;Password reset works;MFA optional" \
  --in-scope "Login;Logout;Password reset" \
  --out-of-scope "Admin portal;User management"

# Mark criterion as met
ai-corp contracts check contract-abc123 --index 0 --verifier qa-lead

# Link to molecule
ai-corp contracts link contract-abc123 --molecule mol-xyz789

# Activate draft contract
ai-corp contracts activate contract-abc123
```

---

## Knowledge Base

### `ai-corp knowledge`

Manage the knowledge base for documents, context, and reference material.

```bash
ai-corp knowledge <action> [entry_id] [options]
```

**Actions:**
| Action | Description |
|--------|-------------|
| `list` | List knowledge entries |
| `show <id>` | Show entry details |
| `add` | Add new knowledge (file, URL, or note) |
| `search` | Search the knowledge base |
| `stats` | Show statistics |
| `remove <id>` | Remove an entry |

**Scope Options (for `add`):**
| Flag | Description |
|------|-------------|
| `--foundation` | Add to foundation (corp-wide) scope |
| `--project <molecule_id>` | Add to project scope |
| `--task <work_item_id>` | Add to task scope |

**Content Options (for `add`):**
| Flag | Description |
|------|-------------|
| `--file <path>` | File to add |
| `--url <url>` | URL reference to add |
| `--note <text>` | Text note to add |

**Metadata Options (for `add`):**
| Flag | Description |
|------|-------------|
| `--name` | Display name |
| `--description` | Description |
| `--tags` | Comma-separated tags |
| `--uploaded-by` | Uploader identifier |

**Other Options:**
| Flag | Description |
|------|-------------|
| `--scope` | Filter by scope: `foundation`, `project`, `task` |
| `-q, --query` | Search query (for `search` action) |

**Examples:**
```bash
# List all knowledge
ai-corp knowledge list

# List foundation knowledge only
ai-corp knowledge list --scope foundation

# Show entry details
ai-corp knowledge show know-abc12345

# Add file to foundation (corp-wide)
ai-corp knowledge add --file ./company_handbook.pdf --foundation --tags "reference,onboarding"

# Add file to a project
ai-corp knowledge add --file ./api_spec.md --project mol-abc123 --name "API Specification"

# Add file to a task
ai-corp knowledge add --file ./screenshot.png --task work-xyz789

# Add URL reference
ai-corp knowledge add --url https://docs.example.com --foundation --name "External Docs"

# Add a note
ai-corp knowledge add --note "Remember: API rate limit is 100 requests/min" --project mol-abc123

# Search knowledge base
ai-corp knowledge search -q "authentication"

# View statistics
ai-corp knowledge stats

# Remove entry
ai-corp knowledge remove know-abc12345
```

**Knowledge Scopes:**

| Scope | Description | Use Case |
|-------|-------------|----------|
| Foundation | Corp-wide | Company handbook, tech stack docs, coding standards |
| Project | Molecule-scoped | Project requirements, specs, mockups |
| Task | Work item-scoped | Bug screenshots, specific references |

---

## Hiring

### `ai-corp hire`

Hire new agents into the organization.

```bash
ai-corp hire <role_type> [options]
```

**Role Types:**
- `vp` - Vice President
- `director` - Director
- `worker` - Worker

**Options:**
| Flag | Description |
|------|-------------|
| `--role-id` | Unique role ID |
| `--name` | Display name |
| `--department` | Department |
| `--reports-to` | Manager role ID (directors) |
| `--pool` | Worker pool (workers) |
| `--director` | Director role ID (workers) |
| `--focus` | Role focus area |
| `--description` | Role description |
| `--capabilities` | Comma-separated capabilities |
| `--responsibilities` | Comma-separated responsibilities |
| `--skills` | Comma-separated Claude Code skills |

**Examples:**
```bash
# Hire a VP
ai-corp hire vp \
  --role-id vp-data \
  --name "VP of Data" \
  --department data \
  --responsibilities "Lead data team,Set data strategy"

# Hire a Director
ai-corp hire director \
  --role-id dir-ml \
  --name "ML Director" \
  --department engineering \
  --reports-to vp-engineering \
  --focus "Machine Learning"

# Hire a Worker
ai-corp hire worker \
  --role-id worker-ml-1 \
  --name "ML Engineer 1" \
  --department engineering \
  --pool ml-pool \
  --director dir-ml \
  --capabilities "pytorch,tensorflow"
```

---

## Templates

### `ai-corp templates`

List and view industry templates.

```bash
ai-corp templates <action> [template_name]
```

**Actions:**
| Action | Description |
|--------|-------------|
| `list` | List available templates |
| `show <name>` | Show template details |

**Examples:**
```bash
ai-corp templates list
ai-corp templates show software_agency
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_CORP_PATH` | Path to corp data directory | `./corp` |

---

## Common Workflows

### Starting a New Project

```bash
# 1. Initialize (if not already done)
ai-corp init software_agency

# 2. Add foundation knowledge
ai-corp knowledge add --file ./company_standards.md --foundation

# 3. Submit task with discovery
ai-corp ceo "Build customer portal" --discover --start

# 4. Add project-specific docs
ai-corp knowledge add --file ./portal_requirements.pdf --project mol-<id>

# 5. Monitor progress
ai-corp status --health
ai-corp molecules show mol-<id>
```

### Checking System Health

```bash
# Quick overview
ai-corp status

# Detailed health with alerts
ai-corp status --health

# Check specific areas
ai-corp molecules list
ai-corp hooks list
ai-corp contracts list --status active
```

### Managing Knowledge

```bash
# See what's in the knowledge base
ai-corp knowledge stats
ai-corp knowledge list

# Search for specific info
ai-corp knowledge search -q "api authentication"

# Add reference material
ai-corp knowledge add --file ./docs/api.md --foundation --tags "api,reference"
```
