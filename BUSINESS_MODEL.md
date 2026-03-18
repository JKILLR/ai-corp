# AI Corp Platform - Business Model

## Executive Summary

AI Corp is a platform for deploying autonomous AI workforces. The platform has three services:
- **APEX** - Multi-corp management for organizations
- **PERSONAL** - Individual AI assistant with deep context
- **FOUNDATION** - Self-development corp (internal)

Revenue comes from subscriptions (Personal Pro, Corp tiers) and usage-based pricing for high-volume customers. The primary cost driver is LLM API usage.

---

## Market Opportunity

### The Problem
- Organizations need AI automation but lack infrastructure to deploy it
- Individuals want AI assistants with persistent memory and context
- Current solutions are either too simple (chatbots) or require heavy engineering

### Our Solution
- Pre-built organizational structures that work autonomously
- Persistent memory, workflows, and quality gates
- Industry-specific presets (software, legal, creative, etc.)
- Personal assistant with relationship/context awareness

### Target Customers

| Segment | Description | Value Proposition |
|---------|-------------|-------------------|
| **Solo Founders** | 1-person companies wanting to scale | AI team without hiring |
| **Small Agencies** | 5-20 person shops | Multiply capacity 10x |
| **Enterprise Teams** | Departments within large orgs | Autonomous task execution |
| **Individual Professionals** | Executives, consultants, creatives | Personal AI with deep context |

---

## Revenue Model

### Personal Edition

| Tier | Price | Features | Target |
|------|-------|----------|--------|
| **Free** | $0/month | Basic Entity Graph (100 entities), manual entry only, single corp connection, 50 messages/day | Try before buy |
| **Pro** | $19/month | Unlimited entities, data connectors (Gmail, iMessage, Calendar), multi-corp dashboard, 500 messages/day | Power users |
| **Pro+** | $39/month | Everything in Pro + priority processing, advanced memory, API access, unlimited messages | Professionals |

### Corp Edition (APEX-Managed)

| Tier | Price | Features | Target |
|------|-------|----------|--------|
| **Starter** | $99/month | 1 department, 5 workers, 100 molecules/month, community support | Solo founders |
| **Business** | $299/month | 3 departments, 20 workers, 500 molecules/month, email support | Small teams |
| **Professional** | $599/month | 5 departments, 50 workers, 2000 molecules/month, priority support | Growing agencies |
| **Enterprise** | Custom | Unlimited, dedicated infrastructure, SLA, custom presets | Large organizations |

### Usage-Based Add-ons

| Add-on | Price | Description |
|--------|-------|-------------|
| Additional molecules | $0.50/molecule | Beyond tier limit |
| Additional workers | $10/worker/month | Beyond tier limit |
| Opus-tier tasks | $2/task | Complex reasoning requiring Opus |
| Data connectors | $5/connector/month | Additional integrations |
| Custom preset development | $2,000+ one-time | Industry-specific configuration |

---

## Cost Structure

### Primary Costs: LLM API Usage

| Model | Input Cost | Output Cost | Use Case | % of Calls |
|-------|------------|-------------|----------|------------|
| Haiku | $0.25/1M tokens | $1.25/1M tokens | Routing, classification, simple tasks | 20% |
| Sonnet | $3/1M tokens | $15/1M tokens | Most work, analysis, code generation | 75% |
| Opus | $15/1M tokens | $75/1M tokens | Architecture, complex debugging | 5% |

### Cost Per Operation (Estimates)

| Operation | Model | Tokens (in/out) | Cost |
|-----------|-------|-----------------|------|
| Message routing | Haiku | 500/100 | $0.0003 |
| COO task analysis | Sonnet | 3000/1500 | $0.03 |
| VP delegation | Sonnet | 2000/800 | $0.02 |
| Worker execution (simple) | Sonnet | 5000/2000 | $0.05 |
| Worker execution (complex) | Sonnet | 15000/8000 | $0.17 |
| Gate review | Sonnet | 2000/500 | $0.01 |
| Architecture decision | Opus | 5000/3000 | $0.30 |
| Entity extraction | Haiku | 1000/500 | $0.001 |
| Context generation | Sonnet | 2000/1000 | $0.02 |

