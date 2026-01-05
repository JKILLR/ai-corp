# Claude Code Skills System - Comprehensive Research Report

**Date**: 2026-01-04
**Researcher**: Research Specialist Agent

---

## Executive Summary

Claude Code Skills are reusable, filesystem-based resources that provide Claude with domain-specific expertise. They transform general-purpose agents into specialists by providing workflows, context, and best practices. Skills are model-invoked, meaning Claude automatically selects and applies relevant skills based on the user's request without explicit invocation.

---

## 1. How Skills Work

### Architecture Overview

Skills employ a **progressive disclosure architecture** to minimize context window usage:

1. **Discovery Phase** (~100 tokens): Claude scans all installed skill metadata (name/description)
2. **Invocation Phase** (<5k tokens): When relevant, Claude reads the full SKILL.md body
3. **Resource Loading** (as needed): Additional bundled resources load only when required

### Model-Invoked Selection

There is **no algorithmic routing or intent classification**. The system:
- Formats all available skills into a text description embedded in the Skill tool's prompt
- Lets Claude's language model make the selection decision
- Injects skill instructions as new user messages into the conversation context
- Modifies execution context (allowed tools, model selection) as needed

### Skill Location Scanning

Claude Code scans these locations for skills:
- `~/.config/claude/skills/` (user settings)
- `.claude/skills/` (project settings)
- Plugin-provided skills
- Built-in Anthropic skills

---

## 2. SKILL.md Format Structure

### Required Structure

```yaml
---
name: skill-name
description: Brief description of what the skill does. Use when [trigger conditions].
---

# Skill Title

## Instructions
[Markdown content with detailed instructions]
```

### YAML Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Max 64 chars, lowercase letters/numbers/hyphens only |
| `description` | Yes | Max 1024 chars, describes purpose and trigger conditions |
| `allowed-tools` | No | Limit which tools Claude can use (e.g., `Read, Grep, Glob`) |

### Directory Structure

```
my-skill/
├── SKILL.md          # Core prompt and instructions (required)
├── scripts/          # Executable Python/Bash scripts
├── references/       # Documentation loaded into context
└── assets/           # Templates and binary files
```

### Best Practices

- Keep SKILL.md body under 500 lines for optimal performance
- Include all "when to use" information in the description (not body)
- Use progressive disclosure for large content
- Avoid tabs; use spaces for YAML indentation

---

## 3. Official Anthropic Skills

### Document Skills (Production-Ready)

| Skill | Description |
|-------|-------------|
| **docx** | Create, edit, analyze Word documents with tracked changes, comments, formatting preservation |
| **pdf** | PDF manipulation: extract text/tables, create, merge/split documents, handle forms |
| **pptx** | PowerPoint presentations with layouts, templates, charts, automated slide generation |
| **xlsx** | Excel spreadsheets with formulas, formatting, data analysis, visualization |

### Design & Creative Skills

| Skill | Description |
|-------|-------------|
| **frontend-design** | Creates distinctive, production-grade frontend interfaces avoiding generic AI aesthetics |
| **canvas-design** | Design visual art in PNG/PDF formats using design philosophies |
| **artifacts-builder** | Build complex HTML artifacts using React, Tailwind CSS, shadcn/ui |
| **algorithmic-art** | Generative art with p5.js: seeded randomness, flow fields, particle systems |
| **slack-gif-creator** | Create animated GIFs optimized for Slack's size constraints |

### Technical Skills

| Skill | Description |
|-------|-------------|
| **skill-creator** | Meta-skill for creating new Claude skills |
| **mcp-server** | Guide for creating high-quality MCP servers for API integration |
| **webapp-testing** | Test web applications using Playwright for UI verification |

### Enterprise Skills

| Skill | Description |
|-------|-------------|
| **brand-guidelines** | Apply brand colors and typography to artifacts |
| **internal-comms** | Write internal communications: status reports, newsletters, FAQs |

---

## 4. Frontend/UI Design Skills (Detailed)

### frontend-design Skill

**Purpose**: Creates distinctive, production-grade frontend interfaces with high design quality that avoids generic "AI slop" aesthetics.

**Key Design Principles**:

1. **Typography**
   - Choose beautiful, unique fonts
   - Avoid generic fonts (Arial, Inter)
   - Pair distinctive display fonts with refined body fonts

2. **Color & Theme**
   - Commit to cohesive aesthetic using CSS variables
   - Dominant colors with sharp accents
   - Avoid timid, evenly-distributed palettes

3. **Motion**
   - Use animations for effects and micro-interactions
   - Prioritize CSS-only solutions for HTML
   - Use Motion library for React
   - Focus on high-impact moments (staggered page load reveals)

**Why It Exists**: Without direction, Claude samples from "safe" design choices due to distributional convergence in training data. This skill provides direction to break from generic patterns.

### Related Frontend Skills

| Skill | Focus |
|-------|-------|
| **artifacts-builder** | React, Tailwind CSS, shadcn/ui components |
| **web-artifacts-builder** | Multi-component HTML artifacts |
| **frontend-designer** | ReactJS, NextJS, TypeScript, Tailwind CSS |

