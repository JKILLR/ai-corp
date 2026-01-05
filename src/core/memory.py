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

import re
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import yaml


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

    def search_all(self, pattern: str, max_per_var: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all context variables.
        Like RLM's grep capability across the environment.
        """
        results = {}
        for name, var in self.variables.items():
            matches = var.grep(pattern, max_matches=max_per_var)
            if matches:
                results[name] = matches
        return results

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