### Cost Per Molecule (Typical 5-Step Workflow)

```
Molecule: "Build user authentication feature"

Step 1: COO Analysis                    $0.03
Step 2: VP Engineering Delegation       $0.02
Step 3: Research (2 workers)            $0.10
Step 4: Implementation (3 workers)      $0.45
Step 5: QA Review                       $0.05
Gate Reviews (2)                        $0.02
Message Routing (10)                    $0.003
─────────────────────────────────────────────
Total                                   $0.67
```

### Monthly Cost Per Tier (Estimated)

| Tier | Molecules | Est. API Cost | Price | Gross Margin |
|------|-----------|---------------|-------|--------------|
| Personal Free | ~30 equiv | $2 | $0 | -100% (loss leader) |
| Personal Pro | ~150 equiv | $8 | $19 | 58% |
| Corp Starter | 100 | $35 | $99 | 65% |
| Corp Business | 500 | $120 | $299 | 60% |
| Corp Professional | 2000 | $400 | $599 | 33% |
| Corp Enterprise | 5000+ | $1000+ | $2000+ | 50%+ |

### Secondary Costs

| Category | Estimate | Notes |
|----------|----------|-------|
| Infrastructure (compute, storage) | $500-2000/month | Scales with customers |
| Third-party services | $200-500/month | Auth, billing, monitoring |
| Support | Variable | Scale with customer base |
| Development | Internal (Foundation) | Uses own platform |

---

## Token Optimization Strategy

Critical for maintaining margins. This is a priority workstream for Foundation Corp.

### 1. Smart Model Routing (20-30% savings)

```python
# Route to cheapest capable model
def select_model(task_type, complexity):
    if task_type in ['routing', 'classification', 'simple_extraction']:
        return 'haiku'  # 12x cheaper than Sonnet
    elif complexity == 'high' or task_type in ['architecture', 'debugging']:
        return 'opus'   # Only when necessary
    else:
        return 'sonnet'  # Default workhorse
```

**Implementation:** Add `model_selector.py` to Core Engine, use task metadata to route.

### 2. Aggressive Caching (15-25% savings)

| Cache Type | TTL | Savings |
|------------|-----|---------|
| System prompts | Infinite | Avoid re-sending role context |
| Entity summaries | 1 hour | Reuse across conversations |
| Common patterns | 24 hours | Skip re-analysis of similar tasks |
| Tool results | 5 minutes | Avoid duplicate tool calls |

**Implementation:** Redis/local cache layer in Core Engine.

### 3. Context Compression (Already Built - 30-40% savings)

