"""
Memory System - RLM-Inspired Context Management

Inspired by Recursive Language Models (RLMs), this system treats context
as an external environment that agents can programmatically navigate
rather than loading everything into the context window.

Key concepts:
- Context Environment: Stores all context as queryable variables
- Memory REPL: Agents execute Python to peek, grep, and transform context
- Recursive Calls: Spawn sub-agents with focused context for sub-tasks
- Memory Buffers: Persistent accumulators that build up across turns
- Smart Summarization: On-demand summarization preserving full data access

References:
- arXiv:2512.24601 "Recursive Language Models"
- https://alexzhang13.github.io/blog/2025/rlm/
"""

import logging
import re
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import yaml


# =============================================================================
# SimpleMem-Inspired Adaptive Retrieval
# Reference: https://github.com/aiming-lab/SimpleMem
# =============================================================================

# Complexity scoring weights
_COMPLEXITY_QUESTION_WORDS = {'what', 'where', 'when', 'who', 'how', 'why', 'which'}
_COMPLEXITY_COMPARISON_WORDS = {'compare', 'difference', 'between', 'versus', 'vs', 'relationship'}
_COMPLEXITY_AGGREGATION_WORDS = {'all', 'every', 'across', 'throughout', 'summary', 'overview'}
_COMPLEXITY_TEMPORAL_WORDS = {'history', 'timeline', 'evolution', 'trend', 'over time', 'since', 'before', 'after'}

# Retrieval configuration
DEFAULT_BASE_K = 5  # Base number of results for simple queries
COMPLEXITY_SENSITIVITY = 0.5  # δ in SimpleMem formula
MAX_RETRIEVAL_DEPTH = 50  # Hard cap on results
TOKENS_PER_RESULT = 50  # Estimated tokens per knowledge entry


def score_query_complexity(query: str) -> float:
    """
    Score query complexity on a 0.0-1.0 scale.

    Inspired by SimpleMem's adaptive retrieval depth calculation.
    Simple queries get low scores, complex multi-hop queries get high scores.

    Args:
        query: The search query string

    Returns:
        Complexity score between 0.0 (trivial) and 1.0 (highly complex)
    """
    if not query:
        return 0.0

    query_lower = query.lower()
    words = query_lower.split()
    word_count = len(words)

    # Base complexity from length (normalized)
    length_score = min(word_count / 20, 0.3)  # Max 0.3 from length

    # Question word complexity
    question_score = 0.1 if any(w in _COMPLEXITY_QUESTION_WORDS for w in words) else 0.0

    # Multi-hop indicators (comparing, relating entities)
    comparison_score = 0.2 if any(w in query_lower for w in _COMPLEXITY_COMPARISON_WORDS) else 0.0

    # Aggregation queries (need more context)
    aggregation_score = 0.2 if any(w in query_lower for w in _COMPLEXITY_AGGREGATION_WORDS) else 0.0

    # Temporal queries (need historical context)
    temporal_score = 0.2 if any(w in query_lower for w in _COMPLEXITY_TEMPORAL_WORDS) else 0.0

    # Entity density (proper nouns suggest more specific retrieval)
    # Simple heuristic: count capitalized words (excluding first word)
    entity_count = sum(1 for w in words[1:] if w and w[0].isupper())
    entity_score = min(entity_count * 0.1, 0.3)

    total = length_score + question_score + comparison_score + aggregation_score + temporal_score + entity_score
    return min(total, 1.0)


def calculate_adaptive_depth(
    query: str,
    base_k: int = DEFAULT_BASE_K,
    sensitivity: float = COMPLEXITY_SENSITIVITY,
    token_budget: Optional[int] = None,
    max_depth: int = MAX_RETRIEVAL_DEPTH
) -> int:
    """
    Calculate adaptive retrieval depth based on query complexity.

    Implements SimpleMem formula: k_dyn = k_base × (1 + δ × C_q)

    Args:
        query: The search query
        base_k: Base number of results for simple queries
        sensitivity: Complexity sensitivity factor (δ)
        token_budget: Optional token budget to enforce
        max_depth: Maximum results regardless of complexity

    Returns:
        Number of results to retrieve
    """
    complexity = score_query_complexity(query)
    k_dyn = int(base_k * (1 + sensitivity * complexity))

    # Apply token budget constraint if specified
    if token_budget is not None:
        budget_limit = token_budget // TOKENS_PER_RESULT
        k_dyn = min(k_dyn, budget_limit)

    # Apply hard cap
    return max(1, min(k_dyn, max_depth))


def estimate_retrieval_tokens(num_results: int, tokens_per_result: int = TOKENS_PER_RESULT) -> int:
    """
    Estimate total tokens for a retrieval operation.

    Args:
        num_results: Number of results to retrieve
        tokens_per_result: Estimated tokens per result

    Returns:
        Estimated total tokens
    """
    return num_results * tokens_per_result


class ContextType(Enum):
    """Types of context that can be stored"""
    MOLECULE = "molecule"          # Workflow state and history
    BEAD = "bead"                  # Ledger entries
    MESSAGE = "message"            # Communication history
    ARTIFACT = "artifact"          # Files, code, documents
    CHECKPOINT = "checkpoint"      # Recovery points
    SUMMARY = "summary"            # Compressed context
    DECISION = "decision"          # Organizational decisions
    BUFFER = "buffer"              # Accumulated answers
    EXTERNAL = "external"          # External data sources
    # Entity Graph types
    ENTITY = "entity"              # Person, organization, project, etc.
    ENTITY_PROFILE = "entity_profile"  # Rich entity profile with context
    RELATIONSHIP = "relationship"  # Relationship between entities
    INTERACTION = "interaction"    # Email, message, meeting, etc.
    ENTITY_CONTEXT = "entity_context"  # Context package for conversation


