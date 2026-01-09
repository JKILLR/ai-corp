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

**Hardware Requirements:**
- GPU with sufficient VRAM (RTX 4090, A100, etc.)
- Or cloud GPU instances (RunPod, Lambda Labs, etc.)

**Dependencies:**
- Need LLM fine-tuning infrastructure (likely using Axolotl, Unsloth, or similar)
- Model serving (vLLM, TGI, Ollama)
- Training data pipeline from Learning System

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

