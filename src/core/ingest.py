"""
Document Ingestion Pipeline - RLM-Inspired Processing

Processes uploaded documents for storage in the knowledge base.
Uses a chunk-and-summarize approach inspired by RLM's recursive
processing pattern, but with deterministic chunking rather than
LLM-directed decomposition.

For large documents:
1. Extract content (PDF, image, text)
2. Chunk into manageable pieces
3. Summarize each chunk (via LLM when available)
4. Extract key facts and entities
5. Store hierarchically with links

For small documents:
- Store directly without chunking
"""

import hashlib
import mimetypes
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

from .knowledge import (
    KnowledgeBase, KnowledgeEntry, KnowledgeScope, KnowledgeType
)
from .memory import ContextEnvironment, ContextVariable, ContextType

logger = logging.getLogger(__name__)


# Thresholds for processing decisions
CHUNK_THRESHOLD = 50_000  # Characters before chunking
CHUNK_SIZE = 10_000       # Target chunk size
CHUNK_OVERLAP = 500       # Overlap between chunks


class ExtractionMethod(Enum):
    """Methods for extracting content from files"""
    TEXT = "text"           # Plain text files
    MARKDOWN = "markdown"   # Markdown files
    PDF = "pdf"             # PDF documents
    IMAGE = "image"         # Images (OCR or description)
    JSON = "json"           # JSON data
    CSV = "csv"             # CSV data
    CODE = "code"           # Source code files
    UNKNOWN = "unknown"     # Unknown file type


@dataclass
class ProcessedChunk:
    """A processed chunk of a document"""
    index: int
    content: str
    summary: Optional[str] = None
    facts: List[str] = field(default_factory=list)
    start_offset: int = 0
    end_offset: int = 0


@dataclass
class IngestResult:
    """Result of document processing/ingestion"""
    success: bool
    entry: Optional[KnowledgeEntry] = None
    error: Optional[str] = None
    chunks_processed: int = 0
    facts_extracted: int = 0
    processing_time_ms: int = 0