@dataclass
class ContextVariable:
    """
    A variable in the context environment.

    Like RLM's REPL variables, these store context that can be
    queried, sliced, and transformed without loading everything.
    """
    id: str
    name: str
    context_type: ContextType
    size: int  # Size in characters/tokens (approximate)
    summary: str  # Brief description for navigation
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    # Lazy loading - content is loaded on demand
    _content_path: Optional[Path] = None
    _content_cache: Optional[Any] = None
    _is_loaded: bool = False

    @classmethod
    def create(
        cls,
        name: str,
        context_type: ContextType,
        content: Any,
        summary: str,
        content_path: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ContextVariable':
        """Create a new context variable"""
        now = datetime.utcnow().isoformat()
        content_str = json.dumps(content) if not isinstance(content, str) else content

        var = cls(
            id=f"ctx-{uuid.uuid4().hex[:8]}",
            name=name,
            context_type=context_type,
            size=len(content_str),
            summary=summary,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            _content_path=content_path
        )
        var._content_cache = content
        var._is_loaded = True
        return var

    def get_content(self) -> Any:
        """Get the full content (loads if needed)"""
        if not self._is_loaded and self._content_path:
            self._load_content()
        return self._content_cache

    def _load_content(self) -> None:
        """Load content from disk"""
        if self._content_path and self._content_path.exists():
            raw = self._content_path.read_text()
            if self._content_path.suffix in ('.yaml', '.yml'):
                self._content_cache = yaml.safe_load(raw)
            elif self._content_path.suffix == '.json':
                self._content_cache = json.loads(raw)
            else:
                self._content_cache = raw
            self._is_loaded = True

    def peek(self, start: int = 0, length: int = 500) -> str:
        """
        Peek at a portion of the content without loading everything.
        Like RLM's ability to inspect context segments.
        """
        content = self.get_content()
        if isinstance(content, str):
            return content[start:start + length]
        else:
            content_str = json.dumps(content, indent=2)
            return content_str[start:start + length]

    def grep(self, pattern: str, max_matches: int = 10) -> List[Dict[str, Any]]:
        """
        Search content using regex pattern.
        Like RLM's grep-based context filtering.
        """
        content = self.get_content()
        content_str = json.dumps(content, indent=2) if not isinstance(content, str) else content

        matches = []
        for i, line in enumerate(content_str.split('\n')):
            if re.search(pattern, line, re.IGNORECASE):
                matches.append({
                    'line_number': i + 1,
                    'content': line.strip(),
                    'context_before': content_str.split('\n')[max(0, i-1):i],
                    'context_after': content_str.split('\n')[i+1:min(i+2, len(content_str.split('\n')))]
                })
                if len(matches) >= max_matches:
                    break
        return matches

    def chunk(self, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """
        Split content into overlapping chunks for parallel processing.
        Like RLM's partition + map strategy.
        """
        content = self.get_content()
        content_str = json.dumps(content, indent=2) if not isinstance(content, str) else content

        chunks = []
        start = 0
        while start < len(content_str):
            end = min(start + chunk_size, len(content_str))
            chunks.append(content_str[start:end])
            start = end - overlap
            if start >= len(content_str):
                break
        return chunks

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'context_type': self.context_type.value,
            'size': self.size,
            'summary': self.summary,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class MemoryBuffer:
    """
    A persistent buffer for accumulating information.
    Like RLM's answer dictionary that builds up across turns.
    """
    id: str
    name: str
    purpose: str
    content: Dict[str, Any] = field(default_factory=dict)
    ready: bool = False
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def create(cls, name: str, purpose: str) -> 'MemoryBuffer':
        now = datetime.utcnow().isoformat()
        return cls(
            id=f"buf-{uuid.uuid4().hex[:8]}",
            name=name,
            purpose=purpose,
            created_at=now,
            updated_at=now
        )

    def set(self, key: str, value: Any) -> None:
        """Set a value in the buffer"""
        self.content[key] = value
        self.updated_at = datetime.utcnow().isoformat()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the buffer"""
        return self.content.get(key, default)

    def append(self, key: str, value: Any) -> None:
        """Append to a list in the buffer"""
        if key not in self.content:
            self.content[key] = []
        if isinstance(self.content[key], list):
            self.content[key].append(value)
        self.updated_at = datetime.utcnow().isoformat()

    def mark_ready(self) -> None:
        """Mark buffer as ready (answer complete)"""
        self.ready = True
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContextEnvironment:
    """
    The context environment that agents interact with.

    Inspired by RLM's REPL environment, this stores all context
    as variables that can be programmatically accessed without
    loading everything into the model's context window.
    """

    def __init__(self, corp_path: Path, agent_id: str):
        self.corp_path = Path(corp_path)
        self.agent_id = agent_id
        self.memory_path = self.corp_path / "memory"
        self.memory_path.mkdir(parents=True, exist_ok=True)

        # Context variables
        self.variables: Dict[str, ContextVariable] = {}

        # Memory buffers (like RLM's answer dict)
        self.buffers: Dict[str, MemoryBuffer] = {}

        # Index for fast lookups
        self.type_index: Dict[ContextType, List[str]] = {t: [] for t in ContextType}

        # Load persisted state
        self._load_state()

    def _load_state(self) -> None:
        """Load persisted environment state"""
        state_file = self.memory_path / f"{self.agent_id}_state.yaml"
        if state_file.exists():
            state = yaml.safe_load(state_file.read_text())
            for var_data in state.get('variables', []):
                var = ContextVariable(
                    id=var_data['id'],
                    name=var_data['name'],
                    context_type=ContextType(var_data['context_type']),
                    size=var_data['size'],
                    summary=var_data['summary'],
                    metadata=var_data.get('metadata', {}),
                    created_at=var_data.get('created_at', ''),
                    updated_at=var_data.get('updated_at', '')
                )
                # Set content path for lazy loading
                var._content_path = self.memory_path / f"var_{var.id}.json"
                self.variables[var.name] = var
                self.type_index[var.context_type].append(var.name)

            for buf_data in state.get('buffers', []):
                buf = MemoryBuffer(
                    id=buf_data['id'],
                    name=buf_data['name'],
                    purpose=buf_data['purpose'],
                    content=buf_data.get('content', {}),
                    ready=buf_data.get('ready', False),
                    created_at=buf_data.get('created_at', ''),
                    updated_at=buf_data.get('updated_at', '')
                )
                self.buffers[buf.name] = buf

    def _save_state(self) -> None:
        """Save environment state to disk"""
        state = {
            'agent_id': self.agent_id,
            'updated_at': datetime.utcnow().isoformat(),
            'variables': [v.to_dict() for v in self.variables.values()],
            'buffers': [b.to_dict() for b in self.buffers.values()]
        }
        state_file = self.memory_path / f"{self.agent_id}_state.yaml"
        state_file.write_text(yaml.dump(state, default_flow_style=False))

    def store(
        self,
        name: str,
        content: Any,
        context_type: ContextType,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextVariable:
        """
        Store content as a context variable.
        Content is persisted to disk for lazy loading.
        """
        # Create variable
        var = ContextVariable.create(
            name=name,
            context_type=context_type,
            content=content,
            summary=summary,
            metadata=metadata
        )

        # Persist content
        content_file = self.memory_path / f"var_{var.id}.json"
        content_file.write_text(json.dumps(content, indent=2, default=str))
        var._content_path = content_file

        # Store in environment
        self.variables[name] = var
        self.type_index[context_type].append(name)

        self._save_state()
        return var

    def get(self, name: str) -> Optional[ContextVariable]:
        """Get a context variable by name"""
        return self.variables.get(name)

    def list_variables(self, context_type: Optional[ContextType] = None) -> List[Dict[str, Any]]:
        """
        List available context variables.
        Returns summaries for navigation without loading content.
        """
        if context_type:
            names = self.type_index.get(context_type, [])
            return [
                {
                    'name': name,
                    'type': self.variables[name].context_type.value,
                    'size': self.variables[name].size,
                    'summary': self.variables[name].summary
                }
                for name in names
                if name in self.variables
            ]
        else:
            return [
                {
                    'name': v.name,
                    'type': v.context_type.value,
                    'size': v.size,
                    'summary': v.summary
                }
                for v in self.variables.values()
            ]

    def search_all(
        self,
        pattern: str,
        max_per_var: Optional[int] = None,
        token_budget: Optional[int] = None,
        adaptive: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all context variables with adaptive retrieval.

        Like RLM's grep capability across the environment, enhanced with
        SimpleMem-inspired adaptive depth calculation.

        Args:
            pattern: Regex pattern to search for
            max_per_var: Explicit max matches per variable (overrides adaptive)
            token_budget: Optional token budget for total retrieval
            adaptive: Whether to use adaptive depth (default True)

        Returns:
            Dict mapping variable names to list of matches
        """
        # Calculate retrieval depth
        if max_per_var is not None:
            limit = max_per_var
        elif adaptive:
            limit = calculate_adaptive_depth(
                query=pattern,
                base_k=DEFAULT_BASE_K,
                token_budget=token_budget
            )
        else:
            limit = DEFAULT_BASE_K

        results = {}
        total_matches = 0

        for name, var in self.variables.items():
            # If we have a token budget, respect it
            if token_budget is not None:
                remaining_budget = token_budget - (total_matches * TOKENS_PER_RESULT)
                if remaining_budget <= 0:
                    break
                current_limit = min(limit, remaining_budget // TOKENS_PER_RESULT)
            else:
                current_limit = limit

            matches = var.grep(pattern, max_matches=current_limit)
            if matches:
                results[name] = matches
                total_matches += len(matches)

        return results

    def search_all_with_stats(
        self,
        pattern: str,
        max_per_var: Optional[int] = None,
        token_budget: Optional[int] = None,
        adaptive: bool = True
    ) -> Dict[str, Any]:
        """
        Search with retrieval statistics for cost tracking.

        Returns both results and metadata about the retrieval operation.
        Useful for tracking costs via Economic Metadata on Molecules.

        Args:
            pattern: Regex pattern to search for
            max_per_var: Explicit max matches per variable
            token_budget: Optional token budget for retrieval
            adaptive: Whether to use adaptive depth (default True)

        Returns:
            Dict with 'results', 'complexity', 'total_matches', 'estimated_tokens'
        """
        complexity = score_query_complexity(pattern)

        results = self.search_all(
            pattern=pattern,
            max_per_var=max_per_var,
            token_budget=token_budget,
            adaptive=adaptive
        )

        total_matches = sum(len(matches) for matches in results.values())

        return {
            'results': results,
            'pattern': pattern,
            'complexity_score': complexity,
            'total_matches': total_matches,
            'variables_searched': len(self.variables),
            'variables_with_matches': len(results),
            'estimated_tokens': estimate_retrieval_tokens(total_matches),
            'token_budget': token_budget,
            'adaptive': adaptive
        }

    def create_buffer(self, name: str, purpose: str) -> MemoryBuffer:
        """Create a new memory buffer for accumulating answers"""
        buffer = MemoryBuffer.create(name=name, purpose=purpose)
        self.buffers[name] = buffer
        self._save_state()
        return buffer

    def get_buffer(self, name: str) -> Optional[MemoryBuffer]:
        """Get a memory buffer by name"""
        return self.buffers.get(name)

    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all available context.
        Useful for agents to understand what's available.
        """
        type_summaries = {}
        for ctx_type in ContextType:
            vars_of_type = self.type_index.get(ctx_type, [])
            if vars_of_type:
                total_size = sum(
                    self.variables[n].size for n in vars_of_type
                    if n in self.variables
                )
                type_summaries[ctx_type.value] = {
                    'count': len(vars_of_type),
                    'total_size': total_size,
                    'variables': [
                        {'name': n, 'summary': self.variables[n].summary}
                        for n in vars_of_type[:5]  # First 5 only
                        if n in self.variables
                    ]
                }

        return {
            'agent_id': self.agent_id,
            'total_variables': len(self.variables),
            'total_buffers': len(self.buffers),
            'by_type': type_summaries,
            'active_buffers': [
                {'name': b.name, 'purpose': b.purpose, 'ready': b.ready}
                for b in self.buffers.values()
            ]
        }


@dataclass
class SubAgentCall:
    """
    A request to spawn a sub-agent with focused context.
    Like RLM's recursive LM calls.
    """
    id: str
    parent_agent_id: str
    query: str
    context_vars: List[str]  # Names of context variables to include
    depth: int  # Recursion depth
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Any] = None
    created_at: str = ""
    completed_at: Optional[str] = None

    @classmethod
    def create(
        cls,
        parent_agent_id: str,
        query: str,
        context_vars: List[str],
        depth: int = 1
    ) -> 'SubAgentCall':
        return cls(
            id=f"sub-{uuid.uuid4().hex[:8]}",
            parent_agent_id=parent_agent_id,
            query=query,
            context_vars=context_vars,
            depth=depth,
            created_at=datetime.utcnow().isoformat()
        )


class RecursiveMemoryManager:
    """
    Manages recursive sub-agent calls with focused context.

    Like RLM's ability to spawn sub-LLMs that only see relevant
    portions of the context, enabling parallel processing and
    context-aware decomposition.
    """

    def __init__(self, corp_path: Path, max_depth: int = 3):
        self.corp_path = Path(corp_path)
        self.max_depth = max_depth
        self.calls_path = self.corp_path / "memory" / "subcalls"
        self.calls_path.mkdir(parents=True, exist_ok=True)
        self.pending_calls: Dict[str, SubAgentCall] = {}

    def request_subcall(
        self,
        parent_agent_id: str,
        query: str,
        context_vars: List[str],
        depth: int = 1
    ) -> SubAgentCall:
        """
        Request a sub-agent call with focused context.

        This creates a work item that a sub-agent can pick up,
        with only the specified context variables included.
        """
        if depth > self.max_depth:
            raise ValueError(f"Max recursion depth {self.max_depth} exceeded")

        call = SubAgentCall.create(
            parent_agent_id=parent_agent_id,
            query=query,
            context_vars=context_vars,
            depth=depth
        )

        # Persist call
        call_file = self.calls_path / f"{call.id}.yaml"
        call_file.write_text(yaml.dump(asdict(call), default_flow_style=False))

        self.pending_calls[call.id] = call
        return call

    def batch_subcalls(
        self,
        parent_agent_id: str,
        queries: List[Dict[str, Any]],
        depth: int = 1
    ) -> List[SubAgentCall]:
        """
        Request multiple sub-agent calls in parallel.
        Like RLM's llm_batch() for parallel processing.

        queries: List of {'query': str, 'context_vars': List[str]}
        """
        calls = []
        for q in queries:
            call = self.request_subcall(
                parent_agent_id=parent_agent_id,
                query=q['query'],
                context_vars=q.get('context_vars', []),
                depth=depth
            )
            calls.append(call)
        return calls

    def get_pending_calls(self) -> List[SubAgentCall]:
        """Get all pending sub-agent calls"""
        pending = []
        for call_file in self.calls_path.glob("sub-*.yaml"):
            data = yaml.safe_load(call_file.read_text())
            if data.get('status') == 'pending':
                pending.append(SubAgentCall(**data))
        return pending

    def claim_subcall(self, call_id: str, agent_id: str) -> Optional[SubAgentCall]:
        """Claim a pending sub-agent call"""
        call_file = self.calls_path / f"{call_id}.yaml"
        if not call_file.exists():
            return None

        data = yaml.safe_load(call_file.read_text())
        if data.get('status') != 'pending':
            return None

        data['status'] = 'running'
        data['assigned_to'] = agent_id
        call_file.write_text(yaml.dump(data, default_flow_style=False))

        return SubAgentCall(**{k: v for k, v in data.items() if k != 'assigned_to'})

    def complete_subcall(self, call_id: str, result: Any) -> None:
        """Mark a sub-agent call as complete with result"""
        call_file = self.calls_path / f"{call_id}.yaml"
        if not call_file.exists():
            return

        data = yaml.safe_load(call_file.read_text())
        data['status'] = 'completed'
        data['result'] = result
        data['completed_at'] = datetime.utcnow().isoformat()
        call_file.write_text(yaml.dump(data, default_flow_style=False))

    def get_results(self, call_ids: List[str]) -> Dict[str, Any]:
        """Get results from completed sub-agent calls"""
        results = {}
        for call_id in call_ids:
            call_file = self.calls_path / f"{call_id}.yaml"
            if call_file.exists():
                data = yaml.safe_load(call_file.read_text())
                if data.get('status') == 'completed':
                    results[call_id] = data.get('result')
        return results


class ContextCompressor:
    """
    Intelligent context compression that preserves access to full data.

    Unlike traditional summarization which is lossy, this creates
    navigable summaries while keeping full data accessible.
    """

    def __init__(self, environment: ContextEnvironment):
        self.env = environment

    def create_navigable_summary(
        self,
        var_names: List[str],
        summary_name: str,
        compression_level: str = "moderate"  # light, moderate, aggressive
    ) -> ContextVariable:
        """
        Create a summary that still allows navigation to original content.

        The summary includes:
        - High-level overview
        - Key decision points
        - Pointers to detailed sections
        """
        sections = []
        pointers = []

        for name in var_names:
            var = self.env.get(name)
            if not var:
                continue

            # Create section summary based on compression level
            if compression_level == "light":
                # Include more detail
                section = self._light_compress(var)
            elif compression_level == "aggressive":
                # Minimal summary
                section = self._aggressive_compress(var)
            else:
                # Balanced
                section = self._moderate_compress(var)

            sections.append(section)
            pointers.append({
                'original_var': name,
                'type': var.context_type.value,
                'size': var.size,
                'access': f"env.get('{name}').get_content()"
            })

        summary_content = {
            'overview': f"Summary of {len(var_names)} context variables",
            'sections': sections,
            'navigation': pointers,
            'full_access': "Use pointers to access full content when needed"
        }

        return self.env.store(
            name=summary_name,
            content=summary_content,
            context_type=ContextType.SUMMARY,
            summary=f"Navigable summary of: {', '.join(var_names[:3])}...",
            metadata={'source_vars': var_names, 'compression_level': compression_level}
        )

    def _light_compress(self, var: ContextVariable) -> Dict[str, Any]:
        """Light compression - keep most detail"""
        content = var.peek(length=2000)
        return {
            'name': var.name,
            'type': var.context_type.value,
            'summary': var.summary,
            'preview': content,
            'keywords': self._extract_keywords(content)
        }

    def _moderate_compress(self, var: ContextVariable) -> Dict[str, Any]:
        """Moderate compression - balanced detail"""
        content = var.peek(length=500)
        return {
            'name': var.name,
            'type': var.context_type.value,
            'summary': var.summary,
            'preview': content[:200] + "..." if len(content) > 200 else content,
            'key_points': self._extract_key_points(content)
        }

    def _aggressive_compress(self, var: ContextVariable) -> Dict[str, Any]:
        """Aggressive compression - minimal summary"""
        return {
            'name': var.name,
            'type': var.context_type.value,
            'summary': var.summary,
            'size': var.size
        }

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction - could be enhanced with NLP
        words = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]{3,}\b', text)
        word_freq = {}
        for word in words:
            word_lower = word.lower()
            word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:max_keywords]]

    def _extract_key_points(self, text: str, max_points: int = 5) -> List[str]:
        """Extract key points from text"""
        # Simple extraction - look for bullet points, headers, etc.
        points = []

        # Look for markdown headers
        headers = re.findall(r'^#+\s+(.+)$', text, re.MULTILINE)
        points.extend(headers[:max_points])

        # Look for bullet points
        bullets = re.findall(r'^\s*[-*]\s+(.+)$', text, re.MULTILINE)
        points.extend(bullets[:max_points - len(points)])

        # If no structure found, take first sentences
        if not points:
            sentences = re.split(r'[.!?]', text)
            points = [s.strip() for s in sentences[:max_points] if s.strip()]

        return points[:max_points]


class OrganizationalMemory:
    """
    Long-term organizational memory for AI Corp.

    Stores collective knowledge, decisions, and lessons learned
    that persist across agent lifecycles.
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.memory_path = self.corp_path / "memory" / "organizational"
        self.memory_path.mkdir(parents=True, exist_ok=True)

        self.decisions_file = self.memory_path / "decisions.yaml"
        self.lessons_file = self.memory_path / "lessons_learned.yaml"
        self.patterns_file = self.memory_path / "patterns.yaml"

    def record_decision(
        self,
        decision_id: str,
        title: str,
        context: str,
        options_considered: List[Dict[str, str]],
        chosen_option: str,
        rationale: str,
        made_by: str,
        department: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Record an organizational decision for future reference.
        Helps maintain consistency and learn from past choices.
        """
        decision = {
            'id': decision_id,
            'title': title,
            'context': context,
            'options_considered': options_considered,
            'chosen_option': chosen_option,
            'rationale': rationale,
            'made_by': made_by,
            'department': department,
            'tags': tags or [],
            'recorded_at': datetime.utcnow().isoformat()
        }

        decisions = self._load_file(self.decisions_file)
        decisions.append(decision)
        self._save_file(self.decisions_file, decisions)

        return decision

    def search_decisions(
        self,
        query: Optional[str] = None,
        department: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search past decisions for relevant context"""
        decisions = self._load_file(self.decisions_file)

        results = []
        for d in decisions:
            # Filter by department
            if department and d.get('department') != department:
                continue

            # Filter by tags
            if tags and not any(t in d.get('tags', []) for t in tags):
                continue

            # Filter by query
            if query:
                searchable = f"{d.get('title', '')} {d.get('context', '')} {d.get('rationale', '')}"
                if not re.search(query, searchable, re.IGNORECASE):
                    continue

            results.append(d)

        return results

    def record_lesson(
        self,
        lesson_id: str,
        title: str,
        situation: str,
        action_taken: str,
        outcome: str,
        lesson: str,
        recommendations: List[str],
        recorded_by: str,
        severity: str = "info"  # info, warning, critical
    ) -> Dict[str, Any]:
        """
        Record a lesson learned for organizational improvement.
        """
        lesson_entry = {
            'id': lesson_id,
            'title': title,
            'situation': situation,
            'action_taken': action_taken,
            'outcome': outcome,
            'lesson': lesson,
            'recommendations': recommendations,
            'recorded_by': recorded_by,
            'severity': severity,
            'recorded_at': datetime.utcnow().isoformat()
        }

        lessons = self._load_file(self.lessons_file)
        lessons.append(lesson_entry)
        self._save_file(self.lessons_file, lessons)

        return lesson_entry

    def get_relevant_lessons(self, context: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get lessons relevant to a given context"""
        lessons = self._load_file(self.lessons_file)

        # Simple relevance scoring based on keyword overlap
        scored = []
        context_words = set(re.findall(r'\b\w+\b', context.lower()))

        for lesson in lessons:
            lesson_text = f"{lesson.get('title', '')} {lesson.get('situation', '')} {lesson.get('lesson', '')}"
            lesson_words = set(re.findall(r'\b\w+\b', lesson_text.lower()))
            overlap = len(context_words & lesson_words)
            if overlap > 0:
                scored.append((overlap, lesson))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:max_results]]

    def record_pattern(
        self,
        pattern_id: str,
        name: str,
        description: str,
        when_to_use: str,
        implementation: str,
        examples: List[str],
        recorded_by: str
    ) -> Dict[str, Any]:
        """Record a recurring pattern for reuse"""
        pattern = {
            'id': pattern_id,
            'name': name,
            'description': description,
            'when_to_use': when_to_use,
            'implementation': implementation,
            'examples': examples,
            'recorded_by': recorded_by,
            'recorded_at': datetime.utcnow().isoformat()
        }

        patterns = self._load_file(self.patterns_file)
        patterns.append(pattern)
        self._save_file(self.patterns_file, patterns)

        return pattern

    # =========================================================================
    # CEO Preferences - High-priority rules that persist across sessions
    # =========================================================================

    # Common stopwords to filter out when extracting action words from preferences
    _PREFERENCE_STOPWORDS = {
        'always', 'never', 'dont', "don't", 'do', 'not', 'please',
        'make', 'sure', 'to', 'the', 'a', 'an', 'i', 'want', 'you',
        'must', 'should', 'need', 'avoid', 'stop', 'use', 'keep'
    }

    # Words indicating positive polarity (do this)
    _POSITIVE_POLARITY_WORDS = {'always', 'must', 'use', 'enable', 'include', 'keep', 'add'}

    # Words indicating negative polarity (don't do this)
    _NEGATIVE_POLARITY_WORDS = {'never', 'dont', "don't", 'avoid', 'stop', 'disable', 'exclude', 'remove', 'no'}

    # Common stopwords for relevance scoring (used in find_similar_past_work)
    _RELEVANCE_STOPWORDS = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'for', 'and', 'or', 'of', 'in', 'on'}

    @property
    def preferences_file(self) -> Path:
        """Path to CEO preferences file"""
        return self.memory_path / "ceo_preferences.yaml"

    def store_preference(
        self,
        preference_id: str,
        rule: str,
        source: str = "explicit",  # explicit, inferred, conversation
        priority: str = "high",  # high, medium, low
        context: Optional[str] = None,
        conversation_id: Optional[str] = None,
        topic: Optional[str] = None,
        supersedes: Optional[str] = None,
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """
        Store a CEO preference/rule for persistent retrieval.

        High-priority preferences are always included in COO context.

        Args:
            preference_id: Unique identifier
            rule: The preference rule (e.g., "Don't modify local files")
            source: Where this came from (explicit, inferred, conversation)
            priority: How important (high = always load, medium = when relevant)
            context: Additional context about when this applies
            conversation_id: If extracted from a conversation, which one
            topic: Category/topic for grouping (e.g., "code_style", "communication")
            supersedes: ID of preference this one replaces (for tracking history)
            confidence: Confidence level 0-1 (lower for inferred preferences)
        """
        now = datetime.utcnow().isoformat()

        # Auto-detect topic if not provided
        if not topic:
            topic = self._infer_preference_topic(rule)

        preference = {
            'id': preference_id,
            'rule': rule,
            'source': source,
            'priority': priority,
            'context': context,
            'conversation_id': conversation_id,
            'topic': topic,
            'active': True,
            'supersedes': supersedes,  # ID of preference this replaces
            'superseded_by': None,     # ID of preference that replaced this
            'confidence': confidence,
            'last_confirmed': now,     # When CEO last confirmed this is accurate
            'created_at': now,
            'updated_at': now
        }

        preferences = self._load_file(self.preferences_file)

        # Check if this preference already exists (by rule similarity)
        existing_idx = None
        for i, p in enumerate(preferences):
            if p.get('rule', '').lower() == rule.lower():
                existing_idx = i
                break

        if existing_idx is not None:
            # Update existing preference - preserve history fields
            old_pref = preferences[existing_idx]
            preferences[existing_idx].update({
                'rule': rule,
                'priority': priority,
                'context': context,
                'topic': topic or old_pref.get('topic'),
                'confidence': confidence,
                'last_confirmed': now,
                'updated_at': now
            })
            preference = preferences[existing_idx]
        else:
            preferences.append(preference)

        self._save_file(self.preferences_file, preferences)
        return preference

    def _infer_preference_topic(self, rule: str) -> str:
        """Infer a topic/category from the preference rule text."""
        rule_lower = rule.lower()

        topic_keywords = {
            'code_style': ['code', 'style', 'format', 'indent', 'naming', 'comment'],
            'communication': ['ask', 'tell', 'notify', 'confirm', 'report', 'update'],
            'workflow': ['commit', 'push', 'branch', 'review', 'test', 'deploy'],
            'files': ['file', 'directory', 'folder', 'path', 'edit', 'modify', 'delete'],
            'security': ['password', 'secret', 'key', 'credential', 'auth', 'permission'],
            'delegation': ['delegate', 'assign', 'worker', 'team', 'vp', 'director'],
            'quality': ['test', 'quality', 'check', 'verify', 'validate', 'ensure'],
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in rule_lower for kw in keywords):
                return topic

        return 'general'

    def detect_preference_conflict(
        self,
        new_rule: str,
        check_inactive: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if a new preference conflicts with existing ones.

        Uses keyword analysis to find semantic conflicts like
        "always do X" vs "never do X".

        Args:
            new_rule: The new preference rule to check
            check_inactive: Whether to also check inactive preferences

        Returns:
            The conflicting preference dict if found, None otherwise
        """
        new_rule_lower = new_rule.lower()
        new_words = set(re.findall(r'\b\w+\b', new_rule_lower))

        # Extract the "action" part - filter out stopwords to get core action
        new_action_words = new_words - self._PREFERENCE_STOPWORDS

        # Determine the "polarity" of the new preference
        new_positive = bool(new_words & self._POSITIVE_POLARITY_WORDS)
        new_negative = bool(new_words & self._NEGATIVE_POLARITY_WORDS)

        preferences = self._load_file(self.preferences_file)

        for pref in preferences:
            # Skip inactive unless requested
            if not check_inactive and not pref.get('active', True):
                continue

            existing_rule_lower = pref.get('rule', '').lower()
            existing_words = set(re.findall(r'\b\w+\b', existing_rule_lower))
            existing_action_words = existing_words - self._PREFERENCE_STOPWORDS

            # Check for significant action word overlap
            overlap = new_action_words & existing_action_words
            if len(overlap) < 2:  # Need at least 2 common action words
                continue

            # Determine polarity of existing preference
            existing_positive = bool(existing_words & self._POSITIVE_POLARITY_WORDS)
            existing_negative = bool(existing_words & self._NEGATIVE_POLARITY_WORDS)

            # Conflict: same topic, opposite polarity
            if (new_positive and existing_negative) or (new_negative and existing_positive):
                return {
                    'conflicting_preference': pref,
                    'overlap_words': list(overlap),
                    'conflict_type': 'polarity_reversal',
                    'new_polarity': 'positive' if new_positive else 'negative',
                    'existing_polarity': 'positive' if existing_positive else 'negative'
                }

            # Also check for exact topic + different instruction
            if pref.get('topic') and self._infer_preference_topic(new_rule) == pref.get('topic'):
                # Same topic - check if instructions differ significantly
                if len(overlap) >= 3 and new_rule_lower != existing_rule_lower:
                    # Significant overlap in same topic but different rules
                    return {
                        'conflicting_preference': pref,
                        'overlap_words': list(overlap),
                        'conflict_type': 'same_topic_different_rule',
                        'topic': pref.get('topic')
                    }

        return None

    def update_preference(
        self,
        old_id: str,
        new_rule: str,
        reason: str,
        new_priority: Optional[str] = None,
        new_context: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a preference by superseding the old one with a new one.

        Preserves history: marks old as inactive with reference to new,
        and new has reference to what it replaced.

        Args:
            old_id: ID of the preference being replaced
            new_rule: The new preference rule
            reason: Why this preference changed
            new_priority: Priority for new preference (defaults to old priority)
            new_context: Context for new preference
            conversation_id: Conversation where this update occurred

        Returns:
            The new preference dict, or None if old_id not found
        """
        preferences = self._load_file(self.preferences_file)

        # Find the old preference
        old_pref = None
        old_idx = None
        for i, p in enumerate(preferences):
            if p.get('id') == old_id:
                old_pref = p
                old_idx = i
                break

        if old_pref is None:
            return None

        now = datetime.utcnow().isoformat()
        new_id = f"pref_{uuid.uuid4().hex[:8]}"

        # Create the new preference
        new_pref = {
            'id': new_id,
            'rule': new_rule,
            'source': 'update',
            'priority': new_priority or old_pref.get('priority', 'high'),
            'context': new_context or f"Updated: {reason}",
            'conversation_id': conversation_id,
            'topic': self._infer_preference_topic(new_rule) or old_pref.get('topic'),
            'active': True,
            'supersedes': old_id,  # Link to what this replaced
            'superseded_by': None,
            'confidence': 1.0,  # High confidence since explicitly updated
            'last_confirmed': now,
            'created_at': now,
            'updated_at': now,
            'update_reason': reason,
            'previous_rule': old_pref.get('rule')  # Keep history
        }

        # Mark old preference as inactive and link to new
        preferences[old_idx]['active'] = False
        preferences[old_idx]['superseded_by'] = new_id
        preferences[old_idx]['updated_at'] = now
        preferences[old_idx]['deactivation_reason'] = reason

        # Add new preference
        preferences.append(new_pref)

        self._save_file(self.preferences_file, preferences)
        return new_pref

    def get_all_preferences(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all stored CEO preferences"""
        preferences = self._load_file(self.preferences_file)
        if active_only:
            preferences = [p for p in preferences if p.get('active', True)]
        return preferences

    def get_preferences_by_topic(self, topic: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get preferences filtered by topic/category"""
        preferences = self.get_all_preferences(active_only=active_only)
        return [p for p in preferences if p.get('topic') == topic]

    def get_preference_history(self, preference_id: str) -> List[Dict[str, Any]]:
        """
        Get the full history of a preference chain.

        Follows supersedes/superseded_by links to build the evolution timeline.
        """
        preferences = self._load_file(self.preferences_file)
        # Build map safely, skipping any malformed preferences without 'id'
        pref_map = {p['id']: p for p in preferences if p.get('id')}

        # Find the starting preference
        current = pref_map.get(preference_id)
        if not current:
            return []

        history = []

        # Walk backwards through supersedes chain
        backward_chain = []
        p = current
        while p:
            backward_chain.append(p)
            supersedes_id = p.get('supersedes')
            p = pref_map.get(supersedes_id) if supersedes_id else None

        # Reverse to get chronological order
        history = list(reversed(backward_chain))

        # Walk forward through superseded_by chain (in case we started mid-chain)
        p = current
        while p.get('superseded_by'):
            next_id = p.get('superseded_by')
            p = pref_map.get(next_id)
            if p and p not in history:
                history.append(p)

        return history

    def get_preferences_for_confirmation(
        self,
        max_age_days: int = 30,
        min_confidence: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Get preferences that should be surfaced for CEO confirmation.

        Returns preferences that:
        - Haven't been confirmed recently
        - Have lower confidence (inferred rather than explicit)
        - Were extracted from conversations (vs explicitly stated)

        Args:
            max_age_days: Consider preferences not confirmed in this many days
            min_confidence: Consider preferences below this confidence level
        """
        preferences = self.get_all_preferences(active_only=True)
        now = datetime.utcnow()
        needs_confirmation = []

        for pref in preferences:
            should_confirm = False
            reason = []

            # Check last confirmed time
            last_confirmed = pref.get('last_confirmed')
            if last_confirmed:
                try:
                    confirmed_time = datetime.fromisoformat(last_confirmed.replace('Z', '+00:00'))
                    days_since = (now - confirmed_time.replace(tzinfo=None)).days
                    if days_since > max_age_days:
                        should_confirm = True
                        reason.append(f"not confirmed in {days_since} days")
                except (ValueError, TypeError):
                    should_confirm = True
                    reason.append("invalid confirmation timestamp")
            else:
                should_confirm = True
                reason.append("never confirmed")

            # Check confidence level
            confidence = pref.get('confidence', 1.0)
            if confidence < min_confidence:
                should_confirm = True
                reason.append(f"low confidence ({confidence:.0%})")

            # Inferred preferences need confirmation more often
            if pref.get('source') == 'inferred':
                should_confirm = True
                reason.append("inferred (not explicitly stated)")

            if should_confirm:
                needs_confirmation.append({
                    **pref,
                    'confirmation_reasons': reason
                })

        # Sort by priority (high first) then by age
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        needs_confirmation.sort(key=lambda p: (
            priority_order.get(p.get('priority', 'low'), 3),
            p.get('last_confirmed', '0')
        ))

        return needs_confirmation

    def confirm_preference(self, preference_id: str) -> bool:
        """Mark a preference as confirmed by the CEO."""
        preferences = self._load_file(self.preferences_file)

        for p in preferences:
            if p.get('id') == preference_id:
                p['last_confirmed'] = datetime.utcnow().isoformat()
                p['confidence'] = 1.0  # Confirmed = high confidence
                self._save_file(self.preferences_file, preferences)
                return True

        return False

    def get_priority_preferences(self, min_priority: str = "high") -> List[Dict[str, Any]]:
        """
        Get preferences at or above the specified priority level.

        Priority levels: high > medium > low
        """
        priority_order = {"high": 3, "medium": 2, "low": 1}
        min_level = priority_order.get(min_priority, 1)

        preferences = self.get_all_preferences()
        return [
            p for p in preferences
            if priority_order.get(p.get('priority', 'low'), 0) >= min_level
        ]

    def deactivate_preference(self, preference_id: str, reason: str = "manually deactivated") -> bool:
        """Deactivate a preference (soft delete)"""
        preferences = self._load_file(self.preferences_file)

        for p in preferences:
            if p.get('id') == preference_id:
                p['active'] = False
                p['updated_at'] = datetime.utcnow().isoformat()
                p['deactivation_reason'] = reason
                self._save_file(self.preferences_file, preferences)
                return True

        return False

    def format_preferences_for_prompt(self) -> str:
        """
        Format high-priority preferences for LLM prompt injection.

        Returns a string suitable for adding to system prompts.
        """
        preferences = self.get_priority_preferences("high")

        if not preferences:
            return ""

        lines = ["## CEO PREFERENCES (Always Follow)", ""]

        # Group by topic for better organization
        by_topic: Dict[str, List[Dict[str, Any]]] = {}
        for p in preferences:
            topic = p.get('topic', 'general')
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(p)

        for topic, prefs in by_topic.items():
            if len(by_topic) > 1:  # Only show topic headers if multiple topics
                lines.append(f"### {topic.replace('_', ' ').title()}")
            for p in prefs:
                lines.append(f"- {p['rule']}")
                if p.get('context') and p.get('context') != "Extracted from conversation":
                    lines.append(f"  (Context: {p['context']})")
            lines.append("")

        return "\n".join(lines)

    # =========================================================================
    # Outcome-Based Learning - Record outcomes and find similar past work
    # =========================================================================

    @property
    def outcomes_file(self) -> Path:
        """Path to molecule outcomes file"""
        return self.memory_path / "molecule_outcomes.yaml"

    @property
    def synthesized_insights_file(self) -> Path:
        """Path to synthesized insights from Evolution Daemon"""
        return self.memory_path / "synthesized_insights.yaml"

    def record_molecule_outcome(
        self,
        molecule_id: str,
        title: str,
        description: str,
        outcome: str,  # 'success', 'partial', 'failed'
        task_type: str,
        approach: str,
        departments: List[str],
        duration_seconds: Optional[int] = None,
        blockers: Optional[List[str]] = None,
        key_learnings: Optional[List[str]] = None,
        conversation_context: Optional[str] = None,
        recorded_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Record the outcome of a completed molecule for learning.

        This captures structured data about what was attempted, what approach
        was used, and what the result was - enabling pattern detection and
        lesson surfacing for similar future work.

        Args:
            molecule_id: ID of the completed molecule
            title: Molecule title/name
            description: What the molecule was trying to accomplish
            outcome: 'success', 'partial', or 'failed'
            task_type: Category of task (e.g., 'code_review', 'feature', 'research')
            approach: The approach/strategy used
            departments: Departments involved
            duration_seconds: How long the work took
            blockers: List of blockers encountered
            key_learnings: Key lessons from this work
            conversation_context: Relevant conversation context (summarized if long)
            recorded_by: Who/what recorded this outcome

        Returns:
            The recorded outcome entry
        """
        outcome_entry = {
            'id': f"outcome-{molecule_id}",
            'molecule_id': molecule_id,
            'title': title,
            'description': description,
            'outcome': outcome,
            'task_type': task_type,
            'approach': approach,
            'departments': departments,
            'duration_seconds': duration_seconds,
            'blockers': blockers or [],
            'key_learnings': key_learnings or [],
            'conversation_context': conversation_context,
            'recorded_by': recorded_by,
            'recorded_at': datetime.utcnow().isoformat()
        }

        # Save to outcomes file
        outcomes = self._load_file(self.outcomes_file)
        outcomes.append(outcome_entry)
        self._save_file(self.outcomes_file, outcomes)

        # Also create a lesson from this outcome if there are learnings
        if key_learnings:
            self.record_lesson(
                lesson_id=f"lesson-from-{molecule_id}",
                title=f"Lessons from: {title}",
                situation=description,
                action_taken=approach,
                outcome=outcome,
                lesson="; ".join(key_learnings),
                recommendations=key_learnings,
                recorded_by=recorded_by,
                severity="info" if outcome == "success" else "warning"
            )

        return outcome_entry

    def find_similar_past_work(
        self,
        task_description: str,
        max_results: int = 5,
        include_failed: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find similar past work to inform a new task.

        Searches both completed molecule outcomes AND lessons_learned,
        using relevance scoring aligned with Phase 1's approach.

        Args:
            task_description: Description of the new task
            max_results: Maximum number of results to return
            include_failed: Whether to include failed outcomes

        Returns:
            List of similar past work with relevance scores, approaches,
            outcomes, and any blockers/learnings. Deduplicated to avoid
            showing both an outcome and its auto-generated lesson.
        """
        results = []
        seen_molecule_ids = set()  # Track outcomes to avoid showing their auto-generated lessons

        # Tokenize and normalize task description for matching
        task_words = set(re.findall(r'\b\w+\b', task_description.lower()))
        task_words -= self._RELEVANCE_STOPWORDS

        if not task_words:
            return []

        # Search molecule outcomes first (higher priority)
        outcomes = self._load_file(self.outcomes_file)
        for outcome in outcomes:
            if not include_failed and outcome.get('outcome') == 'failed':
                continue

            # Compute relevance score
            outcome_text = f"{outcome.get('title', '')} {outcome.get('description', '')} {outcome.get('approach', '')}"
            outcome_words = set(re.findall(r'\b\w+\b', outcome_text.lower()))
            outcome_words -= self._RELEVANCE_STOPWORDS

            overlap = task_words & outcome_words
            if not overlap:
                continue

            # Score based on overlap ratio and complexity alignment
            relevance = len(overlap) / max(len(task_words), 1)

            # Boost if task types match implied categories
            task_type = outcome.get('task_type', '')
            if task_type and task_type.lower() in task_description.lower():
                relevance += 0.2

            # Track this molecule_id to avoid duplicate lessons
            molecule_id = outcome.get('molecule_id')
            if molecule_id:
                seen_molecule_ids.add(molecule_id)

            results.append({
                'source': 'outcome',
                'id': outcome.get('id'),
                'title': outcome.get('title'),
                'description': outcome.get('description'),
                'outcome': outcome.get('outcome'),
                'approach': outcome.get('approach'),
                'blockers': outcome.get('blockers', []),
                'key_learnings': outcome.get('key_learnings', []),
                'task_type': task_type,
                'departments': outcome.get('departments', []),
                'relevance_score': min(relevance, 1.0),
                'overlap_words': list(overlap)
            })

        # Search lessons learned (skip auto-generated lessons from outcomes we already found)
        lessons = self._load_file(self.lessons_file)
        for lesson in lessons:
            # Skip lessons auto-generated from outcomes we already included
            lesson_id = lesson.get('id', '')
            if lesson_id.startswith('lesson-from-'):
                # Extract molecule ID from lesson ID
                source_mol_id = lesson_id.replace('lesson-from-', '')
                if source_mol_id in seen_molecule_ids:
                    continue

            lesson_text = f"{lesson.get('title', '')} {lesson.get('situation', '')} {lesson.get('lesson', '')}"
            lesson_words = set(re.findall(r'\b\w+\b', lesson_text.lower()))
            lesson_words -= self._RELEVANCE_STOPWORDS

            overlap = task_words & lesson_words
            if not overlap:
                continue

            relevance = len(overlap) / max(len(task_words), 1)

            results.append({
                'source': 'lesson',
                'id': lesson.get('id'),
                'title': lesson.get('title'),
                'situation': lesson.get('situation'),
                'outcome': lesson.get('outcome'),
                'lesson': lesson.get('lesson'),
                'recommendations': lesson.get('recommendations', []),
                'severity': lesson.get('severity', 'info'),
                'relevance_score': min(relevance, 1.0),
                'overlap_words': list(overlap)
            })

        # Sort by relevance and return top results
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:max_results]

    def get_lessons_for_task_type(
        self,
        task_type: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get lessons and outcomes filtered by task type.

        Args:
            task_type: The task type to filter by
            max_results: Maximum results to return

        Returns:
            List of relevant outcomes and lessons
        """
        results = []
        task_type_lower = task_type.lower()

        # Search outcomes by task_type
        outcomes = self._load_file(self.outcomes_file)
        for outcome in outcomes:
            if outcome.get('task_type', '').lower() == task_type_lower:
                results.append({
                    'source': 'outcome',
                    **outcome
                })

        # Search lessons (by title/situation keyword match)
        lessons = self._load_file(self.lessons_file)
        for lesson in lessons:
            lesson_text = f"{lesson.get('title', '')} {lesson.get('situation', '')}".lower()
            if task_type_lower in lesson_text:
                results.append({
                    'source': 'lesson',
                    **lesson
                })

        return results[:max_results]

    def aggregate_lessons_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate lessons and outcomes by category/task_type.

        Used by Evolution Daemon for synthesis cycles.

        Returns:
            Dictionary mapping categories to their lessons/outcomes
        """
        categories: Dict[str, List[Dict[str, Any]]] = {}

        # Group outcomes by task_type
        outcomes = self._load_file(self.outcomes_file)
        for outcome in outcomes:
            task_type = outcome.get('task_type', 'general')
            if task_type not in categories:
                categories[task_type] = []
            categories[task_type].append({
                'source': 'outcome',
                'outcome': outcome.get('outcome'),
                'blockers': outcome.get('blockers', []),
                'learnings': outcome.get('key_learnings', []),
                'recorded_at': outcome.get('recorded_at')
            })

        # Add lessons to categories (infer from title/situation)
        lessons = self._load_file(self.lessons_file)
        for lesson in lessons:
            # Try to infer category from lesson content
            lesson_text = f"{lesson.get('title', '')} {lesson.get('situation', '')}".lower()
            matched = False
            for category in categories:
                if category.lower() in lesson_text:
                    categories[category].append({
                        'source': 'lesson',
                        'lesson': lesson.get('lesson'),
                        'recommendations': lesson.get('recommendations', []),
                        'severity': lesson.get('severity'),
                        'recorded_at': lesson.get('recorded_at')
                    })
                    matched = True
                    break
            if not matched:
                if 'general' not in categories:
                    categories['general'] = []
                categories['general'].append({
                    'source': 'lesson',
                    'lesson': lesson.get('lesson'),
                    'recommendations': lesson.get('recommendations', []),
                    'severity': lesson.get('severity'),
                    'recorded_at': lesson.get('recorded_at')
                })

        return categories

    def store_synthesized_insight(
        self,
        insight_id: str,
        category: str,
        pattern: str,
        confidence: float,
        evidence_count: int,
        recommendations: List[str],
        source_cycle: str = "evolution_daemon"
    ) -> Dict[str, Any]:
        """
        Store a synthesized insight from Evolution Daemon analysis.

        These are higher-level patterns identified across multiple
        outcomes and lessons. Uses upsert logic - updates existing
        insight if ID matches, otherwise creates new.

        Args:
            insight_id: Unique identifier
            category: Category/task_type this applies to
            pattern: The identified pattern (e.g., "Tasks involving X tend to have blocker Y")
            confidence: Confidence score (0.0-1.0)
            evidence_count: Number of outcomes/lessons supporting this
            recommendations: Recommended actions based on this pattern
            source_cycle: Which cycle generated this insight

        Returns:
            The stored insight
        """
        insight = {
            'id': insight_id,
            'category': category,
            'pattern': pattern,
            'confidence': confidence,
            'evidence_count': evidence_count,
            'recommendations': recommendations,
            'source_cycle': source_cycle,
            'updated_at': datetime.utcnow().isoformat()
        }

        insights = self._load_file(self.synthesized_insights_file)

        # Upsert: update existing or append new
        existing_idx = None
        for i, existing in enumerate(insights):
            if existing.get('id') == insight_id:
                existing_idx = i
                break

        if existing_idx is not None:
            # Preserve original created_at, update the rest
            insight['created_at'] = insights[existing_idx].get('created_at', insight['updated_at'])
            insights[existing_idx] = insight
        else:
            insight['created_at'] = insight['updated_at']
            insights.append(insight)

        self._save_file(self.synthesized_insights_file, insights)

        return insight

    def get_synthesized_insights(
        self,
        category: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Get synthesized insights, optionally filtered.

        Args:
            category: Filter by category
            min_confidence: Minimum confidence threshold

        Returns:
            List of synthesized insights
        """
        insights = self._load_file(self.synthesized_insights_file)

        results = []
        for insight in insights:
            if category and insight.get('category') != category:
                continue
            if insight.get('confidence', 0) < min_confidence:
                continue
            results.append(insight)

        return results

    def format_lessons_for_context(
        self,
        similar_work: List[Dict[str, Any]],
        max_items: int = 3
    ) -> str:
        """
        Format similar past work for injection into LLM context.

        Creates a readable summary of relevant past experiences.

        Args:
            similar_work: Results from find_similar_past_work()
            max_items: Maximum items to include

        Returns:
            Formatted context string
        """
        if not similar_work:
            return ""

        lines = ["## Relevant Past Experience"]

        for item in similar_work[:max_items]:
            title = item.get('title', 'Unknown')
            outcome = item.get('outcome', 'unknown')

            if item.get('source') == 'outcome':
                approach = item.get('approach', '')
                blockers = item.get('blockers', [])
                learnings = item.get('key_learnings', [])

                outcome_label = "✓" if outcome == "success" else "⚠" if outcome == "partial" else "✗"
                lines.append(f"\n**{title}** [{outcome_label} {outcome}]")
                if approach:
                    lines.append(f"  Approach: {approach}")
                if blockers:
                    lines.append(f"  Blockers: {', '.join(blockers)}")
                if learnings:
                    lines.append(f"  Key insight: {learnings[0]}")

            elif item.get('source') == 'lesson':
                lesson = item.get('lesson', '')
                severity = item.get('severity', 'info')
                severity_icon = "ℹ" if severity == "info" else "⚠" if severity == "warning" else "🔴"

                lines.append(f"\n**{title}** [{severity_icon}]")
                if lesson:
                    lines.append(f"  Lesson: {lesson[:150]}...")

        return "\n".join(lines)

    def _load_file(self, path: Path) -> List[Dict[str, Any]]:
        """Load a YAML file, returning empty list if not exists"""
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text())
        return data if isinstance(data, list) else []

    def _save_file(self, path: Path, data: List[Dict[str, Any]]) -> None:
        """Save data to a YAML file"""
        path.write_text(yaml.dump(data, default_flow_style=False))


# Convenience functions for common operations

def create_agent_memory(corp_path: Path, agent_id: str) -> ContextEnvironment:
    """Create a memory environment for an agent"""
    return ContextEnvironment(corp_path, agent_id)


def load_molecule_to_memory(
    env: ContextEnvironment,
    molecule_id: str,
    molecule_engine: 'MoleculeEngine'
) -> Optional[ContextVariable]:
    """Load a molecule into the memory environment"""
    from .molecule import MoleculeEngine

    molecule = molecule_engine.get_molecule(molecule_id)
    if not molecule:
        return None

    return env.store(
        name=f"molecule_{molecule_id}",
        content=molecule.to_dict(),
        context_type=ContextType.MOLECULE,
        summary=f"{molecule.name}: {molecule.description[:100]}...",
        metadata={
            'molecule_id': molecule_id,
            'status': molecule.status.value,
            'step_count': len(molecule.steps)
        }
    )


def load_bead_history_to_memory(
    env: ContextEnvironment,
    entity_type: str,
    entity_id: str,
    ledger: 'BeadLedger'
) -> ContextVariable:
    """Load bead history for an entity into memory"""
    from .bead import BeadLedger

    entries = ledger.get_entries_for_entity(entity_type, entity_id)
    history = [e.to_dict() for e in entries]

    return env.store(
        name=f"bead_history_{entity_type}_{entity_id}",
        content=history,
        context_type=ContextType.BEAD,
        summary=f"Bead history for {entity_type}/{entity_id}: {len(entries)} entries",
        metadata={
            'entity_type': entity_type,
            'entity_id': entity_id,
            'entry_count': len(entries)
        }
    )


# =========================================================================
# Entity Graph Integration
# =========================================================================

def load_entity_to_memory(
    env: ContextEnvironment,
    entity_id: str,
    entity_graph: 'EntityGraph'
) -> Optional[ContextVariable]:
    """
    Load an entity into the memory environment.

    This provides basic entity information for quick reference.
    """
    from .graph import EntityGraph

    entity = entity_graph.entity_store.get_entity(entity_id)
    if not entity:
        return None

    return env.store(
        name=f"entity_{entity_id}",
        content=entity.to_dict(),
        context_type=ContextType.ENTITY,
        summary=f"{entity.name} ({entity.entity_type.value})",
        metadata={
            'entity_id': entity_id,
            'entity_type': entity.entity_type.value,
            'interaction_count': entity.interaction_count
        }
    )


def load_entity_profile_to_memory(
    env: ContextEnvironment,
    entity_id: str,
    entity_graph: 'EntityGraph'
) -> Optional[ContextVariable]:
    """
    Load a rich entity profile into the memory environment.

    This provides comprehensive context about an entity including:
    - Summary and key facts
    - Recent activity
    - Relationship summaries
    - Communication patterns
    - Pending action items
    """
    from .graph import EntityGraph

    profile = entity_graph.get_entity_profile(entity_id)
    if not profile:
        return None

    return env.store(
        name=f"entity_profile_{entity_id}",
        content=profile.to_dict(),
        context_type=ContextType.ENTITY_PROFILE,
        summary=profile.summary,
        metadata={
            'entity_id': entity_id,
            'entity_name': profile.entity.name,
            'interaction_frequency': profile.interaction_frequency,
            'pending_actions': len(profile.action_items)
        }
    )


def load_entity_context_to_memory(
    env: ContextEnvironment,
    entity_ids: List[str],
    entity_graph: 'EntityGraph',
    context_name: Optional[str] = None
) -> ContextVariable:
    """
    Load full entity context package into memory.

    This is what Claude needs before responding to messages
    involving specific entities. Includes:
    - Entity profiles for all participants
    - Relationship information
    - Recent shared interactions
    - Pending action items
    - Overall context summary
    """
    from .graph import EntityGraph

    context = entity_graph.get_context_for_entities(entity_ids)

    name = context_name or f"entity_context_{'_'.join(entity_ids[:3])}"

    return env.store(
        name=name,
        content=context.to_dict(),
        context_type=ContextType.ENTITY_CONTEXT,
        summary=context.summary[:200] if context.summary else "Entity context package",
        metadata={
            'entity_ids': entity_ids,
            'entity_count': len(context.entities),
            'relationship_count': len(context.relationships),
            'pending_actions': len(context.pending_actions)
        }
    )


def load_interaction_to_memory(
    env: ContextEnvironment,
    interaction_id: str,
    entity_graph: 'EntityGraph'
) -> Optional[ContextVariable]:
    """Load an interaction into the memory environment"""
    from .graph import EntityGraph

    interaction = entity_graph.interaction_store.get_interaction(interaction_id)
    if not interaction:
        return None

    return env.store(
        name=f"interaction_{interaction_id}",
        content=interaction.to_dict(),
        context_type=ContextType.INTERACTION,
        summary=f"{interaction.interaction_type.value}: {interaction.summary[:100]}",
        metadata={
            'interaction_id': interaction_id,
            'interaction_type': interaction.interaction_type.value,
            'participant_count': len(interaction.participants),
            'timestamp': interaction.timestamp
        }
    )


def get_entity_context_for_message(
    env: ContextEnvironment,
    message: str,
    entity_graph: 'EntityGraph',
    sender_email: Optional[str] = None
) -> ContextVariable:
    """
    Automatically extract entity mentions from a message and load context.

    This is a convenience function for quickly preparing context
    before Claude processes a message.
    """
    from .graph import EntityGraph

    context = entity_graph.get_context_for_message(message, sender_email)

    entity_ids = [p.entity.id for p in context.entities]
    name = f"msg_context_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    return env.store(
        name=name,
        content=context.to_dict(),
        context_type=ContextType.ENTITY_CONTEXT,
        summary=context.summary[:200] if context.summary else "Message context",
        metadata={
            'entity_ids': entity_ids,
            'entity_count': len(context.entities),
            'auto_extracted': True
        }
    )


# =============================================================================
# Conversation Summarization
# Reference: Rolling summarization for long conversations
# =============================================================================

# Module-level logger for ConversationSummarizer
_summarizer_logger = logging.getLogger(__name__ + '.summarizer')


class ConversationSummarizer:
    """
    Intelligent conversation summarization with rolling summaries.

    Maintains context across long conversations by:
    - Creating rolling summaries when conversations exceed thresholds
    - Preserving important moments (decisions, preferences) in full
    - Combining summaries with recent messages for optimal context

    Usage:
        # Dependency injection for LLM client
        summarizer = ConversationSummarizer(llm_client=coo.llm)

        # Check if summarization needed
        if summarizer.needs_summarization(messages, threshold=20):
            summary = summarizer.summarize_segment(messages[:15])
            # Store summary, keep recent messages

        # Get combined context for LLM
        context = summarizer.get_conversation_context(
            messages=messages,
            existing_summary="Previous context...",
            max_recent=10
        )
    """

    # Default thresholds
    DEFAULT_MESSAGE_THRESHOLD = 20  # When to trigger summarization
    DEFAULT_RECENT_MESSAGES = 10    # Recent messages to keep in full
    DEFAULT_SUMMARY_MAX_TOKENS = 500  # Target summary length

    # Patterns for detecting important messages
    # Decision patterns - indicates a choice was made or action approved
    DECISION_PATTERNS = [
        r"(?:let'?s|we(?:'ll)?|i(?:'ll)?) (?:go with|do|use|implement|choose|pick)",
        r"(?:decided|decision|agree|agreed|approved|confirmed)",
        r"(?:sounds good|that works|yes,? (?:do|let'?s|please))",
        r"(?:start|begin|kick off|proceed)",
    ]

    # Preference patterns - aligned with OrganizationalMemory._PREFERENCE_STOPWORDS usage
    # These match patterns that indicate rules/preferences the CEO states
    PREFERENCE_PATTERNS = [
        r"(?:don'?t|do not|never|avoid|stop)",
        r"(?:always|must|should|need to|make sure)",
        r"(?:i (?:want|need|prefer|expect))",
        r"(?:remember|important|note|rule|preference)",
        r"(?:from now on)",
    ]

    def __init__(self, llm_client=None):
        """
        Initialize the summarizer.

        Args:
            llm_client: LLM client for generating summaries.
                       Should have execute(LLMRequest) method.
                       If None, summarization will use a fallback method.
        """
        self.llm = llm_client

    def needs_summarization(
        self,
        messages: List[Dict[str, Any]],
        threshold: int = DEFAULT_MESSAGE_THRESHOLD
    ) -> bool:
        """
        Check if a conversation needs summarization.

        Args:
            messages: List of message dicts with 'role' and 'content'
            threshold: Message count that triggers summarization

        Returns:
            True if message count exceeds threshold
        """
        return len(messages) > threshold

    def detect_important_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect if a message contains important content that should be preserved.

        Args:
            message: Message dict with 'role', 'content', and optionally 'type'

        Returns:
            Dict with 'is_important', 'importance_type', 'reasons'
        """
        content = message.get('content', '').lower()
        msg_type = message.get('type', 'message')

        result = {
            'is_important': False,
            'importance_type': None,
            'reasons': []
        }

        # Explicit decision messages are always important
        if msg_type == 'decision':
            result['is_important'] = True
            result['importance_type'] = 'decision'
            result['reasons'].append('marked as decision')
            return result

        # Check for decision patterns
        for pattern in self.DECISION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                result['is_important'] = True
                result['importance_type'] = 'decision'
                result['reasons'].append('matches decision pattern')
                break

        # Check for preference patterns
        for pattern in self.PREFERENCE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                result['is_important'] = True
                if result['importance_type'] != 'decision':
                    result['importance_type'] = 'preference'
                result['reasons'].append('matches preference pattern')
                break

        return result

    def extract_important_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract messages that should be preserved in full.

        Args:
            messages: List of message dicts

        Returns:
            List of important messages with their importance metadata
        """
        important = []

        for i, msg in enumerate(messages):
            detection = self.detect_important_message(msg)
            if detection['is_important']:
                important.append({
                    **msg,
                    '_importance': detection,
                    '_index': i
                })

        return important

    def summarize_segment(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = DEFAULT_SUMMARY_MAX_TOKENS,
        context: Optional[str] = None
    ) -> str:
        """
        Summarize a segment of conversation messages.

        Uses LLM if available, otherwise falls back to extractive summary.

        Args:
            messages: List of message dicts to summarize
            max_tokens: Target maximum tokens for summary
            context: Optional context about the conversation

        Returns:
            Summary string
        """
        if not messages:
            return ""

        # Extract important messages to preserve
        important_msgs = self.extract_important_messages(messages)

        # If LLM available, use it for smart summarization
        if self.llm:
            return self._llm_summarize(messages, important_msgs, max_tokens, context)
        else:
            return self._fallback_summarize(messages, important_msgs)

    def _llm_summarize(
        self,
        messages: List[Dict[str, Any]],
        important_msgs: List[Dict[str, Any]],
        max_tokens: int,
        context: Optional[str]
    ) -> str:
        """Generate summary using LLM."""
        from .llm import LLMRequest

        # Format messages for the prompt
        formatted_msgs = []
        for msg in messages:
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            formatted_msgs.append(f"{role}: {content}")

        # Format important messages to highlight
        important_content = ""
        if important_msgs:
            important_items = []
            for imp in important_msgs:
                imp_type = imp.get('_importance', {}).get('importance_type', 'key point')
                content = imp.get('content', '')[:200]
                important_items.append(f"- [{imp_type.upper()}] {content}")
            important_content = "\n".join(important_items)

        prompt = f"""Summarize this conversation segment concisely while preserving key information.

CONVERSATION:
{chr(10).join(formatted_msgs)}

{'IMPORTANT MOMENTS TO PRESERVE:' + chr(10) + important_content if important_content else ''}

{'CONTEXT: ' + context if context else ''}

Create a summary that:
1. Captures the main topics and flow of discussion
2. Preserves all decisions made and preferences stated
3. Notes any action items or commitments
4. Is concise (target ~{max_tokens} tokens)

Summary:"""

        try:
            response = self.llm.execute(LLMRequest(
                prompt=prompt,
                system_prompt="You are a conversation summarizer. Create clear, factual summaries that preserve important details especially decisions and preferences.",
            ))

            if response.success:
                return response.content.strip()
            else:
                # Fall back to extractive if LLM fails
                return self._fallback_summarize(messages, important_msgs)

        except Exception as e:
            # Log error and fall back
            _summarizer_logger.warning(f"LLM summarization failed: {e}")
            return self._fallback_summarize(messages, important_msgs)

    def _fallback_summarize(
        self,
        messages: List[Dict[str, Any]],
        important_msgs: List[Dict[str, Any]]
    ) -> str:
        """
        Generate summary without LLM (extractive approach).

        Extracts key information from messages rather than generating new text.
        """
        parts = []

        # Count messages by role
        role_counts = {}
        for msg in messages:
            role = msg.get('role', 'unknown')
            role_counts[role] = role_counts.get(role, 0) + 1

        parts.append(f"[{len(messages)} messages: " +
                    ", ".join(f"{count} {role}" for role, count in role_counts.items()) + "]")

        # Extract topics from first few messages
        if messages:
            first_user = next((m for m in messages if m.get('role') in ('user', 'ceo')), None)
            if first_user:
                content = first_user.get('content', '')[:150]
                parts.append(f"Started with: {content}...")

        # Include important messages
        if important_msgs:
            parts.append("Key points:")
            for imp in important_msgs[:5]:  # Limit to 5 most important
                imp_type = imp.get('_importance', {}).get('importance_type', 'note')
                content = imp.get('content', '')[:100]
                role = imp.get('role', 'unknown').upper()
                parts.append(f"  • [{imp_type}] {role}: {content}...")

        return "\n".join(parts)

    def get_conversation_context(
        self,
        messages: List[Dict[str, Any]],
        existing_summary: Optional[str] = None,
        max_recent: int = DEFAULT_RECENT_MESSAGES,
        include_important: bool = True
    ) -> str:
        """
        Get combined context for LLM from summary and recent messages.

        This is the main method for getting conversation context.
        Combines:
        - Existing summary of older messages
        - Important messages from the summarized portion (if include_important)
        - Recent messages in full

        Args:
            messages: All messages in the conversation
            existing_summary: Summary of older messages (if any)
            max_recent: Number of recent messages to include in full
            include_important: Whether to include important messages from summarized portion

        Returns:
            Formatted context string for LLM injection
        """
        parts = []

        # Add existing summary if present
        if existing_summary:
            parts.append("## Earlier in Conversation")
            parts.append(existing_summary)
            parts.append("")

        # Split messages into summarized and recent
        recent_messages = messages[-max_recent:] if len(messages) > max_recent else messages
        older_messages = messages[:-max_recent] if len(messages) > max_recent else []

        # Include important messages from older portion
        if include_important and older_messages:
            important = self.extract_important_messages(older_messages)
            if important:
                parts.append("## Key Moments from Earlier")
                for imp in important:
                    imp_type = imp.get('_importance', {}).get('importance_type', 'note')
                    role = imp.get('role', 'unknown').upper()
                    content = imp.get('content', '')
                    parts.append(f"[{imp_type.upper()}] {role}: {content}")
                parts.append("")

        # Add recent messages
        if recent_messages:
            parts.append("## Recent Messages")
            for msg in recent_messages:
                role = msg.get('role', 'unknown').upper()
                content = msg.get('content', '')
                parts.append(f"{role}: {content}")

        return "\n".join(parts)

    def create_rolling_summary(
        self,
        messages: List[Dict[str, Any]],
        existing_summary: Optional[str] = None,
        threshold: int = DEFAULT_MESSAGE_THRESHOLD,
        keep_recent: int = DEFAULT_RECENT_MESSAGES
    ) -> Dict[str, Any]:
        """
        Create or update a rolling summary for a conversation.

        This is the main entry point for maintaining conversation context
        across long conversations.

        Args:
            messages: All messages in the conversation
            existing_summary: Previous summary (if any)
            threshold: Message count that triggers summarization
            keep_recent: Number of recent messages to keep unsummarized

        Returns:
            Dict with:
            - 'summary': Updated summary string
            - 'summarized_count': Number of messages included in summary
            - 'recent_messages': Messages kept in full
            - 'needs_update': Whether summary was updated
        """
        total = len(messages)

        # If below threshold, no summarization needed
        if total <= threshold:
            return {
                'summary': existing_summary or '',
                'summarized_count': 0,
                'recent_messages': messages,
                'needs_update': False
            }

        # Calculate split point
        summarize_up_to = total - keep_recent
        to_summarize = messages[:summarize_up_to]
        recent = messages[summarize_up_to:]

        # Create summary of older messages
        if existing_summary:
            # Combine old summary with newly old messages
            context = f"Previous summary: {existing_summary}"
        else:
            context = None

        new_summary = self.summarize_segment(to_summarize, context=context)

        return {
            'summary': new_summary,
            'summarized_count': summarize_up_to,
            'recent_messages': recent,
            'needs_update': True,
            'important_preserved': len(self.extract_important_messages(to_summarize))
        }


class EntityAwareMemory:
    """
    Memory system that integrates entity context automatically.

    This wraps ContextEnvironment and EntityGraph to provide
    seamless entity-aware context management.
    """

    def __init__(self, corp_path: Path, agent_id: str):
        from .graph import EntityGraph

        self.env = ContextEnvironment(corp_path, agent_id)
        self.entity_graph = EntityGraph(corp_path)
        self.corp_path = corp_path
        self.agent_id = agent_id

    def prepare_context_for_entities(
        self,
        entity_ids: List[str],
        include_profiles: bool = True,
        include_relationships: bool = True
    ) -> Dict[str, ContextVariable]:
        """
        Prepare all relevant context for a set of entities.

        Returns a dictionary of context variables loaded into memory.
        """
        loaded = {}

        # Load entity context package
        ctx_var = load_entity_context_to_memory(
            self.env,
            entity_ids,
            self.entity_graph
        )
        loaded['context'] = ctx_var

        # Optionally load individual profiles
        if include_profiles:
            for eid in entity_ids:
                profile_var = load_entity_profile_to_memory(
                    self.env, eid, self.entity_graph
                )
                if profile_var:
                    loaded[f'profile_{eid}'] = profile_var

        return loaded

    def prepare_context_for_message(
        self,
        message: str,
        sender_email: Optional[str] = None
    ) -> ContextVariable:
        """
        Automatically prepare context for processing a message.

        Extracts entity mentions and loads all relevant context.
        """
        return get_entity_context_for_message(
            self.env,
            message,
            self.entity_graph,
            sender_email
        )

    def get_entity_graph(self) -> 'EntityGraph':
        """Get the underlying entity graph"""
        return self.entity_graph

    def get_environment(self) -> ContextEnvironment:
        """Get the underlying context environment"""
        return self.env

    def process_interaction(
        self,
        interaction_type: str,
        **kwargs
    ) -> None:
        """
        Process an interaction and update the entity graph.

        Supported types: 'email', 'message', 'calendar_event'
        """
        if interaction_type == 'email':
            self.entity_graph.process_email(**kwargs)
        elif interaction_type == 'message':
            self.entity_graph.process_message(**kwargs)
        elif interaction_type == 'calendar_event':
            self.entity_graph.process_calendar_event(**kwargs)
        else:
            raise ValueError(f"Unknown interaction type: {interaction_type}")

    def get_context_prompt(self, entity_ids: List[str]) -> str:
        """
        Get a prompt-ready context string for entities.

        This is what you inject into Claude's prompt before
        processing messages about these entities.
        """
        context = self.entity_graph.get_context_for_entities(entity_ids)
        return context.to_prompt()
