"""
File Store - Layered File Access and Storage System

Manages files across three layers:
1. Internal: Agent workspace files (generated artifacts, drafts, exports)
2. External: Read-only access to Google Drive (indexed metadata, on-demand fetch)
3. Export: Explicit user-controlled export to external destinations

Design principles:
- Internal files are private to the corp workspace
- External files are never cloned in bulk - metadata indexed, content fetched on-demand
- Exports require explicit user action and destination choice
- Relies on external system's (Drive) permission model for sensitive files
"""

import uuid
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, BinaryIO
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
import logging
import os

logger = logging.getLogger(__name__)


class FileLocation(Enum):
    """Where a file is stored"""
    INTERNAL = "internal"      # Local corp workspace
    GOOGLE_DRIVE = "google_drive"  # External Google Drive
    EXPORTED = "exported"      # Exported to external location


class FileCategory(Enum):
    """Categorization for files"""
    DOCUMENT = "document"      # PDFs, Word docs, text files
    IMAGE = "image"            # Screenshots, diagrams, photos
    CODE = "code"              # Source code files
    DATA = "data"              # CSV, JSON, spreadsheets
    ARTIFACT = "artifact"      # Agent-generated outputs
    ATTACHMENT = "attachment"  # Task attachments
    EXPORT = "export"          # Exported reports/deliverables