class ContentExtractor:
    """
    Extracts text content from various file types.

    Currently supports basic extraction. Future versions will add:
    - PDF parsing (via PyPDF2 or pdfplumber)
    - Image OCR (via pytesseract or vision models)
    - Office documents (via python-docx, openpyxl)
    """

    # File extension to extraction method mapping
    EXTENSION_MAP = {
        '.txt': ExtractionMethod.TEXT,
        '.md': ExtractionMethod.MARKDOWN,
        '.markdown': ExtractionMethod.MARKDOWN,
        '.json': ExtractionMethod.JSON,
        '.csv': ExtractionMethod.CSV,
        '.py': ExtractionMethod.CODE,
        '.js': ExtractionMethod.CODE,
        '.ts': ExtractionMethod.CODE,
        '.java': ExtractionMethod.CODE,
        '.go': ExtractionMethod.CODE,
        '.rs': ExtractionMethod.CODE,
        '.rb': ExtractionMethod.CODE,
        '.php': ExtractionMethod.CODE,
        '.c': ExtractionMethod.CODE,
        '.cpp': ExtractionMethod.CODE,
        '.h': ExtractionMethod.CODE,
        '.html': ExtractionMethod.TEXT,
        '.xml': ExtractionMethod.TEXT,
        '.yaml': ExtractionMethod.TEXT,
        '.yml': ExtractionMethod.TEXT,
        '.pdf': ExtractionMethod.PDF,
        '.png': ExtractionMethod.IMAGE,
        '.jpg': ExtractionMethod.IMAGE,
        '.jpeg': ExtractionMethod.IMAGE,
        '.gif': ExtractionMethod.IMAGE,
        '.webp': ExtractionMethod.IMAGE,
    }

    def detect_method(self, file_path: Path) -> ExtractionMethod:
        """Detect the extraction method for a file"""
        suffix = file_path.suffix.lower()
        return self.EXTENSION_MAP.get(suffix, ExtractionMethod.UNKNOWN)

    def extract(self, file_path: Path) -> Tuple[str, ExtractionMethod]:
        """
        Extract content from a file.

        Returns (content, method_used)
        """
        method = self.detect_method(file_path)

        if method == ExtractionMethod.TEXT:
            return self._extract_text(file_path), method
        elif method == ExtractionMethod.MARKDOWN:
            return self._extract_text(file_path), method
        elif method == ExtractionMethod.CODE:
            return self._extract_code(file_path), method
        elif method == ExtractionMethod.JSON:
            return self._extract_json(file_path), method
        elif method == ExtractionMethod.CSV:
            return self._extract_csv(file_path), method
        elif method == ExtractionMethod.PDF:
            return self._extract_pdf(file_path), method
        elif method == ExtractionMethod.IMAGE:
            return self._extract_image(file_path), method
        else:
            # Try as text
            return self._extract_text(file_path), ExtractionMethod.TEXT

    def _extract_text(self, file_path: Path) -> str:
        """Extract plain text"""
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                return file_path.read_text(encoding='latin-1')
            except Exception as e:
                logger.error(f"Failed to extract text from {file_path}: {e}")
                return ""

    def _extract_code(self, file_path: Path) -> str:
        """Extract code with metadata"""
        content = self._extract_text(file_path)
        language = file_path.suffix[1:]  # Remove the dot

        # Wrap in code block for context
        return f"```{language}\n{content}\n```"

    def _extract_json(self, file_path: Path) -> str:
        """Extract and format JSON"""
        try:
            data = json.loads(file_path.read_text())
            return json.dumps(data, indent=2)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return self._extract_text(file_path)

    def _extract_csv(self, file_path: Path) -> str:
        """Extract CSV as text with structure info"""
        content = self._extract_text(file_path)
        lines = content.split('\n')

        # Add metadata about structure
        header = lines[0] if lines else ""
        row_count = len(lines) - 1  # Exclude header

        metadata = f"[CSV Data: {row_count} rows]\nHeaders: {header}\n\n"
        return metadata + content

    def _extract_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF.

        Currently returns placeholder. Will integrate PDF library later.
        """
        # TODO: Integrate PyPDF2 or pdfplumber
        logger.warning(f"PDF extraction not yet implemented for {file_path}")
        return f"[PDF Document: {file_path.name}]\n[Content extraction pending PDF library integration]"

    def _extract_image(self, file_path: Path) -> str:
        """
        Extract/describe image content.

        Currently returns placeholder. Will integrate vision model later.
        """
        # TODO: Integrate vision model or OCR
        file_size = file_path.stat().st_size
        return f"[Image: {file_path.name}]\n[Size: {file_size} bytes]\n[Description extraction pending vision integration]"


class DocumentChunker:
    """
    Chunks large documents for processing.

    Uses overlapping chunks to preserve context at boundaries.
    """

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, content: str) -> List[ProcessedChunk]:
        """
        Split content into overlapping chunks.

        Tries to split at paragraph or sentence boundaries when possible.
        """
        if len(content) <= self.chunk_size:
            return [ProcessedChunk(
                index=0,
                content=content,
                start_offset=0,
                end_offset=len(content)
            )]

        chunks = []
        start = 0
        index = 0

        while start < len(content):
            end = min(start + self.chunk_size, len(content))

            # Try to find a good break point (paragraph or sentence)
            if end < len(content):
                # Look for paragraph break
                para_break = content.rfind('\n\n', start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break + 2

                # Or sentence break
                elif (sentence_break := self._find_sentence_break(content, start, end)) > start + self.chunk_size // 2:
                    end = sentence_break

            chunk_content = content[start:end].strip()
            if chunk_content:
                chunks.append(ProcessedChunk(
                    index=index,
                    content=chunk_content,
                    start_offset=start,
                    end_offset=end
                ))
                index += 1

            # Move start with overlap
            start = end - self.overlap if end < len(content) else len(content)

        return chunks

    def _find_sentence_break(self, content: str, start: int, end: int) -> int:
        """Find the last sentence break in a range"""
        # Look for ". " or "! " or "? " followed by capital letter
        search_text = content[start:end]
        matches = list(re.finditer(r'[.!?]\s+(?=[A-Z])', search_text))
        if matches:
            return start + matches[-1].end()
        return end


class FactExtractor:
    """
    Extracts key facts and entities from content.

    Uses pattern matching for basic extraction.
    Will integrate LLM for deeper extraction when available.
    """

    def extract_facts(self, content: str, max_facts: int = 10) -> List[str]:
        """Extract key facts from content"""
        facts = []

        # Extract definitions (X is Y, X means Y)
        definitions = re.findall(
            r'(?:^|\. )([A-Z][^.]*?(?:is|are|means|refers to)[^.]+\.)',
            content, re.MULTILINE
        )
        facts.extend(definitions[:max_facts // 3])

        # Extract key points (bullet points, numbered lists)
        list_items = re.findall(
            r'(?:^|\n)\s*[-*•]\s*(.+?)(?=\n|$)',
            content
        )
        facts.extend([f"• {item.strip()}" for item in list_items[:max_facts // 3]])

        # Extract headings as topics
        headings = re.findall(r'^#+\s+(.+?)$', content, re.MULTILINE)
        facts.extend([f"Topic: {h}" for h in headings[:max_facts // 3]])

        return facts[:max_facts]

    def extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract named entities (basic pattern matching)"""
        entities = {
            'urls': [],
            'emails': [],
            'file_paths': [],
            'code_refs': []
        }

        # URLs
        urls = re.findall(r'https?://[^\s<>"]+', content)
        entities['urls'] = list(set(urls))[:10]

        # Emails
        emails = re.findall(r'[\w.-]+@[\w.-]+\.\w+', content)
        entities['emails'] = list(set(emails))[:10]

        # File paths
        paths = re.findall(r'(?:/[\w.-]+)+|\b[\w.-]+\.[a-z]{2,4}\b', content)
        entities['file_paths'] = list(set(paths))[:10]

        # Code references (function names, classes)
        code_refs = re.findall(r'\b[A-Z][a-zA-Z]+(?:Class|Service|Manager|Handler)\b', content)
        code_refs.extend(re.findall(r'\b[a-z_]+\(\)', content))
        entities['code_refs'] = list(set(code_refs))[:10]

        return entities


