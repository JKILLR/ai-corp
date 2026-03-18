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

### Local LLM Integration + Wisdom Store (Future - Hardware Dependent)

**Core Concept:** AI Corp runs its own local LLM models alongside Claude for cost optimization, context absorption, and specialized skills—enabling the COO to have deep "wisdom" about large data corpuses without unlimited token spend.

**The Problem: Storage vs Wisdom**

Current memory system can *store* data efficiently, but there's a gap between:
- **Storage**: Holding documents, chunks, and metadata
- **Wisdom**: Deep understanding that informs decisions, sees patterns, connects concepts

For COO to have wisdom about websites, X posts, blogs, documents, papers, etc., we need:
1. Cost-efficient ingestion (can't send everything to Claude)
2. Semantic understanding (not just keyword search)
3. Synthesis capabilities (turn facts into insights)
4. Persistent knowledge that survives context windows

**Solution: Wisdom Store Architecture**

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WISDOM STORE PIPELINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. INGESTION LAYER                                                 │
│     ├── Web scraping (pages, X posts, blogs)                        │
│     ├── Document extraction (PDF, DOCX, papers)                     │
│     ├── Code/repo analysis                                          │
│     └── Cost: ~$0 (local processing)                                │
│                                                                     │
│  2. CHUNKING + EMBEDDING LAYER                                      │
│     ├── Smart chunking (semantic boundaries, not arbitrary)         │
│     ├── Local embedding models (all-MiniLM, BGE, etc.)              │
│     ├── Vector storage (ChromaDB, FAISS, pgvector)                  │
│     └── Cost: ~$0 (local models)                                    │
│                                                                     │
│  3. FACT EXTRACTION LAYER                                           │
│     ├── Local LLM extracts key facts from chunks                    │
│     ├── Structured output: entities, relationships, claims          │
│     ├── Knowledge graph construction                                │
│     └── Cost: Local compute only                                    │
│                                                                     │
│  4. SYNTHESIS LAYER                                                 │
│     ├── COO Model (70-200B) synthesizes facts into insights         │
│     ├── Identifies patterns, trends, implications                   │
│     ├── Generates "wisdom summaries" for quick access               │
│     └── Cost: Local GPU time                                        │
│                                                                     │
│  5. RETRIEVAL LAYER                                                 │
│     ├── Semantic search over embeddings                             │
│     ├── Knowledge graph queries                                     │
│     ├── Pre-computed wisdom summaries                               │
│     └── Only escalate to Claude for novel synthesis                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**What Claude Code SDK Already Provides:**

Some ingestion capabilities exist via Claude Code SDK tools:
- **PDF Reading**: `Read` tool can process PDFs directly (extracts text + visual content)
- **Web Fetching**: `WebFetch` tool retrieves and processes web content
- **Web Search**: `WebSearch` tool for real-time information

However, these are *per-request* operations that consume Claude tokens. The Wisdom Store approach uses these for initial ingestion, then local models for ongoing processing.

**What Needs Custom Implementation:**
- Embedding generation (local models like BGE, all-MiniLM-L6-v2)
- Vector storage and semantic search (ChromaDB, FAISS)
- Knowledge graph construction and querying
- Local LLM inference for fact extraction and synthesis
- Cost tracking for all operations

**Four Use Cases:**

1. **Cost Reduction via Knowledge Distillation**
   - Claude handles complex reasoning, local models handle routine tasks
   - Feedback loop: Claude validates → local model learns → reduces Claude calls
   - Target: 60-80% reduction in API costs for repetitive operations

2. **Context Sponge Models (Wisdom Store)**
   - Train local models on large context datasets (codebase, docs, history)
   - Acts as persistent memory that survives context windows
   - Query local model for context retrieval instead of stuffing prompts
   - Pre-compute wisdom summaries for common query patterns

3. **Specialized Skill Models**
   - Fine-tune models on specific skill datasets:
     - Business analysis
     - Accounting/financial reasoning
     - Legal document review
     - Code review for specific languages
   - Workers use specialized models for their domain

4. **Large-Scale Data Ingestion**
   - Ingest websites, X posts, blogs, documents, research papers
   - Process locally without per-token costs
   - Build knowledge graph of entities and relationships
   - COO queries synthesized wisdom, not raw documents

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
| **SimpleMem-Inspired Retrieval** | See detailed section below | Adaptive retrieval, token budgeting |

### SimpleMem-Inspired Adaptive Retrieval

**Source:** [SimpleMem: Efficient Lifelong Memory for LLM Agents](https://github.com/aiming-lab/SimpleMem) (Liu et al., 2025)

**Key Insights from SimpleMem:**

1. **Semantic Lossless Compression** - Transform raw dialogue into atomic, self-contained facts at write time
   - "He'll meet Bob tomorrow" → "Alice meets Bob at Starbucks on 2025-11-16T14:00:00"
   - Resolve coreferences and convert relative timestamps ONCE at ingestion
   - Query-time retrieval becomes cheap (no LLM needed)

2. **Three-Tier Indexing** - Parallel retrieval paths for different query types
   - Semantic: Dense embeddings (1024-dim) for conceptual similarity
   - Lexical: BM25-style keyword matching for exact terms
   - Symbolic: Metadata filtering (timestamps, entities, person IDs)

3. **Adaptive Retrieval Depth** - Dynamic k based on query complexity
   - Formula: `k_dyn = k_base × (1 + δ × C_q)` where C_q is query complexity
   - Simple queries → ~100 tokens, Complex queries → ~1000 tokens
   - Achieves 30x token reduction vs full-context methods

**What We Can Implement Now (No Local LLM Needed):**

| Feature | Implementation | Benefit |
|---------|----------------|---------|
| Query Complexity Scoring | Heuristic based on word count, entity count, question words | Route simple/complex queries differently |
| Adaptive Retrieval Depth | Upgrade `search_relevant()` to use dynamic max_results | Right amount of context per query |
| Token Budget Enforcement | Add token_budget param to search methods | Cost control, connects to Economic Metadata |

**What Needs Local LLM (Future):**
- Atomic fact extraction from raw text
- Write-time disambiguation (coreference resolution)
- Synthesis of facts into wisdom summaries

**Integration with Existing Systems:**
- `knowledge.py:search_relevant()` - Add adaptive depth
- `memory.py:search_all()` - Add token budget enforcement
- Molecule `actual_cost` field - Track token usage per retrieval

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