@dataclass
class FileMetadata:
    """
    Metadata for a file in the system.

    For internal files: full content stored locally
    For external files: metadata only, content fetched on-demand
    """
    id: str
    name: str
    location: FileLocation
    category: FileCategory

    # Size and type
    size_bytes: int
    mime_type: str
    extension: str

    # Paths
    internal_path: Optional[str] = None  # For internal files
    external_id: Optional[str] = None    # For Drive files (file ID)
    external_path: Optional[str] = None  # For Drive files (folder path)

    # Ownership and scope
    created_by: str = "system"  # agent_id or "user"
    molecule_id: Optional[str] = None
    work_item_id: Optional[str] = None

    # Timestamps
    created_at: str = ""
    modified_at: str = ""
    accessed_at: str = ""

    # Content tracking
    content_hash: Optional[str] = None
    is_cached: bool = False
    cache_path: Optional[str] = None

    # Export tracking
    exported_to: List[Dict[str, str]] = field(default_factory=list)

    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_internal(
        cls,
        name: str,
        category: FileCategory,
        size_bytes: int,
        internal_path: str,
        created_by: str = "system",
        molecule_id: Optional[str] = None,
        work_item_id: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> 'FileMetadata':
        """Create metadata for an internal file"""
        ext = Path(name).suffix.lower()
        mime_type, _ = mimetypes.guess_type(name)

        return cls(
            id=f"file-{uuid.uuid4().hex[:12]}",
            name=name,
            location=FileLocation.INTERNAL,
            category=category,
            size_bytes=size_bytes,
            mime_type=mime_type or "application/octet-stream",
            extension=ext,
            internal_path=internal_path,
            created_by=created_by,
            molecule_id=molecule_id,
            work_item_id=work_item_id,
            created_at=datetime.utcnow().isoformat(),
            modified_at=datetime.utcnow().isoformat(),
            description=description,
            tags=tags or []
        )

    @classmethod
    def create_external(
        cls,
        name: str,
        category: FileCategory,
        size_bytes: int,
        external_id: str,
        external_path: str,
        mime_type: str,
        modified_at: str
    ) -> 'FileMetadata':
        """Create metadata for an external (Drive) file"""
        ext = Path(name).suffix.lower()

        return cls(
            id=f"ext-{uuid.uuid4().hex[:12]}",
            name=name,
            location=FileLocation.GOOGLE_DRIVE,
            category=category,
            size_bytes=size_bytes,
            mime_type=mime_type,
            extension=ext,
            external_id=external_id,
            external_path=external_path,
            created_at=datetime.utcnow().isoformat(),
            modified_at=modified_at
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location.value,
            'category': self.category.value,
            'size_bytes': self.size_bytes,
            'mime_type': self.mime_type,
            'extension': self.extension,
            'internal_path': self.internal_path,
            'external_id': self.external_id,
            'external_path': self.external_path,
            'created_by': self.created_by,
            'molecule_id': self.molecule_id,
            'work_item_id': self.work_item_id,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'accessed_at': self.accessed_at,
            'content_hash': self.content_hash,
            'is_cached': self.is_cached,
            'cache_path': self.cache_path,
            'exported_to': self.exported_to,
            'description': self.description,
            'tags': self.tags,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileMetadata':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            name=data['name'],
            location=FileLocation(data['location']),
            category=FileCategory(data['category']),
            size_bytes=data['size_bytes'],
            mime_type=data['mime_type'],
            extension=data['extension'],
            internal_path=data.get('internal_path'),
            external_id=data.get('external_id'),
            external_path=data.get('external_path'),
            created_by=data.get('created_by', 'system'),
            molecule_id=data.get('molecule_id'),
            work_item_id=data.get('work_item_id'),
            created_at=data.get('created_at', ''),
            modified_at=data.get('modified_at', ''),
            accessed_at=data.get('accessed_at', ''),
            content_hash=data.get('content_hash'),
            is_cached=data.get('is_cached', False),
            cache_path=data.get('cache_path'),
            exported_to=data.get('exported_to', []),
            description=data.get('description', ''),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class DriveFolder:
    """Represents a folder in Google Drive"""
    id: str
    name: str
    path: str
    parent_id: Optional[str]
    is_shared: bool = False
    children_indexed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'parent_id': self.parent_id,
            'is_shared': self.is_shared,
            'children_indexed': self.children_indexed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DriveFolder':
        return cls(
            id=data['id'],
            name=data['name'],
            path=data['path'],
            parent_id=data.get('parent_id'),
            is_shared=data.get('is_shared', False),
            children_indexed=data.get('children_indexed', False)
        )


class InternalFileStore:
    """
    Manages internal file storage.

    Files are organized by:
    - /files/agents/{agent_id}/ - Agent workspaces
    - /files/projects/{molecule_id}/ - Project files
    - /files/tasks/{work_item_id}/ - Task attachments
    - /files/exports/ - Staged exports
    - /files/shared/ - Shared resources
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.files_path = self.corp_path / "files"
        self.files_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.agents_path = self.files_path / "agents"
        self.projects_path = self.files_path / "projects"
        self.tasks_path = self.files_path / "tasks"
        self.exports_path = self.files_path / "exports"
        self.shared_path = self.files_path / "shared"

        for path in [self.agents_path, self.projects_path,
                     self.tasks_path, self.exports_path, self.shared_path]:
            path.mkdir(exist_ok=True)

        # Index
        self.index_file = self.files_path / "index.yaml"
        self.files: Dict[str, FileMetadata] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load file index"""
        if self.index_file.exists():
            data = yaml.safe_load(self.index_file.read_text()) or {}
            for file_data in data.get('files', []):
                meta = FileMetadata.from_dict(file_data)
                self.files[meta.id] = meta

    def _save_index(self) -> None:
        """Save file index"""
        data = {
            'updated_at': datetime.utcnow().isoformat(),
            'file_count': len(self.files),
            'files': [f.to_dict() for f in self.files.values()]
        }
        self.index_file.write_text(yaml.dump(data, default_flow_style=False))

    def _get_storage_path(
        self,
        filename: str,
        agent_id: Optional[str] = None,
        molecule_id: Optional[str] = None,
        work_item_id: Optional[str] = None
    ) -> Path:
        """Determine storage path based on scope"""
        if work_item_id:
            base = self.tasks_path / work_item_id
        elif molecule_id:
            base = self.projects_path / molecule_id
        elif agent_id:
            base = self.agents_path / agent_id
        else:
            base = self.shared_path

        base.mkdir(parents=True, exist_ok=True)
        return base / filename

    def store(
        self,
        filename: str,
        content: Union[bytes, str, BinaryIO],
        category: FileCategory,
        created_by: str = "system",
        molecule_id: Optional[str] = None,
        work_item_id: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> FileMetadata:
        """Store a file internally"""
        # Determine path
        storage_path = self._get_storage_path(
            filename,
            agent_id=created_by if created_by != "user" else None,
            molecule_id=molecule_id,
            work_item_id=work_item_id
        )

        # Handle different content types
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        elif hasattr(content, 'read'):
            content_bytes = content.read()
        else:
            content_bytes = content

        # Write file
        storage_path.write_bytes(content_bytes)

        # Calculate hash
        content_hash = hashlib.sha256(content_bytes).hexdigest()

        # Create metadata
        meta = FileMetadata.create_internal(
            name=filename,
            category=category,
            size_bytes=len(content_bytes),
            internal_path=str(storage_path.relative_to(self.corp_path)),
            created_by=created_by,
            molecule_id=molecule_id,
            work_item_id=work_item_id,
            description=description,
            tags=tags
        )
        meta.content_hash = content_hash

        self.files[meta.id] = meta
        self._save_index()

        logger.info(f"Stored internal file: {filename} -> {meta.id}")
        return meta

    def get(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata by ID"""
        return self.files.get(file_id)

    def read(self, file_id: str) -> Optional[bytes]:
        """Read file content"""
        meta = self.files.get(file_id)
        if not meta or not meta.internal_path:
            return None

        file_path = self.corp_path / meta.internal_path
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None

        # Update access time
        meta.accessed_at = datetime.utcnow().isoformat()
        self._save_index()

        return file_path.read_bytes()

    def list(
        self,
        category: Optional[FileCategory] = None,
        created_by: Optional[str] = None,
        molecule_id: Optional[str] = None,
        work_item_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[FileMetadata]:
        """List files with filters"""
        results = list(self.files.values())

        if category:
            results = [f for f in results if f.category == category]
        if created_by:
            results = [f for f in results if f.created_by == created_by]
        if molecule_id:
            results = [f for f in results if f.molecule_id == molecule_id]
        if work_item_id:
            results = [f for f in results if f.work_item_id == work_item_id]
        if tags:
            results = [f for f in results if any(t in f.tags for t in tags)]

        return sorted(results, key=lambda f: f.modified_at, reverse=True)

    def delete(self, file_id: str) -> bool:
        """Delete a file"""
        meta = self.files.get(file_id)
        if not meta:
            return False

        # Delete actual file
        if meta.internal_path:
            file_path = self.corp_path / meta.internal_path
            if file_path.exists():
                file_path.unlink()

        del self.files[file_id]
        self._save_index()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_size = sum(f.size_bytes for f in self.files.values())
        by_category = {}
        for f in self.files.values():
            cat = f.category.value
            if cat not in by_category:
                by_category[cat] = {'count': 0, 'size': 0}
            by_category[cat]['count'] += 1
            by_category[cat]['size'] += f.size_bytes

        return {
            'total_files': len(self.files),
            'total_size_bytes': total_size,
            'by_category': by_category
        }


class DriveIndex:
    """
    Index of Google Drive files.

    Stores metadata only - content is fetched on-demand.
    This avoids bulk cloning of Drive data.
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.index_path = self.corp_path / "drive_index"
        self.index_path.mkdir(parents=True, exist_ok=True)

        self.cache_path = self.index_path / "cache"
        self.cache_path.mkdir(exist_ok=True)

        self.folders_file = self.index_path / "folders.yaml"
        self.files_file = self.index_path / "files.yaml"
        self.config_file = self.index_path / "config.yaml"

        self.folders: Dict[str, DriveFolder] = {}
        self.files: Dict[str, FileMetadata] = {}
        self.config: Dict[str, Any] = {}

        self._load()

    def _load(self) -> None:
        """Load index from disk"""
        if self.config_file.exists():
            self.config = yaml.safe_load(self.config_file.read_text()) or {}

        if self.folders_file.exists():
            data = yaml.safe_load(self.folders_file.read_text()) or {}
            for folder_data in data.get('folders', []):
                folder = DriveFolder.from_dict(folder_data)
                self.folders[folder.id] = folder

        if self.files_file.exists():
            data = yaml.safe_load(self.files_file.read_text()) or {}
            for file_data in data.get('files', []):
                meta = FileMetadata.from_dict(file_data)
                self.files[meta.id] = meta

    def _save(self) -> None:
        """Save index to disk"""
        self.config_file.write_text(yaml.dump(self.config, default_flow_style=False))

        folders_data = {
            'updated_at': datetime.utcnow().isoformat(),
            'folders': [f.to_dict() for f in self.folders.values()]
        }
        self.folders_file.write_text(yaml.dump(folders_data, default_flow_style=False))

        files_data = {
            'updated_at': datetime.utcnow().isoformat(),
            'files': [f.to_dict() for f in self.files.values()]
        }
        self.files_file.write_text(yaml.dump(files_data, default_flow_style=False))

    def configure(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        root_folder_id: Optional[str] = None
    ) -> None:
        """Configure Drive connection"""
        if client_id:
            self.config['client_id'] = client_id
        if client_secret:
            self.config['client_secret'] = client_secret
        if refresh_token:
            self.config['refresh_token'] = refresh_token
        if root_folder_id:
            self.config['root_folder_id'] = root_folder_id

        self.config['configured_at'] = datetime.utcnow().isoformat()
        self._save()

    def is_configured(self) -> bool:
        """Check if Drive is configured"""
        return bool(self.config.get('refresh_token'))

    def index_folder(
        self,
        folder_id: str,
        folder_name: str,
        folder_path: str,
        parent_id: Optional[str] = None,
        is_shared: bool = False
    ) -> DriveFolder:
        """Add a folder to the index"""
        folder = DriveFolder(
            id=folder_id,
            name=folder_name,
            path=folder_path,
            parent_id=parent_id,
            is_shared=is_shared
        )
        self.folders[folder_id] = folder
        self._save()
        return folder

    def index_file(
        self,
        file_id: str,
        name: str,
        folder_path: str,
        size_bytes: int,
        mime_type: str,
        modified_at: str
    ) -> FileMetadata:
        """Add a file to the index (metadata only)"""
        # Determine category from mime type
        category = self._categorize_file(mime_type, name)

        meta = FileMetadata.create_external(
            name=name,
            category=category,
            size_bytes=size_bytes,
            external_id=file_id,
            external_path=folder_path,
            mime_type=mime_type,
            modified_at=modified_at
        )

        self.files[meta.id] = meta
        self._save()
        return meta

    def _categorize_file(self, mime_type: str, name: str) -> FileCategory:
        """Categorize file based on mime type"""
        mime_lower = mime_type.lower()

        if 'image' in mime_lower:
            return FileCategory.IMAGE
        elif 'pdf' in mime_lower or 'document' in mime_lower or 'word' in mime_lower:
            return FileCategory.DOCUMENT
        elif 'spreadsheet' in mime_lower or 'csv' in mime_lower or 'json' in mime_lower:
            return FileCategory.DATA
        elif any(ext in name.lower() for ext in ['.py', '.js', '.ts', '.go', '.rs', '.java']):
            return FileCategory.CODE
        else:
            return FileCategory.DOCUMENT

    def get_file(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata"""
        return self.files.get(file_id)

    def list_files(
        self,
        folder_path: Optional[str] = None,
        category: Optional[FileCategory] = None
    ) -> List[FileMetadata]:
        """List indexed files"""
        results = list(self.files.values())

        if folder_path:
            results = [f for f in results if f.external_path and
                      f.external_path.startswith(folder_path)]
        if category:
            results = [f for f in results if f.category == category]

        return sorted(results, key=lambda f: f.name)

    def list_folders(self, parent_id: Optional[str] = None) -> List[DriveFolder]:
        """List indexed folders"""
        if parent_id:
            return [f for f in self.folders.values() if f.parent_id == parent_id]
        return list(self.folders.values())

    def search(self, query: str) -> List[FileMetadata]:
        """Search indexed files by name"""
        query_lower = query.lower()
        return [
            f for f in self.files.values()
            if query_lower in f.name.lower()
        ]

    def cache_file(self, file_id: str, content: bytes) -> Optional[str]:
        """Cache file content locally"""
        meta = self.files.get(file_id)
        if not meta:
            return None

        cache_file = self.cache_path / f"{file_id}_{meta.name}"
        cache_file.write_bytes(content)

        meta.is_cached = True
        meta.cache_path = str(cache_file.relative_to(self.corp_path))
        self._save()

        return str(cache_file)

    def get_cached(self, file_id: str) -> Optional[bytes]:
        """Get cached file content"""
        meta = self.files.get(file_id)
        if not meta or not meta.is_cached or not meta.cache_path:
            return None

        cache_file = self.corp_path / meta.cache_path
        if cache_file.exists():
            return cache_file.read_bytes()

        return None

    def clear_cache(self) -> int:
        """Clear all cached files"""
        count = 0
        for meta in self.files.values():
            if meta.is_cached and meta.cache_path:
                cache_file = self.corp_path / meta.cache_path
                if cache_file.exists():
                    cache_file.unlink()
                    count += 1
                meta.is_cached = False
                meta.cache_path = None

        self._save()
        return count


class FileStore:
    """
    Unified file storage system.

    Combines:
    - Internal storage for agent-generated files
    - Google Drive index for external file access
    - Export functionality with user-chosen destinations
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.internal = InternalFileStore(corp_path)
        self.drive = DriveIndex(corp_path)

        # Export history
        self.export_history_file = self.corp_path / "files" / "export_history.yaml"
        self.export_history: List[Dict[str, Any]] = []
        self._load_export_history()

    def _load_export_history(self) -> None:
        """Load export history"""
        if self.export_history_file.exists():
            data = yaml.safe_load(self.export_history_file.read_text()) or {}
            self.export_history = data.get('exports', [])

    def _save_export_history(self) -> None:
        """Save export history"""
        data = {
            'updated_at': datetime.utcnow().isoformat(),
            'exports': self.export_history
        }
        self.export_history_file.write_text(yaml.dump(data, default_flow_style=False))

    # =========================================================================
    # Internal File Operations
    # =========================================================================

    def store_internal(
        self,
        filename: str,
        content: Union[bytes, str, BinaryIO],
        category: FileCategory,
        created_by: str = "system",
        molecule_id: Optional[str] = None,
        work_item_id: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> FileMetadata:
        """Store a file in internal storage"""
        return self.internal.store(
            filename=filename,
            content=content,
            category=category,
            created_by=created_by,
            molecule_id=molecule_id,
            work_item_id=work_item_id,
            description=description,
            tags=tags
        )

    def read_internal(self, file_id: str) -> Optional[bytes]:
        """Read an internal file"""
        return self.internal.read(file_id)

    def list_internal(
        self,
        category: Optional[FileCategory] = None,
        created_by: Optional[str] = None,
        molecule_id: Optional[str] = None,
        work_item_id: Optional[str] = None
    ) -> List[FileMetadata]:
        """List internal files"""
        return self.internal.list(
            category=category,
            created_by=created_by,
            molecule_id=molecule_id,
            work_item_id=work_item_id
        )

    # =========================================================================
    # Drive Operations
    # =========================================================================

    def configure_drive(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        root_folder_id: Optional[str] = None
    ) -> None:
        """Configure Google Drive connection"""
        self.drive.configure(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            root_folder_id=root_folder_id
        )

    def is_drive_configured(self) -> bool:
        """Check if Drive is configured"""
        return self.drive.is_configured()

    def browse_drive(
        self,
        folder_path: Optional[str] = None,
        category: Optional[FileCategory] = None
    ) -> Dict[str, Any]:
        """Browse Drive files and folders"""
        return {
            'folders': [f.to_dict() for f in self.drive.list_folders()],
            'files': [f.to_dict() for f in self.drive.list_files(folder_path, category)],
            'is_configured': self.drive.is_configured()
        }

    def search_drive(self, query: str) -> List[FileMetadata]:
        """Search Drive files"""
        return self.drive.search(query)

    # =========================================================================
    # Export Operations
    # =========================================================================

    def prepare_export(
        self,
        file_id: str,
        destination_folder_id: Optional[str] = None,
        destination_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare a file for export.

        Returns export details for user confirmation.
        """
        meta = self.internal.get(file_id)
        if not meta:
            return {'success': False, 'error': 'File not found'}

        return {
            'success': True,
            'file': meta.to_dict(),
            'destination_folder_id': destination_folder_id,
            'destination_path': destination_path,
            'ready_for_export': True
        }

    def record_export(
        self,
        file_id: str,
        destination_type: str,
        destination_path: str,
        destination_id: Optional[str] = None,
        exported_by: str = "user"
    ) -> Dict[str, Any]:
        """Record an export after it's completed"""
        meta = self.internal.get(file_id)
        if not meta:
            return {'success': False, 'error': 'File not found'}

        export_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'destination_type': destination_type,
            'destination_path': destination_path,
            'destination_id': destination_id,
            'exported_by': exported_by
        }

        meta.exported_to.append(export_record)
        self.internal._save_index()

        # Add to history
        self.export_history.append({
            'file_id': file_id,
            'file_name': meta.name,
            **export_record
        })
        self._save_export_history()

        return {'success': True, 'export': export_record}

    def get_export_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent export history"""
        return self.export_history[-limit:]

    # =========================================================================
    # Unified Operations
    # =========================================================================

    def get_file(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata from any source"""
        # Check internal first
        meta = self.internal.get(file_id)
        if meta:
            return meta

        # Check drive index
        return self.drive.get_file(file_id)

    def search_all(self, query: str) -> Dict[str, List[FileMetadata]]:
        """Search all file sources"""
        return {
            'internal': [f for f in self.internal.files.values()
                        if query.lower() in f.name.lower()],
            'drive': self.drive.search(query)
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get file store statistics"""
        return {
            'internal': self.internal.get_stats(),
            'drive': {
                'is_configured': self.drive.is_configured(),
                'indexed_files': len(self.drive.files),
                'indexed_folders': len(self.drive.folders),
                'cached_files': sum(1 for f in self.drive.files.values() if f.is_cached)
            },
            'exports': {
                'total_exports': len(self.export_history)
            }
        }

    def get_browse_data(
        self,
        location: str = "all",
        folder_path: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get data for file browser UI.

        Args:
            location: "internal", "drive", or "all"
            folder_path: Filter by folder path
            category: Filter by category
        """
        cat = FileCategory(category) if category else None

        result = {
            'internal_files': [],
            'drive_files': [],
            'drive_folders': [],
            'drive_configured': self.drive.is_configured()
        }

        if location in ["internal", "all"]:
            result['internal_files'] = [
                f.to_dict() for f in self.internal.list(category=cat)
            ]

        if location in ["drive", "all"] and self.drive.is_configured():
            result['drive_files'] = [
                f.to_dict() for f in self.drive.list_files(folder_path, cat)
            ]
            result['drive_folders'] = [
                f.to_dict() for f in self.drive.list_folders()
            ]

        return result


# Convenience functions

def get_file_store(corp_path: Path) -> FileStore:
    """Get the file store for a corp"""
    return FileStore(corp_path)