Our RLM-inspired memory system already provides:
- Lazy loading (don't load until needed)
- Peek/grep (partial context access)
- Hierarchical summaries (compressed views)
- Navigable compression (full access preserved)

### 4. Token-Efficient Prompts (10-15% savings)

| Before | After | Savings |
|--------|-------|---------|
| Long prose instructions | Structured bullet points | 40% |
| Inline documentation | Reference by ID | 60% |
| Full conversation history | Summarized context | 50% |

**Implementation:** Optimize all system prompts, create prompt library.

### 5. Batching Similar Tasks (10-20% savings)

```python
# Instead of 5 separate worker calls
for task in tasks:
    worker.execute(task)  # 5 API calls

# Batch into single call with multiple outputs
worker.execute_batch(tasks)  # 1 API call, 5 outputs
```

**Implementation:** Add batch execution mode to Worker agents.

### 6. Early Termination (5-10% savings)

- Stop generation when confidence is high
- Use structured output to avoid rambling
- Set appropriate max_tokens per operation type

### Optimization Roadmap

| Phase | Focus | Expected Savings | Timeline |
|-------|-------|------------------|----------|
| 1 | Smart model routing | 20% | Foundation Phase 2 |
| 2 | Caching layer | 15% | Foundation Phase 2 |
| 3 | Prompt optimization | 10% | Foundation Phase 3 |
| 4 | Batching | 10% | Foundation Phase 3 |
| 5 | Early termination | 5% | Foundation Phase 4 |

**Total potential savings: 40-50%** (some strategies overlap)

---

## Unit Economics

### Personal Pro User

```
Monthly Revenue:                 $19.00
├── API Cost (150 equiv mol)     ($8.00)
├── Infrastructure (allocated)   ($1.00)
├── Support (allocated)          ($0.50)
├── Payment processing (3%)      ($0.57)
└── ─────────────────────────────────────
Gross Profit:                    $8.93
Gross Margin:                    47%
```

### Corp Business Customer

```
Monthly Revenue:                 $299.00
├── API Cost (500 molecules)     ($120.00)
├── Infrastructure (allocated)   ($15.00)
├── Support (allocated)          ($10.00)
├── Payment processing (3%)      ($8.97)
└── ─────────────────────────────────────
Gross Profit:                    $145.03
Gross Margin:                    48%
```

### Blended Target Margins

| Metric | Target | Notes |
|--------|--------|-------|
| Gross Margin | 50%+ | After optimization |
| Net Margin | 20-30% | At scale |
| CAC Payback | < 3 months | For Pro/Business tiers |
| LTV:CAC | > 3:1 | Healthy SaaS ratio |

---

## Go-to-Market Strategy

### Phase 1: Foundation (Current)
- Build core platform
- Use internally (dogfooding)
- No external revenue

### Phase 2: Private Beta
- 10-20 hand-picked customers
- Corp Business tier only
- Focus on software companies (our expertise)
- Learn, iterate, optimize

### Phase 3: Public Beta
- Open Personal Free tier
- Open Corp Starter tier
- Content marketing, developer relations
- Build case studies from beta customers

### Phase 4: General Availability
- Full pricing in effect
- Enterprise sales motion
- Partner channel (agencies reselling)
- Marketplace for presets

### Customer Acquisition Channels

| Channel | Cost | Volume | Quality |
|---------|------|--------|---------|
| Organic/SEO | Low | Medium | High |
| Developer communities | Low | Low | Very High |
| Content marketing | Medium | Medium | High |
| Paid social | High | High | Medium |
| Enterprise sales | Very High | Low | Very High |

---

## Competitive Landscape

### Direct Competitors

| Competitor | Positioning | Our Differentiation |
|------------|-------------|---------------------|
| AutoGPT/AgentGPT | Open-source agents | Production-ready, organizational structure |
| Crew AI | Multi-agent framework | Full corp simulation, persistence, gates |
| LangChain/LangGraph | Developer tools | No-code/low-code, pre-built presets |
| Custom solutions | Enterprise builds | Faster deployment, industry templates |

### Indirect Competitors

| Category | Examples | Our Position |
|----------|----------|--------------|
| Task automation | Zapier, Make | More intelligent, handles ambiguity |
| Virtual assistants | ChatGPT, Claude | Persistent, organizational, autonomous |
| BPO/Outsourcing | Upwork, agencies | Faster, cheaper, 24/7, scalable |

### Competitive Moats

1. **Organizational abstraction** - Not just agents, but corps with hierarchy
2. **Persistence layer** - Molecules, beads, checkpoints (crash recovery)
3. **Quality gates** - Built-in QA, security review
4. **Memory system** - RLM-inspired context management
5. **Industry presets** - Fast deployment for specific verticals
6. **Personal + Corp integration** - Unified experience for CEOs

---

## Risk Analysis

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API costs exceed projections | Medium | High | Aggressive optimization, usage caps |
| Model quality regression | Low | High | Multi-provider support, fallbacks |
| Scaling bottlenecks | Medium | Medium | Early load testing, architecture review |
| Security vulnerabilities | Low | Very High | Security gates, audits, Foundation priority |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Slow customer adoption | Medium | High | Free tier, case studies, content marketing |
| Price competition | High | Medium | Value differentiation, not price war |
| Enterprise sales cycle | High | Medium | Focus on SMB first, build references |
| Churn | Medium | Medium | Sticky integrations, continuous value |

### Market Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM commoditization | Medium | Medium | Provider-agnostic, value in orchestration |
| Regulation | Low | High | Compliance features, audit trails |
| Economic downturn | Medium | Medium | Cost-savings positioning |

---

## Financial Projections (Illustrative)

### Year 1 (Beta + Launch)

| Metric | Q1 | Q2 | Q3 | Q4 |
|--------|----|----|----|----|
| Personal Free | 0 | 100 | 500 | 2,000 |
| Personal Pro | 0 | 10 | 50 | 200 |
| Corp Starter | 0 | 5 | 20 | 50 |
| Corp Business | 0 | 2 | 10 | 30 |
| MRR | $0 | $1,000 | $6,000 | $18,000 |

### Year 2 (Growth)

| Metric | Q1 | Q2 | Q3 | Q4 |
|--------|----|----|----|----|
| Personal Free | 5,000 | 10,000 | 20,000 | 40,000 |
| Personal Pro | 500 | 1,000 | 2,000 | 4,000 |
| Corp Starter | 100 | 200 | 350 | 500 |
| Corp Business | 50 | 100 | 175 | 250 |
| Corp Professional | 5 | 15 | 30 | 50 |
| MRR | $40,000 | $85,000 | $160,000 | $300,000 |

### Year 3 (Scale)

| Metric | Target |
|--------|--------|
| Personal Pro | 20,000+ |
| Corp customers | 2,000+ |
| ARR | $5M+ |
| Gross Margin | 55%+ |
| Team Size | 10-20 (mostly AI) |

---

## Key Metrics to Track

### Product Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| Molecules completed | Successful workflow completions | Growing |
| Success rate | Molecules completed / started | > 90% |
| Time to completion | Average molecule duration | Decreasing |
| Tokens per molecule | Efficiency metric | Decreasing |

### Business Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| MRR | Monthly recurring revenue | Growing 20%+ MoM |
| Churn | Monthly customer loss rate | < 5% |
| NPS | Net Promoter Score | > 50 |
| CAC | Customer acquisition cost | < 3 months revenue |
| LTV | Lifetime value | > 3x CAC |

### Operational Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| API cost ratio | API cost / revenue | < 40% |
| Uptime | Platform availability | > 99.5% |
| Support tickets | Per customer per month | < 1 |
| Time to resolution | Average ticket close time | < 24 hours |

---

## Open Questions

1. **Pricing validation** - Need customer interviews to validate willingness to pay
2. **Free tier limits** - What caps prevent abuse while allowing evaluation?
3. **Enterprise pricing** - Custom pricing model for large deployments
4. **Partner economics** - Revenue share for agencies reselling?
5. **Geographic pricing** - Different pricing for different regions?

---

## Next Steps

1. **Validate pricing** - Interview 10+ potential customers
2. **Build usage tracking** - Instrument token usage per operation
3. **Implement model routing** - Start with smart routing (Phase 1 optimization)
4. **Define free tier caps** - Balance evaluation vs abuse prevention
5. **Create sales materials** - Pitch deck, case study template

---

## Appendix: API Cost Trends

Historical Claude API pricing shows consistent decreases:

| Model | 2023 | 2024 | 2025 | Trend |
|-------|------|------|------|-------|
| Best available | $30/1M | $15/1M | $3/1M* | -80%/year |

*Sonnet-tier capability at dramatically lower cost

**Projection:** Expect continued 50%+ annual cost reduction, improving margins over time without price increases.

---

*Last updated: 2026-01-07*