---

## 5. Specialized Skills by Department

### Security Department

| Skill | Description |
|-------|-------------|
| **security-bluebook-builder** | Build security Blue Book for sensitive apps (threat model, auth, logging, IR) |
| **defense-in-depth** | Multi-layered security approaches |
| **varlock-claude-skill** | Secure environment variable management, prevent secret exposure |

### DevOps & Infrastructure

| Skill | Description |
|-------|-------------|
| **aws-skills** | AWS CDK best practices, cost optimization, serverless patterns |
| **terraform-skills** | Infrastructure as Code with Terraform/Terragrunt |
| **git-pushing** | Automate git operations |
| **ci-cd-automation** | Generate/troubleshoot CI/CD pipeline configurations |

### Testing & QA

| Skill | Description |
|-------|-------------|
| **webapp-testing** | Playwright-based UI testing from natural language |
| **api-tester** | Test REST APIs, validate responses |
| **test-fixing** | Detect failing tests, propose patches/fixes |
| **pypict-claude-skill** | Design test cases using PICT for pairwise coverage |

### Data & Analytics

| Skill | Description |
|-------|-------------|
| **xlsx** | Excel data analysis and visualization |
| **data-analysis** | Domain-specific data analysis workflows |
| **log-analysis** | Analyze logs, diagnose issues |

### Research & Documentation

| Skill | Description |
|-------|-------------|
| **claude-scientific-skills** | 125+ scientific skills (bioinformatics, cheminformatics, ML) |
| **revealjs-skill** | Generate Reveal.js presentations |
| **internal-comms** | Status reports, newsletters, documentation |

---

## 6. Community Resources

### Awesome Claude Skills Repositories

1. **travisvn/awesome-claude-skills** - Curated list with tools for customizing AI workflows
2. **BehiSecc/awesome-claude-skills** - 4.1k+ stars, categorized collection
3. **VoltAgent/awesome-claude-skills** - Collection with resources
4. **ComposioHQ/awesome-claude-skills** - Integration with 500+ apps via Composio
5. **alirezarezvani/claude-skills** - Real-world usage collection including subagents

### Skill Categories in Community Repos

- Research, Learning & Problem Solving
- Knowledge Management
- Writing & Documentation
- Presentation & Reporting
- Media & YouTube
- Data Skills
- Finance & Invoicing
- Development/Debugging/Testing/Coding
- Agent Skills
- Meeting & Collaboration

---

## 7. Creating Custom Skills

### When to Create a Skill

"If you find yourself typing the same prompt repeatedly across multiple conversations, it's time to create a Skill."

### Creation Process

1. Create a directory with your skill name
2. Add a SKILL.md file with proper frontmatter
3. Include instructions in markdown format
4. Optionally add scripts/, references/, assets/ directories
5. Install to `~/.config/claude/skills/` or `.claude/skills/`

### Tool Restriction Example

```yaml
---
name: reading-files-safely
description: Read-only file access skill
allowed-tools: Read, Grep, Glob
---
```

---

## 8. Open Standard

As of December 18, 2025, Agent Skills has been published as an **open standard** at agentskills.io. This means:
- Skills are portable across AI platforms
- Same skill format works across tools that adopt the standard
- Not locked to Claude ecosystem

---

## 9. Availability & Requirements

| Plan | Access |
|------|--------|
| Claude Pro | Skills available |
| Claude Max | Skills available |
| Claude Team | Skills available |
| Claude Enterprise | Skills available |
| Claude API | Skills available (code execution tool) |
| Claude Code | Skills available (beta) |

**Requirements**: Code execution must be enabled

**Cost**: No additional costs for official skills beyond subscription. Community/custom skills are free, though may require external services with their own costs.

---

## 10. Key Sources

- [Agent Skills - Claude Code Docs](https://code.claude.com/docs/en/skills)
- [GitHub - anthropics/skills](https://github.com/anthropics/skills)
- [Anthropic Engineering Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Claude Help Center - What are Skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [GitHub - travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills)
- [Inside Claude Code Skills - Mikhail Shilkov](https://mikhail.io/2025/10/claude-code-skills/)
- [Claude Agent Skills Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [claude-plugins.dev/skills](https://claude-plugins.dev/skills)

---

## 11. Recommendations for Agent Departments

### For Implementation Agents
- Install **frontend-design** skill for UI work
- Use **webapp-testing** for automated testing
- Consider **api-tester** for backend validation

### For Research Agents
- **claude-scientific-skills** for technical research
- Document skills (pdf, docx) for report generation

### For Operations/DevOps Agents
- **aws-skills** for cloud infrastructure
- **terraform-skills** for IaC
- **git-pushing** for automation

### For Security Agents
- **security-bluebook-builder** for security documentation
- **defense-in-depth** for layered security
- **varlock-claude-skill** for secrets management

### For QA/Testing Agents
- **webapp-testing** with Playwright
- **test-fixing** for test maintenance
- **pypict-claude-skill** for test case design
