# AI Corp Ideas

> **Purpose:** Capture ideas for future brainstorming. NOT approved plans.
> **Rule:** Ideas here are just ideas. Move to ROADMAP.md only after discussion and approval.

---

## How to Use This File

**Adding ideas:**
- Add under the relevant category (or create a new one)
- Include a brief description
- Add context if helpful (why this might be useful)
- Date is optional but can help track when ideas emerged

**Promoting to roadmap:**
- Discuss the idea first
- If approved, move to ROADMAP.md under "Approved Plans"
- Remove from this file (or mark as "→ Promoted to ROADMAP")

---

## Architecture Ideas

| Idea | Description | Context |
|------|-------------|---------|
| **Local LLM Integration** | See detailed section below | Hardware-dependent, critical for scale |

### Local LLM Integration (Future - Hardware Dependent)

**Core Concept:** AI Corp runs its own local LLM models alongside Claude for cost optimization, context absorption, and specialized skills.

**Three Use Cases:**

1. **Cost Reduction via Knowledge Distillation**
   - Claude handles complex reasoning, local models handle routine tasks
   - Feedback loop: Claude validates → local model learns → reduces Claude calls
   - Target: 60-80% reduction in API costs for repetitive operations

2. **Context Sponge Models**
   - Train local models on large context datasets (codebase, docs, history)
   - Acts as persistent memory that survives context windows
   - Query local model for context retrieval instead of stuffing prompts

3. **Specialized Skill Models**
   - Fine-tune models on specific skill datasets:
     - Business analysis
     - Accounting/financial reasoning
     - Legal document review
     - Code review for specific languages
   - Workers use specialized models for their domain

**Integration Points:**
- `LLMBackendFactory` already supports swappable backends
- Could add `LocalModelBackend` alongside ClaudeCode/API/Mock
- WorkScheduler could route tasks to appropriate backend based on complexity
- Learning System could feed distilled knowledge to local training

**Tiered Model Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL MODEL HIERARCHY                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  COO Model (70-200B parameters)                             │
│  ├── Largest model for deepest understanding                │
│  ├── Trained on full corp context + history                 │
│  ├── Handles strategic reasoning, complex decisions         │
│  └── Single instance, always available                      │
│                                                             │
│  Worker Models (7-13B parameters each)                      │
│  ├── Smaller, specialized per skill/domain                  │
│  ├── Multiple can run in parallel                           │
│  ├── Examples:                                              │
│  │   ├── code-review-model (trained on PR feedback)        │
│  │   ├── business-analysis-model                           │
│  │   ├── frontend-specialist-model                         │
│  │   └── testing-specialist-model                          │
│  └── Learn what works/fails for their domain               │
│                                                             │
│  Overnight Training Cycle                                   │
│  ├── Collect day's data (successes, failures, patterns)    │
│  ├── Queue training jobs by priority                        │
│  ├── Fine-tune models on new data                          │
│  ├── Validate against test set                              │
│  └── Deploy updated models for next day                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Model Routing Logic:**
- Claude API: Complex novel tasks, critical decisions needing latest capabilities
- COO Local Model: Strategic planning, context-heavy decisions for this corp
- Worker Local Models: Routine domain-specific tasks, pattern matching
- Fallback: If local model confidence < threshold, escalate to Claude

**Overnight Training Pipeline:**
1. Evolution Daemon exports day's outcomes to training format
2. Data filtered by quality (successful patterns prioritized)
3. Each model trains on relevant subset (COO gets all, workers get domain-specific)
4. Validation run against held-out test cases
5. If validation passes, hot-swap models at session start
6. Failed training logged for human review

**Hardware Requirements:**
- COO Model: 80-160GB VRAM (2-4x A100 80GB or equivalent)
- Worker Models: 16-24GB VRAM each (RTX 4090 or A6000)
- Training: Additional GPU capacity for overnight fine-tuning
- Or: Cloud GPU cluster (RunPod, Lambda Labs, etc.)

**Dependencies:**
- Need LLM fine-tuning infrastructure (likely using Axolotl, Unsloth, or similar)
- Model serving (vLLM, TGI, Ollama)
- Training data pipeline from Learning System
- Model registry for version management

**When to Revisit:** When hardware is available and core system is generating revenue

---

## Agent Ideas

| Idea | Description | Context |
|------|-------------|---------|
| - | - | - |

---

## Learning System Ideas

| Idea | Description | Context |
|------|-------------|---------|
| - | - | - |

---

## Integration Ideas

| Idea | Description | Context |
|------|-------------|---------|
| - | - | - |

---

## Business/Product Ideas

| Idea | Description | Context |
|------|-------------|---------|
| - | - | - |

---

## Tooling Ideas

| Idea | Description | Context |
|------|-------------|---------|
| - | - | - |

---

## Random/Uncategorized

| Idea | Description | Context |
|------|-------------|---------|
| - | - | - |

---

## Rejected Ideas (with reasons)

Keep track of why ideas were rejected to avoid revisiting them.

| Idea | Reason Rejected | Date |
|------|-----------------|------|
| 6 new Operations Agent types | Over-engineering - use existing agents with configs | 2026-01-09 |
| Separate orchestration layer | Molecules already handle this | 2026-01-09 |
| Context Selector system | Depth-Based Context already does this | 2026-01-09 |