class DocumentProcessor:
    """
    Main document processing pipeline.

    Processes files for storage in the knowledge base:
    1. Extract content based on file type
    2. Chunk large documents
    3. Summarize chunks (when LLM available)
    4. Extract facts and entities
    5. Store in knowledge base with proper linking
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        llm_summarizer: Optional[Callable[[str], str]] = None
    ):
        self.kb = knowledge_base
        self.llm_summarizer = llm_summarizer

        self.extractor = ContentExtractor()
        self.chunker = DocumentChunker()
        self.fact_extractor = FactExtractor()

    def process(
        self,
        file_path: Path,
        scope: KnowledgeScope,
        scope_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        uploaded_by: str = "system"
    ) -> IngestResult:
        """
        Process a file and store in knowledge base.

        Args:
            file_path: Path to the file to process
            scope: Knowledge scope (FOUNDATION, PROJECT, TASK)
            scope_id: Molecule ID or Work Item ID (for PROJECT/TASK scope)
            name: Display name (defaults to filename)
            description: Description (auto-generated if not provided)
            tags: Tags for categorization
            uploaded_by: Who uploaded the file

        Returns:
            IngestResult with success status and created entry
        """
        import time
        start_time = time.time()

        file_path = Path(file_path)
        if not file_path.exists():
            return IngestResult(
                success=False,
                error=f"File not found: {file_path}"
            )

        try:
            # Extract content
            content, method = self.extractor.extract(file_path)
            if not content:
                return IngestResult(
                    success=False,
                    error=f"Failed to extract content from {file_path}"
                )

            # Determine knowledge type
            knowledge_type = self._method_to_type(method)

            # Calculate file hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            # Create entry metadata
            entry_name = name or file_path.name
            entry_description = description or self._auto_describe(content, method)

            # Create the knowledge entry
            entry = KnowledgeEntry.create(
                name=entry_name,
                description=entry_description,
                scope=scope,
                scope_id=scope_id,
                knowledge_type=knowledge_type,
                source_file=str(file_path.absolute()),
                uploaded_by=uploaded_by,
                tags=tags
            )
            entry.file_size = file_path.stat().st_size
            entry.content_hash = content_hash

            # Process based on size
            chunks_processed = 0
            facts_extracted = 0

            if len(content) > CHUNK_THRESHOLD:
                # Large document - chunk and process
                chunks = self.chunker.chunk(content)
                chunks_processed = len(chunks)

                # Process each chunk
                all_facts = []
                summaries = []

                for chunk in chunks:
                    # Extract facts from chunk
                    chunk.facts = self.fact_extractor.extract_facts(chunk.content)
                    all_facts.extend(chunk.facts)

                    # Summarize if LLM available
                    if self.llm_summarizer:
                        chunk.summary = self.llm_summarizer(chunk.content)
                    else:
                        # Simple first-paragraph summary
                        chunk.summary = self._simple_summary(chunk.content)

                    summaries.append(chunk.summary)

                facts_extracted = len(all_facts)

                # Store content with chunks
                entry.metadata['chunks'] = [
                    {
                        'index': c.index,
                        'summary': c.summary,
                        'facts': c.facts,
                        'start': c.start_offset,
                        'end': c.end_offset
                    }
                    for c in chunks
                ]
                entry.metadata['combined_summary'] = '\n\n'.join(summaries[:5])  # First 5 summaries
                entry.metadata['all_facts'] = all_facts[:20]  # Top 20 facts

            else:
                # Small document - process directly
                facts = self.fact_extractor.extract_facts(content)
                facts_extracted = len(facts)
                entry.metadata['facts'] = facts

            # Extract entities
            entities = self.fact_extractor.extract_entities(content)
            entry.metadata['entities'] = entities

            # Store the entry
            self.kb.add_entry(entry)

            # Store content in memory system
            env = self.kb.get_context_environment(f"processor_{scope.value}")
            self.kb.store_content_for_entry(entry, content, env)

            processing_time = int((time.time() - start_time) * 1000)

            return IngestResult(
                success=True,
                entry=entry,
                chunks_processed=chunks_processed,
                facts_extracted=facts_extracted,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.exception(f"Error processing {file_path}")
            return IngestResult(
                success=False,
                error=str(e)
            )

    def process_directory(
        self,
        dir_path: Path,
        scope: KnowledgeScope,
        scope_id: Optional[str] = None,
        recursive: bool = True,
        tags: Optional[List[str]] = None,
        uploaded_by: str = "system"
    ) -> List[IngestResult]:
        """Process all files in a directory"""
        dir_path = Path(dir_path)
        results = []

        pattern = '**/*' if recursive else '*'
        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                result = self.process(
                    file_path=file_path,
                    scope=scope,
                    scope_id=scope_id,
                    tags=tags,
                    uploaded_by=uploaded_by
                )
                results.append(result)

        return results

    def process_url(
        self,
        url: str,
        scope: KnowledgeScope,
        scope_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        uploaded_by: str = "system"
    ) -> IngestResult:
        """Process a URL as a knowledge entry (stores reference)"""
        entry = KnowledgeEntry.create(
            name=name or url,
            description=description or f"Reference URL: {url}",
            scope=scope,
            scope_id=scope_id,
            knowledge_type=KnowledgeType.URL,
            source_url=url,
            uploaded_by=uploaded_by,
            tags=tags
        )

        self.kb.add_entry(entry)

        return IngestResult(
            success=True,
            entry=entry
        )

    def process_note(
        self,
        content: str,
        scope: KnowledgeScope,
        scope_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        uploaded_by: str = "system"
    ) -> IngestResult:
        """Process a free-form text note"""
        entry = KnowledgeEntry.create(
            name=name or "Note",
            description=description or content[:200],
            scope=scope,
            scope_id=scope_id,
            knowledge_type=KnowledgeType.NOTE,
            uploaded_by=uploaded_by,
            tags=tags
        )
        entry.file_size = len(content)

        # Extract facts from note
        facts = self.fact_extractor.extract_facts(content)
        entry.metadata['facts'] = facts

        self.kb.add_entry(entry)

        # Store content
        env = self.kb.get_context_environment(f"processor_{scope.value}")
        self.kb.store_content_for_entry(entry, content, env)

        return IngestResult(
            success=True,
            entry=entry,
            facts_extracted=len(facts)
        )

    def _method_to_type(self, method: ExtractionMethod) -> KnowledgeType:
        """Convert extraction method to knowledge type"""
        mapping = {
            ExtractionMethod.TEXT: KnowledgeType.DOCUMENT,
            ExtractionMethod.MARKDOWN: KnowledgeType.DOCUMENT,
            ExtractionMethod.PDF: KnowledgeType.DOCUMENT,
            ExtractionMethod.IMAGE: KnowledgeType.IMAGE,
            ExtractionMethod.JSON: KnowledgeType.DATA,
            ExtractionMethod.CSV: KnowledgeType.DATA,
            ExtractionMethod.CODE: KnowledgeType.CODE,
            ExtractionMethod.UNKNOWN: KnowledgeType.DOCUMENT
        }
        return mapping.get(method, KnowledgeType.DOCUMENT)

    def _auto_describe(self, content: str, method: ExtractionMethod) -> str:
        """Generate auto-description from content"""
        # Take first meaningful paragraph
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if len(para) > 50:  # Skip short paragraphs
                return para[:500] + ('...' if len(para) > 500 else '')

        return content[:500] + ('...' if len(content) > 500 else '')

    def _simple_summary(self, content: str, max_length: int = 200) -> str:
        """Generate simple summary without LLM"""
        # Take first paragraph or sentences
        paragraphs = content.split('\n\n')
        if paragraphs:
            first_para = paragraphs[0].strip()
            if len(first_para) <= max_length:
                return first_para
            return first_para[:max_length] + '...'

        return content[:max_length] + '...'


# Convenience functions

def ingest_file(
    corp_path: Path,
    file_path: Path,
    scope: KnowledgeScope,
    scope_id: Optional[str] = None,
    **kwargs
) -> IngestResult:
    """Convenience function to ingest a single file"""
    kb = KnowledgeBase(corp_path)
    processor = DocumentProcessor(kb)
    return processor.process(file_path, scope, scope_id, **kwargs)


def ingest_foundation(
    corp_path: Path,
    file_path: Path,
    **kwargs
) -> IngestResult:
    """Convenience function to ingest foundation knowledge"""
    return ingest_file(corp_path, file_path, KnowledgeScope.FOUNDATION, **kwargs)


def ingest_project(
    corp_path: Path,
    file_path: Path,
    molecule_id: str,
    **kwargs
) -> IngestResult:
    """Convenience function to ingest project knowledge"""
    return ingest_file(corp_path, file_path, KnowledgeScope.PROJECT, molecule_id, **kwargs)


def ingest_task(
    corp_path: Path,
    file_path: Path,
    work_item_id: str,
    **kwargs
) -> IngestResult:
    """Convenience function to ingest task knowledge"""
    return ingest_file(corp_path, file_path, KnowledgeScope.TASK, work_item_id, **kwargs)
